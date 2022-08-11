import typing as T
import itertools

import numpy as np

import structures


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
                f" {player.xP:<5.2f} {player.price/10:<6}"
                f" {player.team:<{15}} {player.name}({player.webname}) "
                f" {'X' if player.name in best else ''}"
            )


def header(pool: T.Sequence["structures.Player"], prefix="", postfix="") -> None:
    print(
        f"{prefix}Price: {squad_price(pool)/10} xP: {squad_xP(pool):.1f} n: {len(pool)}{postfix}"
    )


def xP(
    past_points: list[int],
    backtrace: int = 3,
) -> tuple[tuple[float, ...], float]:

    inference, train = past_points[:backtrace], past_points[backtrace:]
    assert len(train) >= backtrace
    m = list[tuple[int, list[int]]]()

    while train and len(train) > backtrace:
        target = train.pop(0)
        m.append((target, train[:backtrace]))

    coef, *_ = np.linalg.lstsq(
        np.array([x for _, x in m]),
        np.array([t for t, _ in m]),
        rcond=None,
    )

    return tuple(round(c, 3) for c in coef), np.array(inference).dot(coef.T)
