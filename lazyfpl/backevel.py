from __future__ import annotations

import dataclasses
import datetime
import statistics
import traceback
import typing

import more_itertools
import torch

from lazyfpl import conf, fetch, helpers, ml_model, structures


@dataclasses.dataclass
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
                    ).unsqueeze(0)
                )
                .detach()
                .numpy()
            )

            assert xP is not None
            assert target.points is not None
            yield PredictionOutcome(
                prediceted=xP,
                target=target.points,
                kickoff=target.kickoff_time,
            )


def players_backeval(
    top_n_total_points: int = 100,
) -> typing.Generator[
    tuple[structures.Player, tuple[PredictionOutcome, ...]],
    None,
    None,
]:
    """
    Evaluates the back-evaluation for all players and returns
    a dictionary with the results.
    """
    for player in sorted(
        sorted(fetch.players(), key=lambda x: x.tp())[-top_n_total_points:],
        key=lambda x: (
            x.team,
            helpers.position_order(x.position),
            x.name,
        ),
    ):
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
    for n in range(1, 6):
        rc = statistics.mean(
            1 if abs(v.prediceted - v.target) <= n else 0
            for _, values in player_xp
            for v in values
        )
        print(f"RC{n}: {rc*100:.1f}")

    print()

    print(f"Num selected for backeval: {len(player_xp)}")
