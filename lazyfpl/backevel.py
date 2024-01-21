from __future__ import annotations

import dataclasses
import datetime
import statistics
import traceback
import typing

import more_itertools
import torch

from lazyfpl import conf, fetch, ml_model, structures


@dataclasses.dataclass(frozen=True)
class PredictionOutcome:
    """
    Represents the outcome of a prediction, including predicted and
    actual values, and kickoff time.
    """

    prediceted: float
    target: float
    kickoff: datetime.datetime


def backeval(
    player: structures.Player,
    backtrace: int = conf.backtrace,
    backstep: int = 10,
) -> typing.Iterator[PredictionOutcome]:
    """
    Back-evaluates a player's performance predictions for a
    given number of past fixtures.
    """
    with torch.no_grad():
        net = ml_model.load_model(player).eval()
        fixutres = [f for f in player.fixutres if not f.upcoming][-backstep:]
        for *context, target in more_itertools.sliding_window(fixutres, backtrace + 1):
            xP = (
                net(
                    torch.tensor(
                        [(ml_model.features(c)).flattend() for c in context],
                        dtype=torch.float32,
                    )
                )
                .detach()
                .numpy()[0]
            )

            assert xP is not None
            assert target.points is not None
            yield PredictionOutcome(
                prediceted=xP,
                target=target.points,
                kickoff=target.kickoff_time,
            )


def players_backeval() -> (
    typing.Generator[
        tuple[structures.Player, tuple[PredictionOutcome, ...]],
        None,
        None,
    ]
):
    """
    Evaluates the back-evaluation for all players and returns
    a dictionary with the results.
    """
    for player in sorted(fetch.players(), key=lambda x: (x.team, x.webname, x.name)):
        try:
            yield player, tuple(backeval(player))
        except ValueError as e:
            if conf.debug:
                traceback.print_exception(e)


if __name__ == "__main__":
    player_xp = tuple(players_backeval())

    for player, ev in player_xp:
        print(f"\n{player.name}({player.webname}) - {player.position} - {player.team}")
        for e in sorted(ev, key=lambda x: x.kickoff):
            print(
                f"  When: {e.kickoff.date()} xP: {e.prediceted:<6.1f} "
                f"TP: {e.target:<6.1f} Err: {abs(e.prediceted - e.target):<6.1f}"
            )

    print()
    rms = (
        statistics.mean(
            (v.prediceted - v.target) ** 2 for _, values in player_xp for v in values
        )
        ** 0.5
    )
    print(f"RMS: {rms:.1f}")
    am = statistics.mean(
        (abs(v.prediceted - v.target)) for _, values in player_xp for v in values
    )
    print(f"AM : {am:.1f}")
    for n in range(1, 6):
        errs = (
            1 if abs(v.prediceted - v.target) <= n else 0
            for _, values in player_xp
            for v in values
        )
        print(f"RC{n}: {statistics.mean(errs)*100:.1f}")

    print()

    def key(values: tuple[PredictionOutcome, ...]) -> float:
        return (
            statistics.mean((v.prediceted - v.target) ** 2 for v in values) ** 0.5 + 1
        )

    for player, values in sorted(
        player_xp,
        key=lambda x: (x[0].xP or 0) / (key(x[1])),
    )[-10:]:
        if player.xP:
            print(
                f"{player.webname:<20} {player.xP:<6.2f} "
                f"{key(values):<6.2f} {(player.xP or 0)/(key(values)):<6.2f}"
            )
