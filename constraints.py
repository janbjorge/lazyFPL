import collections as C
import typing as T

import structures


def team_constraint(lineup: T.Sequence[structures.Player], n: int = 3) -> bool:
    count = C.Counter(p.team[-1] for p in lineup)
    return max(count.values()) <= n


def position_constraint(
    lineup: T.Sequence[structures.Player],
    n: int,
    position: T.Literal["GK", "DEF", "MID", "FWD"],
) -> bool:
    return sum(1 for p in lineup if p.position == position) <= n


def must_contain(
    lineup: T.Sequence[structures.Player],
    must: set[structures.Player],
) -> bool:
    return must.issubset(lineup)


def gkp_def_not_same_team(
    lineup: T.Sequence[structures.Player],
) -> bool:
    _gkps = set(p.team for p in lineup if p.position == "GK")
    _defs = set(p.team for p in lineup if p.position == "DEF")
    return not bool(_gkps.intersection(_defs))


def valid_formation(lineup: T.Sequence[structures.Player]) -> bool:

    if sum(1 for p in lineup if p.position == "GK") != 1:
        return False

    if sum(1 for p in lineup if p.position == "DEF") < 3:
        return False

    if sum(1 for p in lineup if p.position == "FWD") < 1:
        return False

    return True
