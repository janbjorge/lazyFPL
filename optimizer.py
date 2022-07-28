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
    min_cost_mid_fwd = min_cost_mid + min_cost_fwd

    best_squad: list[structures.Player] = []
    best_lineup: list[structures.Player] = []
    best_defs: float = 0
    best_mids: float = 0
    best_fwds: float = 0
    best_lineup_xp = 0
    step = len(mid_combinations) * len(fwd_combinations)

    def score_gk_def(c: list[structures.Player]) -> bool:
        return (
            helpers.squad_price(c) + min_cost_mid_fwd <= buget
            and constraints.team_constraint(c, n=3)
        )

    def score_gk_def_mid(c: list[structures.Player]) -> bool:
        return (
            helpers.squad_price(c) + min_cost_fwd <= buget
            and constraints.team_constraint(c, n=3)
        )

    def score_gk_def_mid_fwd(c: list[structures.Player]) -> bool:
        return (
            helpers.squad_price(c) <= buget
            and constraints.team_constraint(c, n=3)
            and helpers.best_lineup_xP(c) > best_lineup_xp
        )

    with tqdm(
        total=total,
        bar_format="{percentage:3.0f}%|{bar:20}{r_bar}",
        unit_scale=True,
        unit_divisor=1_000,
        ascii=True,
    ) as bar:
        for g in gkp_combinations:
            for d in def_combinations:
                bar.update(step)
                if sum(p.xP() for p in d) < best_defs:
                    continue
                gk_def = g + d
                if score_gk_def(gk_def):
                    for m in mid_combinations:
                        if sum(p.xP() for p in m) < best_mids:
                            break
                        gk_def_mid = gk_def + m
                        if score_gk_def_mid(gk_def_mid):
                            for f in fwd_combinations:
                                if sum(p.xP() for p in f) < best_fwds:
                                    break
                                gk_def_mid_fwd = gk_def_mid + f
                                if score_gk_def_mid_fwd(gk_def_mid_fwd):
                                    best_lineup = helpers.best_lineup(gk_def_mid_fwd)
                                    best_defs = sum(p.xP() for p in best_lineup if p.position == "DEF")
                                    best_mids = sum(p.xP() for p in best_lineup if p.position == "MID")
                                    best_fwds = sum(p.xP() for p in best_lineup if p.position == "FWD")
                                    best_lineup_xp = helpers.squad_xP(best_lineup)
                                    best_squad = list(gk_def_mid_fwd)
                                    helpers.lprint(best_squad, [p.name for p in best_lineup])
                                    print("-->>", best_lineup_xp)

    return best_squad


if __name__ == "__main__":
    import fetch

    # Top 3 players per position and price
    pool: list[structures.Player] = []
    for _, y in itertools.groupby(
        sorted(
            (p for p in fetch.players() if p.tm > 90 * 38 * 0.25),
            key=lambda x: (x.position, x.price, x.xP()),
        ),
        key=lambda x: (x.position, x.price),
    ):
        pool.extend(tuple(y)[:2])

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
