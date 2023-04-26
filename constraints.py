import collections as C
import typing as T

import structures


def team_constraint(lineup: T.Sequence["structures.Player"], n: int) -> bool:
    return max(C.Counter(p.team for p in lineup).values()) <= n


def gkp_def_same_team(
    lineup: T.Sequence["structures.Player"],
) -> bool:
    gkps = set(p.team for p in lineup if p.position == "GKP")
    defs = set(p.team for p in lineup if p.position == "DEF")
    return bool(gkps.intersection(defs))
