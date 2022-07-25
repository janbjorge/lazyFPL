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
        (p for p in pool if p.position == "GK"), key=lambda p: p.xP(), reverse=True
    )
    _def = sorted(
        (p for p in pool if p.position == "DEF"), key=lambda p: p.xP(), reverse=True
    )
    _mid = sorted(
        (p for p in pool if p.position == "MID"), key=lambda p: p.xP(), reverse=True
    )
    _fwd = sorted(
        (p for p in pool if p.position == "FWD"), key=lambda p: p.xP(), reverse=True
    )

    gkp_combinations = tuple(
        sorted(itertools.combinations(_gkp, 2), key=helpers.total_xP, reverse=True)
    )
    gkp_combinations = tuple(c for c in gkp_combinations if constraints.team_constraint(c, n=1))

    def_combinations = tuple(
        sorted(itertools.combinations(_def, 5), key=helpers.total_xP, reverse=True)
    )
    def_combinations = tuple(c for c in def_combinations if constraints.team_constraint(c, n=2))

    mid_combinations = tuple(
        sorted(itertools.combinations(_mid, 5), key=helpers.total_xP, reverse=True)
    )
    mid_combinations = tuple(c for c in mid_combinations if constraints.team_constraint(c, n=2))

    fwd_combinations = tuple(
        sorted(itertools.combinations(_fwd, 3), key=helpers.total_xP, reverse=True)
    )
    fwd_combinations = tuple(c for c in fwd_combinations if constraints.team_constraint(c, n=1))

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

    max_xp_mid = helpers.total_xP(max(mid_combinations, key=helpers.total_xP))
    max_xp_fwd = helpers.total_xP(max(fwd_combinations, key=helpers.total_xP))

    min_cost_mid_fwd = min_cost_mid + min_cost_fwd
    max_cost_mid_fwd = max_cost_mid + max_cost_fwd
    max_xp_mid_fwd = max_xp_mid + max_xp_fwd

    best_lineup: T.List[structures.Player] = []
    buget_lower = buget * 0.8
    best_xp = float("-Inf")
    step = len(mid_combinations) * len(fwd_combinations)

    def lvl1(c):
        return (
            buget_lower - max_cost_mid_fwd
            <= helpers.total_price(c)
            <= buget - min_cost_mid_fwd
            and helpers.total_xP(c) + max_xp_mid_fwd > best_xp
            and constraints.team_constraint(c)
            and constraints.gkp_def_not_same_team(c)
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
            and helpers.total_xP(c) >= best_xp
            and constraints.team_constraint(c)
        )

    with tqdm(
        total=total,
        bar_format="{percentage:3.0f}%|{bar:20}{r_bar}",
        unit_scale=True,
        unit_divisor=2**10,
    ) as bar:
        for g in gkp_combinations:
            for d in def_combinations:
                bar.update(step)
                gk_def = g + d
                if lvl1(gk_def):
                    for m in mid_combinations:
                        gk_def_mid = gk_def + m
                        if lvl2(gk_def_mid):
                            for f in fwd_combinations:
                                gk_def_mid_fwd = gk_def_mid + f
                                if lvl3(gk_def_mid_fwd):
                                    best_xp = helpers.total_xP(gk_def_mid_fwd)
                                    best_lineup = gk_def_mid_fwd
                                    helpers.lprint(best_lineup)

    return best_lineup


if __name__ == "__main__":
    import fetch

    pool = []
    for _, top in fetch.top_position_players(
        strikers=15,
        midfielders=20,
        defenders=20,
        goalkeeper=15,
    ):
        pool.extend(top)

    helpers.lprint(pool)
    helpers.lprint(lineup(pool=pool))
