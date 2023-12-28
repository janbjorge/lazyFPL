from __future__ import annotations

import collections as C
import typing as T

from lazyfpl import structures


def team_constraint(lineup: T.Sequence[structures.Player], n: int) -> bool:
    """
    Checks if any team is over-represented in the lineup.

    Returns True if the maximum number of players from any
    single team in the lineup does not exceed 'n'.
    """
    return max(C.Counter(p.team for p in lineup).values()) <= n


def gkp_def_same_team(
    lineup: T.Sequence[structures.Player],
) -> bool:
    """
    Determines if any goalkeepers (GKP) and defenders (DEF) in the
    lineup are from the same team.
    Returns True if there is at least one common team between
    goalkeepers and defenders.
    """
    gkps = {p.team for p in lineup if p.position == "GKP"}
    defs = {p.team for p in lineup if p.position == "DEF"}
    return bool(gkps.intersection(defs))
