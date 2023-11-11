import argparse
import dataclasses
import pickle
import traceback
import typing

import numpy as np
import torch
from torch.utils.data import DataLoader as TorchDataLoader
from torch.utils.data import Dataset as TorchDataset
from tqdm.std import tqdm

import conf
import database
import fetch
import populator
import structures

if conf.debug:
    torch.set_printoptions(threshold=10_000)


@dataclasses.dataclass
class NormalizedFeatures:
    at_home: float
    points: float
    opponent_strength_attack_away: float
    opponent_strength_attack_home: float
    opponent_strength_defence_away: float
    opponent_strength_defence_home: float
    opponent_strength_overall_away: float
    opponent_strength_overall_home: float
    team_strength_attack_away: float
    team_strength_attack_home: float
    team_strength_defence_away: float
    team_strength_defence_home: float
    team_strength_overall_away: float
    team_strength_overall_home: float


@dataclasses.dataclass
class FeatureBundle:
    features: tuple[NormalizedFeatures, ...]
    target: float


class Net(torch.nn.Module):
    def __init__(self, nfeature: int, rnn_hidden: int = 16) -> None:
        super().__init__()
        self.rrn_hidden = rnn_hidden
        self.nfeature = nfeature
        self.enc = torch.nn.GRU(
            input_size=nfeature,
            hidden_size=rnn_hidden,
            batch_first=True,
        )
        self.dec = torch.nn.Sequential(
            torch.nn.Linear(
                in_features=rnn_hidden,
                out_features=rnn_hidden,
            ),
            torch.nn.ELU(),
            torch.nn.Dropout(),
            torch.nn.Linear(
                in_features=rnn_hidden,
                out_features=1,
            ),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size = x.shape[0]
        h_init = torch.randn(
            1,
            batch_size,
            self.rrn_hidden,
            requires_grad=True,
        )
        _, h_final = self.enc(x, h_init)
        return self.dec(h_final).flatten()


def features(f: "structures.Fixture") -> NormalizedFeatures:
    assert f.points is not None
    p_scale = database.points()
    s_scale = database.strengths()
    return NormalizedFeatures(
        at_home=(f.at_home - 0.5) / 0.5,
        points=p_scale.normalize(f.points),
        opponent_strength_attack_away=s_scale["strength_attack_away"].normalize(
            f.opponent_strength_attack_away,
        ),
        opponent_strength_attack_home=s_scale["strength_attack_home"].normalize(
            f.opponent_strength_attack_home,
        ),
        opponent_strength_defence_away=s_scale["strength_defence_away"].normalize(
            f.opponent_strength_defence_away,
        ),
        opponent_strength_defence_home=s_scale["strength_defence_home"].normalize(
            f.opponent_strength_defence_home,
        ),
        opponent_strength_overall_away=s_scale["strength_overall_away"].normalize(
            f.opponent_strength_overall_away,
        ),
        opponent_strength_overall_home=s_scale["strength_overall_home"].normalize(
            f.opponent_strength_overall_home,
        ),
        team_strength_attack_away=s_scale["strength_attack_away"].normalize(
            f.team_strength_attack_away,
        ),
        team_strength_attack_home=s_scale["strength_attack_home"].normalize(
            f.team_strength_attack_home,
        ),
        team_strength_defence_away=s_scale["strength_defence_away"].normalize(
            f.team_strength_defence_away,
        ),
        team_strength_defence_home=s_scale["strength_defence_home"].normalize(
            f.team_strength_defence_home,
        ),
        team_strength_overall_away=s_scale["strength_overall_away"].normalize(
            f.team_strength_overall_away,
        ),
        team_strength_overall_home=s_scale["strength_overall_home"].normalize(
            f.team_strength_overall_home,
        ),
    )


class SequenceDataset(TorchDataset):
    def __init__(self, x: torch.Tensor, y: torch.Tensor) -> None:
        self.x, self.y = x, y

    def __len__(self) -> int:
        return self.x.shape[0]

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.x[idx], self.y[idx]


def samples(
    fixtures: list["structures.Fixture"],
    backtrace: int = conf.backtrace,
    upsample: int = 5,
) -> typing.Iterator[FeatureBundle]:
    fixtures = sorted(fixtures, key=lambda x: x.kickoff_time)
    # time --->
    train = [f for f in fixtures if not f.upcoming]
    min_ko = min(f.kickoff_time for f in train)
    max_ko = max(f.kickoff_time for f in train)

    if len(train) < backtrace:
        raise ValueError("To few samples.")

    while len(train) > backtrace:
        target = train.pop(-1)
        assert target.points is not None
        repat = (target.kickoff_time - min_ko) / (max_ko - min_ko) * upsample
        repat = round(repat**2 + 1)
        for _ in range(repat):
            yield FeatureBundle(
                features=tuple(features(f) for f in train[-backtrace:]),
                target=target.points,
            )


def train(
    player: "structures.Player",
    epochs: int,
    lr: float,
    upsample: int,
):
    bundles = tuple(samples(player.fixutres, conf.backtrace, upsample=upsample))
    ds = SequenceDataset(
        x=torch.tensor(
            tuple(tuple(dataclasses.astuple(f) for f in b.features) for b in bundles),
            dtype=torch.float32,
        ),
        y=torch.tensor(tuple(b.target for b in bundles), dtype=torch.float32),
    )
    loader = TorchDataLoader(ds, batch_size=16, shuffle=True)

    loss_function = torch.nn.MSELoss()
    net = Net(ds[0][0].shape[-1])
    optimizer = torch.optim.AdamW(net.parameters(), lr=lr)

    for _ in range(epochs):
        for x, y in loader:
            output = net(x)
            assert output.shape == y.shape, (output.shape, y.shape)
            loss = loss_function(output, y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
    return net


def load(player: "structures.Player") -> "Net":
    pid = populator.player_id_fuzzer(player.name)
    if bts := database.fetch_model(pid):
        ms = pickle.loads(bts)
        n = Net(nfeature=ms["nfeature"], rnn_hidden=ms["rnn_hidden"])
        n.load_state_dict(ms["weights"])
        return n
    raise ValueError(f"No model for {player.name=} / {player.team=} / {pid=}.")


def save(player: "structures.Player", m: "Net") -> None:
    database.set_model(
        populator.player_id_fuzzer(player.name),
        pickle.dumps(
            dict(
                rnn_hidden=m.rrn_hidden,
                nfeature=m.nfeature,
                weights=m.state_dict(),
            )
        ),
    )


def xP(
    player: "structures.Player",
    lookahead: int = conf.lookahead,
    backtrace: int = conf.backtrace,
) -> float:
    expected = list[float]()
    fixutres = sorted(player.fixutres, key=lambda x: x.kickoff_time)
    inference = [features(f) for f in fixutres if not f.upcoming][-backtrace:]
    upcoming = [f for f in fixutres if f.upcoming]

    model = load(player)
    model.eval()
    with torch.no_grad():
        for nxt in upcoming[:lookahead]:
            inf = np.expand_dims(
                np.stack(
                    [
                        np.array(dataclasses.astuple(x), dtype=np.float32)
                        for x in inference
                    ],
                    axis=0,
                ).astype(np.float32),
                axis=0,
            )
            points = model(torch.from_numpy(inf)).detach().numpy()
            assert points.shape == (1,), points.shape
            expected.extend(points)
            inference.pop(0)
            inference.append(
                features(
                    structures.Fixture(
                        **(dataclasses.asdict(nxt) | dict(points=points[0]))
                    )
                )
            )

    if conf.debug:
        print(player.name, player.team, expected)

    return round(sum(expected), 1)


def main():
    parser = argparse.ArgumentParser(
        prog="Player model trainer.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=50,
        help="(default: %(default)s)",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=0.01,
        help="(default: %(default)s)",
    )
    parser.add_argument(
        "--min-mtm",
        type=int,
        default=0,
        help="(default: %(default)s)",
    )
    parser.add_argument(
        "--upsample",
        type=int,
        default=5,
        help="(default: %(default)s)",
    )

    args = parser.parse_args()

    players = [p for p in fetch.players() if p.mtm() >= args.min_mtm]

    with tqdm(
        ascii=True,
        bar_format="{percentage:3.0f}% | {bar:20} {r_bar}",
        total=len(players),
        unit_divisor=1_000,
        unit_scale=True,
    ) as bar:
        for player in players:
            try:
                m = train(
                    player,
                    epochs=args.epochs,
                    lr=args.lr,
                    upsample=args.upsample,
                )
            except ValueError:
                pass
            except Exception as e:
                bar.write("".join(traceback.format_exception(e)))
            else:
                save(player, m)
                bar.write(
                    f"{xP(player):<6.1f} "
                    + f"{player.name} ("
                    + f"{player.team} - "
                    + f"{player.next_opponent})"
                )
            finally:
                bar.update(1)


if __name__ == "__main__":
    main()
