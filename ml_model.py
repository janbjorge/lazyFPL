import argparse
import dataclasses
import pickle

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


class Net(torch.nn.Module):
    def __init__(self, sensors: int, rnn_hidden: int = 16) -> None:
        super().__init__()
        self.rrn_hidden = rnn_hidden
        self.num_layers = 1
        self.sensors = sensors
        self.dropout = torch.nn.Dropout(0.25)
        self.dec = torch.nn.Sequential(
            torch.nn.Linear(
                in_features=rnn_hidden,
                out_features=rnn_hidden,
            ),
            torch.nn.ReLU(),
            torch.nn.Linear(
                in_features=rnn_hidden,
                out_features=1,
            ),
        )
        self.enc = torch.nn.GRU(
            input_size=sensors,
            hidden_size=rnn_hidden,
            batch_first=True,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size = x.shape[0]
        h_init = torch.zeros(
            self.num_layers,
            batch_size,
            self.rrn_hidden,
        ).requires_grad_()
        _, h_final = self.enc(x, h_init)
        return self.dec(self.dropout(h_final)).flatten()


def normalization(v: float, s: "database.SampleSummay") -> float:
    assert s.variance > 0
    return (v - s.mean) / s.variance


def features(f: "structures.Fixture") -> tuple[float, ...]:
    assert f.points is not None
    p_scale = database.points()
    s_scale = database.strengths()
    return (
        (f.at_home - 0.5) / 0.5,
        normalization(
            f.points,
            p_scale,
        ),
        normalization(
            f.opponent_strength_attack_away,
            s_scale["strength_attack_away"],
        ),
        normalization(
            f.opponent_strength_attack_home,
            s_scale["strength_attack_home"],
        ),
        normalization(
            f.opponent_strength_defence_away,
            s_scale["strength_defence_away"],
        ),
        normalization(
            f.opponent_strength_defence_home,
            s_scale["strength_defence_home"],
        ),
        normalization(
            f.opponent_strength_overall_away,
            s_scale["strength_overall_away"],
        ),
        normalization(
            f.opponent_strength_overall_home,
            s_scale["strength_overall_home"],
        ),
        normalization(
            f.team_strength_attack_away,
            s_scale["strength_attack_away"],
        ),
        normalization(
            f.team_strength_attack_home,
            s_scale["strength_attack_home"],
        ),
        normalization(
            f.team_strength_defence_away,
            s_scale["strength_defence_away"],
        ),
        normalization(
            f.team_strength_defence_home,
            s_scale["strength_defence_home"],
        ),
        normalization(
            f.team_strength_overall_away,
            s_scale["strength_overall_away"],
        ),
        normalization(
            f.team_strength_overall_home,
            s_scale["strength_overall_home"],
        ),
    )


class SequenceDataset(TorchDataset):
    def __init__(
        self,
        fixtures: list["structures.Fixture"],
        backtrace: int = conf.backtrace,
    ) -> None:
        x, y = samples(fixtures, backtrace)
        self.x, self.y = torch.Tensor(x), torch.Tensor(y)

    def __len__(self) -> int:
        return self.x.shape[0]

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.x[idx], self.y[idx]


def samples(
    fixtures: list["structures.Fixture"],
    backtrace: int = 3,
) -> tuple[list[tuple[tuple[float, ...], ...]], list[float]]:
    fixtures = sorted(fixtures, key=lambda x: x.kickoff_time)
    # time --->
    back = (backtrace + 2) * 3
    assert isinstance(back, int) and back > 0
    train = [f for f in fixtures if not f.upcoming][-back:]

    if len(train) < backtrace:
        raise ValueError("To few samples.")

    targets = list[float]()
    coefficients = list[tuple[tuple[float, ...], ...]]()

    while len(train) > backtrace:
        target = train.pop(-1)
        sub = tuple(features(f) for f in train[-backtrace:])
        coefficients.append(sub)
        assert target.points is not None
        targets.append(target.points)

    coefficients, targets = coefficients * 100, targets * 100
    return coefficients, targets


def train(
    player: "structures.Player",
    epochs: int,
    lr: float,
):
    ds = SequenceDataset(player.fixutres)
    loader = TorchDataLoader(ds, batch_size=8, shuffle=True)

    loss_function = torch.nn.MSELoss()
    net = Net(ds[0][0].shape[-1])
    optimizer = torch.optim.SGD(net.parameters(), lr=lr)

    for _ in range(epochs):
        for x, y in loader:
            output = net(x)
            assert output.shape == y.shape
            loss = loss_function(output, y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
    return net


def load(player: "structures.Player") -> "Net":
    pid = populator.player_id_fuzzer(player.name)
    if bts := database.fetch_model(pid):
        ms = pickle.loads(bts)
        n = Net(sensors=ms["sensors"], rnn_hidden=ms["rnn_hidden"])
        n.load_state_dict(ms["weights"])
        return n
    raise ValueError(f"No model for {player.name=} / {player.team=} / {pid=}.")


def save(player: "structures.Player", m: "Net") -> None:
    database.set_model(
        populator.player_id_fuzzer(player.name),
        pickle.dumps(
            dict(
                inputs=m.num_layers,
                rnn_hidden=m.rrn_hidden,
                sensors=m.sensors,
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
                    [np.array(x, dtype=np.float32) for x in inference],
                    axis=0,
                ).astype(np.float32),
                axis=0,
            )
            points = model(torch.from_numpy(inf)).detach().numpy()
            assert points.shape == (1,), print(points.shape)
            expected.extend(points)
            inference.pop(0)
            inference.append(
                features(
                    structures.Fixture(
                        **(dataclasses.asdict(nxt) | dict(points=points))
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
                m = train(player, epochs=args.epochs, lr=args.lr)
            except ValueError as e:
                bar.write(f"Skipped due {player.name} to: {e}")
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
