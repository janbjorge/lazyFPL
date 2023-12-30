from __future__ import annotations

import argparse
import dataclasses
import functools
import itertools
import math
import pickle
import traceback
import typing

import torch
from torch.utils.data import DataLoader as TorchDataLoader, Dataset as TorchDataset
from tqdm.std import tqdm

from lazyfpl import conf, database, fetch, populator, structures

if conf.debug:
    torch.set_printoptions(threshold=10_000)


@dataclasses.dataclass
class NormalizedFeatures:
    at_home: float
    points: float
    minutes: float
    opponent: tuple[float, ...]
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

    def flattend(self) -> tuple[float, ...]:
        def _flatter(obj):
            if isinstance(obj, (float, int, bool)):
                yield obj
            elif isinstance(obj, (tuple, list, set)):
                for v in obj:
                    yield from _flatter(v)
            else:
                raise NotImplementedError(type(obj))

        return tuple(_flatter(dataclasses.astuple(self)))


@dataclasses.dataclass
class FeatureBundle:
    features: tuple[NormalizedFeatures, ...]
    target: float


class Net(torch.nn.Module):
    def __init__(
        self,
        nfeature: int,
        rnn_hidden: int = 16,
    ) -> None:
        super().__init__()
        self.nfeature = nfeature
        self.rnn_hidden = rnn_hidden
        self.enc = torch.nn.GRU(
            input_size=nfeature,
            hidden_size=rnn_hidden,
            batch_first=True,
        )
        self.dec = torch.nn.Sequential(
            torch.nn.Linear(
                in_features=rnn_hidden,
                out_features=1,
            ),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        _, h_final = self.enc(x)
        return self.dec(h_final.squeeze()).view(-1)


@functools.cache
def onehot_team_name(name: str) -> tuple[float, ...]:
    names = sorted({g.team for g in database.games()})
    enc = [0.0] * len(names)
    enc[names.index(name)] = 1.0
    return tuple(enc)


def features(f: structures.Fixture) -> NormalizedFeatures:
    """Generates and returns normalized features for a given fixture."""
    assert f.points is not None
    p_scale = database.points()
    s_scale = database.strengths()
    m_scale = database.minutes()
    return NormalizedFeatures(
        at_home=(f.at_home - 0.5) / 0.5,
        points=p_scale.normalize(f.points),
        minutes=m_scale.normalize(f.minutes or 0),
        opponent=onehot_team_name(f.opponent),
        opponent_strength_attack_away=s_scale.strength_attack_away.normalize(
            f.opponent_strength_attack_away,
        ),
        opponent_strength_attack_home=s_scale.strength_attack_home.normalize(
            f.opponent_strength_attack_home,
        ),
        opponent_strength_defence_away=s_scale.strength_defence_away.normalize(
            f.opponent_strength_defence_away,
        ),
        opponent_strength_defence_home=s_scale.strength_defence_home.normalize(
            f.opponent_strength_defence_home,
        ),
        opponent_strength_overall_away=s_scale.strength_overall_away.normalize(
            f.opponent_strength_overall_away,
        ),
        opponent_strength_overall_home=s_scale.strength_overall_home.normalize(
            f.opponent_strength_overall_home,
        ),
        team_strength_attack_away=s_scale.strength_attack_away.normalize(
            f.team_strength_attack_away,
        ),
        team_strength_attack_home=s_scale.strength_attack_home.normalize(
            f.team_strength_attack_home,
        ),
        team_strength_defence_away=s_scale.strength_defence_away.normalize(
            f.team_strength_defence_away,
        ),
        team_strength_defence_home=s_scale.strength_defence_home.normalize(
            f.team_strength_defence_home,
        ),
        team_strength_overall_away=s_scale.strength_overall_away.normalize(
            f.team_strength_overall_away,
        ),
        team_strength_overall_home=s_scale.strength_overall_home.normalize(
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
    fixtures: list[structures.Fixture],
    upsample: int,
    backtrace: int = conf.backtrace,
) -> typing.Iterator[FeatureBundle]:
    """Generates training samples from a list of fixtures, considering
    upsampling and backtrace length."""
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
        repat = max(
            (
                math.exp((target.kickoff_time - min_ko) / (max_ko - min_ko) * 2)
                / (math.e**2)
                * upsample
            ),
            1,
        )
        yield from itertools.repeat(
            FeatureBundle(
                features=tuple(features(f) for f in train[-backtrace:]),
                target=target.points,
            ),
            round(repat),
        )


def train(
    player: structures.Player,
    epochs: int,
    lr: float,
    upsample: int,
    batch_size: int,
):
    """Trains a model for the given player using the specified parameters."""
    bundles = tuple(samples(player.fixutres, upsample, conf.backtrace))
    features = [[f.flattend() for f in b.features] for b in bundles]
    ds = SequenceDataset(
        x=torch.tensor(
            features,
            dtype=torch.float32,
        ),
        y=torch.tensor(
            tuple(b.target for b in bundles),
            dtype=torch.float32,
        ),
    )
    loader = TorchDataLoader(ds, batch_size=batch_size, shuffle=True)

    loss_function = torch.nn.HuberLoss()
    net = Net(ds[0][0].shape[-1])
    optimizer = torch.optim.AdamW(net.parameters(), lr=lr)

    for _ in range(epochs):
        for x, y in loader:
            optimizer.zero_grad()
            output = net(x)
            assert output.shape == y.shape, (output.shape, y.shape)
            loss = loss_function(output, y)
            loss.backward()
            optimizer.step()
    return net


def load_model(player: structures.Player) -> Net:
    """Loads a trained model for the specified player."""
    pid = populator.player_id_fuzzer(player.name)
    if bts := database.load_model(pid):
        ms = pickle.loads(bts)
        n = Net(nfeature=ms["nfeature"], rnn_hidden=ms["rnn_hidden"])
        n.load_state_dict(ms["weights"])
        return n
    raise ValueError(f"No model for {player.name=} / {player.team=} / {pid=}.")


def save_model(player: structures.Player, m: Net) -> None:
    """Saves the trained model for the specified player."""
    database.save_model(
        populator.player_id_fuzzer(player.name),
        pickle.dumps(
            {
                "rnn_hidden": m.rnn_hidden,
                "nfeature": m.nfeature,
                "weights": m.state_dict(),
            }
        ),
    )


def xP(
    player: structures.Player,
    lookahead: int = conf.lookahead,
    backtrace: int = conf.backtrace,
) -> float:
    """Calculates the expected points (xP) for a player based
    on their upcoming fixtures."""
    expected = list[float]()
    fixutres = sorted(player.fixutres, key=lambda x: x.kickoff_time)
    inference = [features(f).flattend() for f in fixutres if not f.upcoming][
        -backtrace:
    ]
    upcoming = [f for f in fixutres if f.upcoming]
    model = load_model(player)
    model.eval()
    with torch.no_grad():
        for nxt in upcoming[:lookahead]:
            points = (
                model(
                    torch.tensor(inference, dtype=torch.float32),
                )
                .detach()
                .numpy()
            )
            assert points.shape == (1,), points.shape
            expected.extend(points)
            inference.pop(0)
            inference.append(
                features(
                    structures.Fixture(
                        **(dataclasses.asdict(nxt) | {"points": points[0]})
                    )
                ).flattend()
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
        default=5,
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
        default=32,
        help="(default: %(default)s)",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=16,
        help="(default: %(default)s)",
    )

    args = parser.parse_args()

    players = [p for p in fetch.players() if p.mtm() >= args.min_mtm]

    with tqdm(
        ascii=True,
        ncols=120,
        total=len(players),
        unit_divisor=1_000,
        unit_scale=True,
    ) as bar:
        for player in players:
            bar.set_postfix_str(player.name)
            try:
                m = train(
                    player,
                    epochs=args.epochs,
                    lr=args.lr,
                    upsample=args.upsample,
                    batch_size=args.batch_size,
                )
            except (
                IndexError,
                ValueError,
            ):
                ...
            except Exception as e:
                bar.write("".join(traceback.format_exception(e)))
            else:
                save_model(player, m)
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
