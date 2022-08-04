import typing as T
import itertools
import math

import structures


def squad_price(lineup: T.Sequence[structures.Player]) -> int:
    return sum(p.price for p in lineup)


def squad_xP(lineup: T.Sequence[structures.Player]) -> float:
    return sum(p.xP() for p in lineup)


def valid_formation(
    lineup: T.Sequence[structures.Player],
    eligible: tuple[tuple[int, int, int, int], ...] = (
        # gk, def, mid, fwd
        (1, 3, 4, 3),
        (1, 3, 5, 2),
        (1, 4, 3, 3),
        (1, 4, 4, 2),
        (1, 4, 5, 1),
        (1, 5, 2, 3),
        (1, 5, 3, 2),
        (1, 5, 4, 1),
    ),
) -> bool:
    gkps = sum(1 for p in lineup if p.position == "GKP")
    if gkps != 1:
        return False
    defs = sum(1 for p in lineup if p.position == "DEF")
    if not (3 <= defs <= 5):
        return False
    mids = sum(1 for p in lineup if p.position == "MID")
    if not (3 <= mids <= 5):
        return False
    fwds = sum(1 for p in lineup if p.position == "FWD")
    if not (1 <= fwds <= 3):
        return False
    return (gkps, defs, mids, fwds) in eligible


def best_lineup(
    team: T.Sequence[structures.Player],
    size: int = 11,
) -> tuple[structures.Player, ...]:
    return max(
        itertools.combinations(team, size),
        key=lambda c: valid_formation(c) * squad_xP(c),
    )


def best_lineup_xP(lineup: T.Sequence[structures.Player]) -> float:
    return squad_xP(best_lineup(lineup))


def lprint(lineup: T.Sequence[structures.Player], best: T.Sequence[str] | None = None) -> None:

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

    print("", flush=True)
    header(lineup)
    for pos, _players in itertools.groupby(
        sorted(
            lineup, key=lambda x: (position_order(x.position), x.xP()), reverse=True,
        ),
        key=lambda x: x.position,
    ):
        players = list(_players)
        header(players, prefix=f"{pos}(", postfix=")")
        print(f" xP    Price  Team            Player")
        for player in players:
            print(
                f" {player.xP():<5.2f} {player.price/10:<6}"
                f" {player.team:<{15}} {player.name}({player.webname}) "
                f" {'X' if player.name in best else ''}"
            )


def header(pool: T.Sequence[structures.Player], prefix="", postfix="") -> None:
    print(
        f"{prefix}Price: {squad_price(pool)/10} xP: {squad_xP(pool):.1f} n: {len(pool)}{postfix}"
    )
