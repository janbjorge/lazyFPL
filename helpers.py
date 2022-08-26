import itertools
import os
import typing as T

import numpy as np

import structures


def lookahead() -> int | None:
    try:
        return int(os.environ["FPL_LOOKAHEAD"])
    except KeyError:
        return None


def backtrace() -> int:
    return int(os.environ.get("FPL_BACKTRACE", "3"))


def squad_price(lineup: T.Sequence["structures.Player"]) -> int:
    return sum(p.price for p in lineup)


def squad_xP(lineup: T.Sequence["structures.Player"]) -> float:
    return sum(p.xP for p in lineup)


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


def lprint(
    lineup: T.Sequence["structures.Player"], best: T.Sequence[str] | None = None
) -> None:

    if not best:
        best = []

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
        print(f" xP    Price  Team            Player")
        for player in players:
            print(
                f" {player.xP:<5.1f} {player.price/10:<6}"
                f" {player.team:<{15}} {player.name}({player.webname}) "
                f" {'X' if player.name in best else ''}"
            )


def header(pool: T.Sequence["structures.Player"], prefix="", postfix="") -> None:
    print(
        f"{prefix}Price: {squad_price(pool)/10} xP: {squad_xP(pool):.1f} n: {len(pool)}{postfix}"
    )


def xP(
    fixtures: list["structures.Fixture"],
    backtrace: int = backtrace(),
    lookahead: int | None = lookahead(),
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
                bt3.points * bt3.relative.combined,
                bt2.points * bt2.relative.combined,
                bt1.points * bt1.relative.combined,
            )
        )

    coef, *_ = np.linalg.lstsq(
        np.array(coefficients),
        np.array(targets),
        rcond=None,
    )

    _sum = coef.sum()
    if abs(_sum) > 1e-6:
        coef = coef / _sum
    coef = np.clip(coef, -1, 1)

    expected = list[float]()
    inference = [f for f in fixtures if not f.upcoming][-backtrace:]
    inference = [f.points * f.relative.combined for f in inference]
    upcoming = [f for f in fixtures if f.upcoming]
    for _this, _next in zip(
        upcoming[:lookahead],
        upcoming[1:],
    ):
        expected.append(np.array(inference).dot(coef.T) / _next.relative.combined)
        inference.pop(0)
        inference.append(expected[-1] * _this.relative.combined)

    return tuple(round(c, 3) for c in coef), sum(expected)
