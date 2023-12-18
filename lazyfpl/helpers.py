import collections
import typing as T

from lazyfpl import conf, structures


def squad_price(lineup: T.Sequence["structures.Player"]) -> int:
    return sum(p.price for p in lineup)


def squad_xP(lineup: T.Sequence["structures.Player"]) -> float:
    return sum(p.xP or 0 for p in lineup)


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


def sscore(lineup: T.Sequence["structures.Player"], n: int = conf.lookahead) -> int:
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


def tcnt(lineup: T.Sequence["structures.Player"]) -> int:
    return sum(v - 1 for v in collections.Counter(p.team for p in lineup).values()) * 2


def tsscore(lineup: T.Sequence["structures.Player"], n: int = conf.lookahead) -> float:
    return (tcnt(lineup) ** 2 + sscore(lineup, n=n) ** 2) ** 0.5
