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

    gkp_combinations = sorted(
        (
            c
            for c in itertools.combinations((p for p in pool if p.position == "GK"), 2)
            if constraints.team_constraint(c, 1)
        ),
        key=helpers.total_xP,
        reverse=True,
    )

    def_combinations = sorted(
        (
            c
            for c in itertools.combinations((p for p in pool if p.position == "DEF"), 5)
            if constraints.team_constraint(c, 2)
        ),
        key=helpers.total_xP,
        reverse=True,
    )

    mid_combinations = sorted(
        (
            c
            for c in itertools.combinations((p for p in pool if p.position == "MID"), 5)
            if constraints.team_constraint(c, 2)
        ),
        key=helpers.total_xP,
        reverse=True,
    )

    fwd_combinations = sorted(
        (
            c
            for c in itertools.combinations((p for p in pool if p.position == "FWD"), 3)
            if constraints.team_constraint(c, 1)
        ),
        key=helpers.total_xP,
        reverse=True,
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
            and constraints.team_constraint(c, n=3)
            and constraints.gkp_def_not_same_team(c)
        )

    def lvl2(c):
        return (
            buget_lower - max_cost_fwd <= helpers.total_price(c) <= buget - min_cost_fwd
            and helpers.total_xP(c) + max_xp_fwd > best_xp
            and constraints.team_constraint(c, n=3)
        )

    def lvl3(c):
        return (
            helpers.total_price(c) <= buget
            and helpers.total_xP(c) >= best_xp
            and constraints.team_constraint(c, n=3)
        )

    with tqdm(
        total=total,
        bar_format="{percentage:3.0f}%|{bar:20}{r_bar}",
        unit_scale=True,
        unit_divisor=2**10,
        ascii=True,
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

    pool = [
        p
        for _, players in fetch.top_position_players(
            strikers=0,
            midfielders=0,
            defenders=0,
            goalkeeper=0,
        )
        for p in players
    ]

    pool = [p for p in pool if sum(p.minutes) > 90 * 38 * 0.1 and p.xP() > 0.2]
    helpers.lprint(pool)
    helpers.lprint(lineup(pool=pool))
