import collections
import functools
import itertools
import os
import typing as T

import numpy as np

import structures


@functools.cache
def debug() -> bool:
    return bool(os.environ.get("FPL_DEBUG"))


@functools.cache
def lookahead() -> int:
    return int(os.environ.get("FPL_LOOKAHEAD", "1"))


@functools.cache
def backtrace() -> int:
    return int(os.environ.get("FPL_BACKTRACE", "3"))


def squad_price(lineup: T.Sequence["structures.Player"]) -> int:
    return sum(p.price for p in lineup)


def squad_xP(lineup: T.Sequence["structures.Player"]) -> float:
    return sum(p.xP for p in lineup)


def overall_xP(lineup: T.Sequence["structures.Player"]) -> float:
    return (squad_xP(lineup) ** 2 + best_lineup_xP(lineup) ** 2) ** 0.5


def best_lineup(
    team: T.Sequence["structures.Player"],
    min_gkp: int = 1,
    min_def: int = 3,
    min_mid: int = 2,
    min_fwd: int = 1,
    size: int = 11,
) -> list["structures.Player"]:
    team = sorted(team, key=lambda x: x.xP, reverse=True)
    gkps = [p for p in team if p.position == "GKP"]
    defs = [p for p in team if p.position == "DEF"]
    mids = [p for p in team if p.position == "MID"]
    fwds = [p for p in team if p.position == "FWD"]
    best = gkps[:min_gkp] + defs[:min_def] + mids[:min_mid] + fwds[:min_fwd]
    remainder = sorted(
        defs[min_def:] + mids[min_mid:] + fwds[min_fwd:],
        key=lambda x: x.xP,
        reverse=True,
    )
    return best + remainder[: (size - len(best))]


def best_lineup_xP(lineup: T.Sequence["structures.Player"]) -> float:
    return squad_xP(best_lineup(lineup))


def valid_squad(
    squad: T.Sequence["structures.Player"],
    gkps: int = 2,
    defs: int = 5,
    mids: int = 5,
    fwds: int = 3,
) -> bool:
    cnt = collections.Counter(p.position for p in squad)
    return (
        cnt["GKP"] == gkps
        and cnt["DEF"] == defs
        and cnt["MID"] == mids
        and cnt["FWD"] == fwds
    )


def lprint(
    lineup: T.Sequence["structures.Player"],
    best: T.Sequence[str] | None = None,
) -> None:

    best = best or []

    if not lineup:
        return

    def position_order(position: str) -> int:
        if position == "GKP":
            return 0
        if position == "DEF":
            return 1
        if position == "MID":
            return 2
        if position == "FWD":
            return 3
        raise NotImplementedError(position)

    header(lineup)
    for pos, _players in itertools.groupby(
        sorted(
            lineup,
            key=lambda x: (position_order(x.position), x.xP),
            reverse=True,
        ),
        key=lambda x: x.position,
    ):
        players = list(_players)
        header(players, prefix=f"{pos}(", postfix=")")
        print(
            "BIS  xP     Price  TP   UD       Team            Position  Player"
            + " " * 15
            + "News"
        )
        for player in players:
            print(("X    " if player.name in best else "     ") + str(player))


def header(
    pool: T.Sequence["structures.Player"],
    prefix: str = "",
    postfix: str = "",
) -> None:
    print(
        f"{prefix}Price: {squad_price(pool)/10} oxP: {overall_xP(pool):.1f} n: {len(pool)}{postfix}",
    )


def xP(
    fixtures: list["structures.Fixture"],
    backtrace: int = backtrace(),
    lookahead: int = lookahead(),
) -> tuple[tuple[float, ...], float]:

    fixtures = sorted(fixtures, key=lambda x: x.kickoff_time)
    # time --->
    back = (backtrace + 2) ** 2
    train = [f for f in fixtures if not f.upcoming][-back:]

    assert len(train) >= backtrace
    targets = list[float]()
    coefficients = list[tuple[float, ...]]()

    while len(train) > backtrace:
        target = train.pop(-1)
        bt1, bt2, bt3 = train[-backtrace:]

        assert target.points is not None
        assert bt1.points is not None
        assert bt2.points is not None
        assert bt3.points is not None

        targets.append(target.points)
        coefficients.append(
            (
                round(bt3.points / bt3.relative.combined, 2),
                round(bt2.points / bt2.relative.combined, 2),
                round(bt1.points / bt1.relative.combined, 2),
            )
        )

    coef, *_ = np.linalg.lstsq(
        np.array(coefficients),
        np.array(targets),
        rcond=None,
    )

    _sum = sum(abs(v) for v in coef)
    if abs(_sum) > 1e-7:
        coef = coef / _sum
    coef = np.clip(coef, -1, 1)

    expected = list[float]()
    inference = [f for f in fixtures if not f.upcoming][-backtrace:]
    inference = [f.points / f.relative.combined for f in inference]
    upcoming = [f for f in fixtures if f.upcoming]
    for _this, _next in zip(
        upcoming[:lookahead],
        upcoming[1:],
    ):
        expected.append(np.array(inference).dot(coef.T) * _next.relative.combined)
        inference.pop(0)
        inference.append(
            expected[-1] * _this.relative.combined / _next.relative.combined
        )

    return tuple(round(c, 3) for c in coef), sum(expected)
