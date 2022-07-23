import typing as T

import structures


def total_price(lineup: list[structures.Player]) -> int:
    return sum(p.price[-1] for p in lineup)


def total_xP(lineup: T.Sequence[structures.Player]) -> float:
    return sum(p.xP for p in lineup)
