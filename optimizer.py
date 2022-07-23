import typing as T
import itertools

from tqdm import (
    tqdm,
)

import constraints
import helpers
import structures


def lineup(
    pool: list[structures.Player],
    buget: int = 1_000,
) -> list[structures.Player]:

    _gkp = sorted(
        (p for p in pool if p.position == "GK"), key=lambda p: p.xP, reverse=True
    )
    _def = sorted(
        (p for p in pool if p.position == "DEF"), key=lambda p: p.xP, reverse=True
    )
    _mid = sorted(
        (p for p in pool if p.position == "MID"), key=lambda p: p.xP, reverse=True
    )
    _fwd = sorted(
        (p for p in pool if p.position == "FWD"), key=lambda p: p.xP, reverse=True
    )

    gkp_combinations = tuple(
        sorted(itertools.combinations(_gkp, 2), key=helpers.total_xP, reverse=True)
    )
    def_combinations = tuple(
        sorted(itertools.combinations(_def, 5), key=helpers.total_xP, reverse=True)
    )
    mid_combinations = tuple(
        sorted(itertools.combinations(_mid, 5), key=helpers.total_xP, reverse=True)
    )
    fwd_combinations = tuple(
        sorted(itertools.combinations(_fwd, 3), key=helpers.total_xP, reverse=True)
    )

    total = (
        len(gkp_combinations)
        * len(def_combinations)
        * len(mid_combinations)
        * len(fwd_combinations)
    )

    print(f"Goalkeeper combinations: {len(gkp_combinations)}")
    print(f"Defender   combinations: {len(def_combinations)}")
    print(f"Midfielder combinations: {len(mid_combinations)}")
    print(f"Forwarder  combinations: {len(fwd_combinations)}")
    print(f"Total      combinations: {total:.1e}")

    if not total:
        return []

    min_cost_mid = helpers.total_price(min(mid_combinations, key=helpers.total_price))
    min_cost_fwd = helpers.total_price(min(fwd_combinations, key=helpers.total_price))

    max_cost_mid = helpers.total_price(max(mid_combinations, key=helpers.total_price))
    max_cost_fwd = helpers.total_price(max(fwd_combinations, key=helpers.total_price))

    max_xp_gkp = helpers.total_xP(max(gkp_combinations, key=helpers.total_xP))
    max_xp_def = helpers.total_xP(max(def_combinations, key=helpers.total_xP))
    max_xp_mid = helpers.total_xP(max(mid_combinations, key=helpers.total_xP))
    max_xp_fwd = helpers.total_xP(max(fwd_combinations, key=helpers.total_xP))

    min_cost_mid_fwd = min_cost_mid + min_cost_fwd
    max_cost_mid_fwd = max_cost_mid + max_cost_fwd
    max_xp_mid_fwd = max_xp_mid + max_xp_fwd

    best_lineup: T.List[structures.Player] = []
    buget_lower = buget * 0.85
    best_xp = sum((max_xp_gkp, max_xp_def, max_xp_mid, max_xp_fwd))
    step = len(mid_combinations) * len(fwd_combinations)

    def lvl1(c):
        return (
            buget_lower - max_cost_mid_fwd
            <= helpers.total_price(c)
            <= buget - min_cost_mid_fwd
            and helpers.total_xP(c) + max_xp_mid_fwd > best_xp
            and constraints.team_constraint(c)
        )

    def lvl2(c):
        return (
            buget_lower - max_cost_fwd <= helpers.total_price(c) <= buget - min_cost_fwd
            and helpers.total_xP(c) + max_xp_fwd > best_xp
            and constraints.team_constraint(c)
        )

    def lvl3(c):
        return (
            helpers.total_price(c) <= buget
            and helpers.total_xP(c) > best_xp
            and constraints.team_constraint(c)
        )

    while not best_lineup:

        best_xp = best_xp * 0.95

        with tqdm(
            total=total,
            bar_format="{percentage:3.0f}%|{bar:20}{r_bar}",
            unit_scale=True,
            unit_divisor=2**10,
        ) as bar:
            for g in gkp_combinations:
                for d in def_combinations:
                    bar.update(step)
                    g1 = g + d
                    if lvl1(g1):
                        for m in mid_combinations:
                            g2 = g1 + m
                            if lvl2(g2):
                                for f in fwd_combinations:
                                    g3 = g2 + f
                                    if lvl3(g3):
                                        best_xp = helpers.total_xP(g3)
                                        best_lineup = g3
                                        print(best_xp)

    return best_lineup


if __name__ == "__main__":
    import fetch
    pool = fetch.players()
    pool = [p for p in pool if p.xP > 4]
    print(len(pool))
    for p in sorted(lineup(pool=pool), key=lambda x: x.position):
        print(p.position, p.team[-1], p.name, p.xP)