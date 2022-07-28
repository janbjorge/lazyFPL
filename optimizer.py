import itertools
import statistics

from tqdm import (
    tqdm,
)

import constraints
import helpers
import structures


def lineup(
    pool: list[structures.Player],
    buget: int = 1_000,
):

    gkp_combinations = sorted(
        (
            c
            for c in itertools.combinations((p for p in pool if p.position == "GK"), 2)
            if constraints.team_constraint(c, 1)
        ),
        key=helpers.squad_xP,
        reverse=True,
    )

    def_combinations = sorted(
        (
            c
            for c in itertools.combinations((p for p in pool if p.position == "DEF"), 5)
            if constraints.team_constraint(c, 2)
        ),
        key=helpers.squad_xP,
        reverse=True,
    )

    mid_combinations = sorted(
        (
            c
            for c in itertools.combinations((p for p in pool if p.position == "MID"), 5)
            if constraints.team_constraint(c, 2)
        ),
        key=helpers.squad_xP,
        reverse=True,
    )

    fwd_combinations = sorted(
        (
            c
            for c in itertools.combinations((p for p in pool if p.position == "FWD"), 3)
            if constraints.team_constraint(c, 1)
        ),
        key=helpers.squad_xP,
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

    min_cost_mid = helpers.squad_price(min(mid_combinations, key=helpers.squad_price))
    min_cost_fwd = helpers.squad_price(min(fwd_combinations, key=helpers.squad_price))

    max_cost_mid = helpers.squad_price(max(mid_combinations, key=helpers.squad_price))
    max_cost_fwd = helpers.squad_price(max(fwd_combinations, key=helpers.squad_price))

    min_cost_mid_fwd = min_cost_mid + min_cost_fwd
    max_cost_mid_fwd = max_cost_mid + max_cost_fwd

    max_xp_mid = helpers.squad_xP(max(mid_combinations, key=helpers.squad_xP))
    max_xp_fwd = helpers.squad_xP(max(fwd_combinations, key=helpers.squad_xP))
    max_xp_mid_fwd = max_xp_mid + max_xp_fwd

    best_lineup: list[structures.Player] = []
    buget_lower = buget * 0.9
    best_xp = 0
    step = len(mid_combinations) * len(fwd_combinations)

    def score_gk_def(c: list[structures.Player]) -> bool:
        return (
            (
                buget_lower - max_cost_mid_fwd
                <= helpers.squad_price(c)
                <= buget - min_cost_mid_fwd
            )
            and constraints.team_constraint(c, n=3)
            and helpers.squad_xP(c) + max_xp_mid_fwd > best_xp
        )

    def score_gk_def_mid(c: list[structures.Player]) -> bool:
        return (
            buget_lower - max_cost_fwd <= helpers.squad_price(c) <= buget - min_cost_fwd
            and constraints.team_constraint(c, n=3)
            and helpers.squad_xP(c) + max_xp_fwd > best_xp
        )

    def score_gk_def_mid_fwd(c: list[structures.Player]) -> bool:
        return (
            helpers.squad_price(c) <= buget
            and constraints.team_constraint(c, n=3)
            and helpers.best_lineup_xP(c) >= best_xp
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
                if score_gk_def(gk_def):
                    for m in mid_combinations:
                        gk_def_mid = gk_def + m
                        if score_gk_def_mid(gk_def_mid):
                            for f in fwd_combinations:
                                gk_def_mid_fwd = gk_def_mid + f
                                if score_gk_def_mid_fwd(gk_def_mid_fwd):
                                    bl = helpers.best_lineup(gk_def_mid_fwd)
                                    best_xp = helpers.squad_xP(bl)
                                    best_lineup = gk_def_mid_fwd
                                    helpers.lprint(best_lineup, [p.name for p in bl])
                                    print("-->>", best_xp)

    return best_lineup


if __name__ == "__main__":
    import fetch

    # Top 3 players per position and price
    pool: list[structures.Player] = []
    for _, y in itertools.groupby(
        sorted(
            (p for p in fetch.players() if p.xP() > 0.5 and p.tm > 90 * 38 * 0.5),
            key=lambda x: (x.position, x.price),
        ),
        key=lambda x: (x.position, x.price),
    ):
        pool.extend(tuple(y)[:3])

    # pool = [
    #     p
    #     for _, players in fetch.top_position_players(
    #         strikers=0,
    #         midfielders=0,
    #         defenders=0,
    #         goalkeeper=0,
    #     )
    #     for p in players
    # ]

    helpers.lprint(pool)
    helpers.lprint(lineup(pool=pool))
