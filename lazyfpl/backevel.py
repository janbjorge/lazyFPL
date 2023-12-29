from __future__ import annotations

import dataclasses
import datetime
import statistics
import traceback
import typing

import torch

from lazyfpl import conf, fetch, ml_model, structures


@dataclasses.dataclass(frozen=True)
class PredictionOutcome:
    """
    Represents the outcome of a prediction, including predicted and
    actual values, and kickoff time.
    """

    prediceted: float
    truth: float
    kickoff: datetime.datetime


def backeval(
    player: structures.Player,
    lookahead: int = 1,
    backtrace: int = conf.backtrace,
    backstep: int = 10,
) -> typing.Iterator[PredictionOutcome]:
    """
    Back-evaluates a player's performance predictions for a
    given number of past fixtures.
    """
    with torch.no_grad():
        net = ml_model.load_model(player)
        net.eval()
        for n in range(backstep):
            fixutres = [f for f in player.fixutres if not f.upcoming][
                -(backtrace + lookahead + n) : -(lookahead + n)
            ]
            inference = [(ml_model.features(f)).flattend() for f in fixutres]
            try:
                next_fixture = player.fixutres[player.fixutres.index(fixutres[-1]) + 1]
            except IndexError:
                break

            xP = net(torch.tensor(inference, dtype=torch.float32)).detach().numpy()[0]

            assert xP is not None
            assert next_fixture.points is not None
            yield PredictionOutcome(
                prediceted=xP,
                truth=next_fixture.points,
                kickoff=next_fixture.kickoff_time,
            )


def players_backeval() -> dict[structures.Player, tuple[PredictionOutcome, ...]]:
    """
    Evaluates the back-evaluation for all players and returns
    a dictionary with the results.
    """
    rv = dict[structures.Player, tuple[PredictionOutcome, ...]]()
    for player in sorted(fetch.players(), key=lambda x: (x.team, x.webname, x.name)):
        try:
            rv[player] = tuple(backeval(player))
        except ValueError as e:
            if conf.debug:
                traceback.print_exception(e)
    return rv


if __name__ == "__main__":
    player_xp = players_backeval()

    for player, ev in player_xp.items():
        print(f"\n{player.name}({player.webname}) - {player.position} - {player.team}")
        for e in sorted(ev, key=lambda x: x.kickoff):
            print(
                f"  When: {e.kickoff.date()} xP: {e.prediceted:<6.1f} "
                f"TP: {e.truth:<6.1f} Err: {abs(e.prediceted - e.truth):<6.1f}"
            )

    print()
    rms = (
        statistics.mean(
            (v.prediceted - v.truth) ** 2
            for values in player_xp.values()
            for v in values
        )
        ** 0.5
    )
    print(f"RMS: {rms:.1f}")
    am = statistics.mean(
        (abs(v.prediceted - v.truth)) for values in player_xp.values() for v in values
    )
    print(f"AM : {am:.1f}")
    for n in range(1, 6):
        errs = (
            1 if abs(v.prediceted - v.truth) <= n else 0
            for values in player_xp.values()
            for v in values
        )
        print(f"RC{n}: {statistics.mean(errs)*100:.1f}")

    print()

    def key(values: tuple[PredictionOutcome, ...]) -> float:
        return statistics.mean((v.prediceted - v.truth) ** 2 for v in values) ** 0.5 + 1

    for player, values in sorted(
        player_xp.items(),
        key=lambda x: (x[0].xP or 0) / (key(x[1])),
    )[-10:]:
        if player.xP:
            print(
                f"{player.webname:<20} {player.xP:<6.2f} "
                f"{key(values):<6.2f} {(player.xP or 0)/(key(values)):<6.2f}"
            )
