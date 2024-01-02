from __future__ import annotations

import collections
import functools
from typing import Sequence, get_args

from tabulate import tabulate

from lazyfpl import conf, database, structures


def squad_price(lineup: Sequence[structures.Player]) -> int:
    """Calculates and returns the total price of a football squad."""
    return sum(p.price for p in lineup)


def squad_xP(lineup: Sequence[structures.Player]) -> float:
    """Calculates and returns the total expected points (xP) of a football squad."""
    return sum(p.xP or 0 for p in lineup)


def overall_xP(lineup: Sequence[structures.Player]) -> float:
    """Calculates and returns the overall expected points (xP) for a lineup."""
    return (squad_xP(lineup) ** 2 + best_lineup_xP(lineup) ** 2) ** 0.5


def best_lineup(
    team: Sequence[structures.Player],
    min_gkp: int = 1,
    min_def: int = 3,
    min_mid: int = 2,
    min_fwd: int = 1,
    size: int = 11,
) -> list[structures.Player]:
    """Determines the best lineup based on expected points,
    respecting position constraints.
    """
    team = sorted(team, key=lambda x: x.xP or 0, reverse=True)
    gkps = [p for p in team if p.position == "GKP"]
    defs = [p for p in team if p.position == "DEF"]
    mids = [p for p in team if p.position == "MID"]
    fwds = [p for p in team if p.position == "FWD"]
    best = gkps[:min_gkp] + defs[:min_def] + mids[:min_mid] + fwds[:min_fwd]
    remainder = sorted(
        defs[min_def:] + mids[min_mid:] + fwds[min_fwd:],
        key=lambda x: x.xP or 0,
        reverse=True,
    )
    return best + remainder[: (size - len(best))]


def best_lineup_xP(lineup: Sequence[structures.Player]) -> float:
    """Calculates and returns the expected points of the best possible lineup."""
    return squad_xP(best_lineup(lineup))


def valid_squad(
    squad: Sequence[structures.Player],
    gkps: int = 2,
    defs: int = 5,
    mids: int = 5,
    fwds: int = 3,
) -> bool:
    """Checks if a squad meets the specified position requirements."""
    tally = collections.Counter(p.position for p in squad)
    return (
        tally["GKP"] == gkps
        and tally["DEF"] == defs
        and tally["MID"] == mids
        and tally["FWD"] == fwds
    )


def sscore(lineup: Sequence[structures.Player], n: int = conf.lookahead) -> int:
    """Calculates and returns the 'schedule score' based on players
    playing in the same match."""
    # "sscore -> "schedule score"
    # counts players in the lineup who plays in same match.
    # Ex. l'pool vs. man. city, and your team has Haaland and Salah as the only
    # players from the l'pool and city, the sscore is 2 since both play
    # the same match (assuming they start/play ofc.)

    per_gw = collections.defaultdict(list)
    for player in lineup:
        for i, nextopp in enumerate(player.upcoming_opponents()[:n]):
            per_gw[i].append((player.team, nextopp))

    return sum(sum(vs.count(x[::-1]) for x in set(vs)) for vs in per_gw.values())


def tcnt(lineup: Sequence[structures.Player]) -> int:
    """Counts and returns the total number of team constraints in a lineup."""
    return sum(v - 1 for v in collections.Counter(p.team for p in lineup).values()) * 2


def tsscore(lineup: Sequence[structures.Player], n: int = conf.lookahead) -> float:
    """Calculates and returns the total 'team schedule score' for a lineup."""
    return (tcnt(lineup) ** 2 + sscore(lineup, n=n) ** 2) ** 0.5


@functools.cache
def position_order(position: database.POSITIONS) -> int:
    return {p: n for n, p in enumerate(get_args(database.POSITIONS))}[position]


def tabulater(tabular_data: list[dict[str, str | float | None]]) -> str:
    return tabulate(
        tabular_data,
        tablefmt=conf.tabulate_format,
        headers={},
        numalign="left",
        rowalign="left",
        stralign="left",
    )
