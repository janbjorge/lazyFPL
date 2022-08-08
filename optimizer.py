import itertools
import statistics
import typing as T

from tqdm import (
    tqdm,
)

import constraints
import helpers
import structures


def lineup(
    pool: T.Sequence[structures.Player],
    budget_lower: int = 950,
    budget_upper: int = 1_000,
    min_xp_gkp_combination: float = 4.0,
    min_xp_def_combination: float = 20.0,
    min_xp_mid_combination: float = 25.0,
    min_xp_fwd_combination: float = 7.0,
    # min_xp_gkp_combination: float = 0,
    # min_xp_def_combination: float = 0,
    # min_xp_mid_combination: float = 0,
    # min_xp_fwd_combination: float = 0,
) -> T.Sequence[structures.Player]:

    gkp_combinations = sorted(
        (
            (helpers.squad_price(c), helpers.squad_xP(c), c)
            for c in itertools.combinations((p for p in pool if p.position == "GKP"), 2)
        ),
        key=lambda x: x[1],
        reverse=True,
    )
    gkp_combinations = [
        c
        for c in gkp_combinations
        if c[1] > min_xp_gkp_combination
        and any(
            p.price == min(p.price for p in pool if p.position == "GKP") for p in c[-1]
        )
    ]

    def_combinations = sorted(
        (
            (helpers.squad_price(c), helpers.squad_xP(c), c)
            for c in itertools.combinations((p for p in pool if p.position == "DEF"), 5)
            if constraints.team_constraint(c, 3)
        ),
        key=lambda x: x[0],
        reverse=True,
    )
    def_combinations = [c for c in def_combinations if c[1] > min_xp_def_combination]

    mid_combinations = sorted(
        (
            (helpers.squad_price(c), helpers.squad_xP(c), c)
            for c in itertools.combinations((p for p in pool if p.position == "MID"), 5)
            if constraints.team_constraint(c, 3)
        ),
        key=lambda x: x[1],
        reverse=True,
    )
    mid_combinations = [c for c in mid_combinations if c[1] > min_xp_mid_combination]

    fwd_combinations = sorted(
        (
            (helpers.squad_price(c), helpers.squad_xP(c), c)
            for c in itertools.combinations((p for p in pool if p.position == "FWD"), 3)
        ),
        key=lambda x: x[1],
        reverse=True,
    )
    fwd_combinations = [c for c in fwd_combinations if c[1] > min_xp_fwd_combination]

    total = (
        len(gkp_combinations)
        * len(def_combinations)
        * len(mid_combinations)
        * len(fwd_combinations)
    )

    print(f"Goalkeeper combinations: {len(gkp_combinations):.1e}")
    print(f"Defender   combinations: {len(def_combinations):.1e}")
    print(f"Midfielder combinations: {len(mid_combinations):.1e}")
    print(f"Forwarder  combinations: {len(fwd_combinations):.1e}")
    print(f"Total      combinations: {total:.1e}")

    if not total:
        return []

    best_squad = tuple[structures.Player, ...]()
    best_lxp = 60.0
    gxp = 70.0

    max_mid_price = max(price for price, _, _ in mid_combinations)
    min_mid_price = min(price for price, _, _ in mid_combinations)
    max_mid_xp = max(xp for _, xp, _ in mid_combinations)

    with tqdm(
        total=total,
        bar_format="{percentage:3.0f}% | {bar:20} {r_bar}",
        unit_scale=True,
        unit_divisor=1_000,
        ascii=True,
    ) as bar:
        for gp, gxp, g in gkp_combinations:
            for fp, fxp, f in fwd_combinations:
                bar.update(len(def_combinations) * len(mid_combinations))
                for dp, dxp, d in def_combinations:

                    if gp + fp + dp + max_mid_price < budget_lower:
                        break

                    if gp + fp + dp + min_mid_price > budget_upper:
                        continue

                    if (gxp + fxp + dxp + max_mid_xp) < gxp:
                        continue

                    if not constraints.team_constraint(g + f + d, n=4):
                        continue

                    for mp, mxp, m in mid_combinations:

                        if (gxp + fxp + dxp + mxp) < gxp:
                            break

                        if (
                            budget_lower <= mp + dp + fp + gp <= budget_upper
                            and gxp + fxp + dxp + mxp >= best_lxp
                            and constraints.team_constraint(squad := g + f + d + m, n=3)
                            and (bl := helpers.best_lineup(squad))
                            and (blxp := helpers.squad_xP(bl)) > best_lxp
                        ):
                            best_lxp = blxp
                            best_squad = squad
                            helpers.lprint(best_squad, [p.name for p in bl])
                            print(
                                f"-->> lxp={best_lxp:.2f}, gxp={gxp + fxp + dxp + mxp:.2f} "
                            )

    # NOTE: without candidates(...) (26316.53seconds) xP = 66.12268150503445
    # NOTE: with candidates(...), alpha=.9(600 seconds) xP = 65.64198652433947
    # -->> 64.24060150375941 alpha = .85
    # assert best_lxp > 66.8
    return best_squad


if __name__ == "__main__":
    import statistics
    import fetch

    pool: list[structures.Player] = []
    for position, _position_candidates in itertools.groupby(
        sorted(
            [
                p
                for p in fetch.players()
                if not p.news and p.xP() > 0
            ],
            key=lambda x: x.position,
        ),
        key=lambda x: x.position,
    ):
        position_candidates = sorted(list(_position_candidates), key=lambda x: x.xP())
        cut = statistics.mean(p.xP() for p in position_candidates) + statistics.stdev(p.xP() for p in position_candidates)
        pool.extend([p for p in position_candidates if p.xP() > cut])
        pool.extend([p for p in position_candidates if p.xP() <= cut][:5])

    # for _, players in itertools.groupby(
    #     sorted(
    #         (p for p in fetch.players() if not p.news and p.xP() > 0),
    #         key=lambda x: (x.position, round(x.price / x.xP(),1))
    #     ),
    #     key=lambda x:  (x.position, round(x.price / x.xP(),1)),
    # ):
    #     candidates = sorted(list(players), key=lambda x: x.xP())
    #     pool.extend(candidates[-n:]

    # Just in case.
    pool = list(set(pool))

    helpers.lprint(pool)
    squad = lineup(pool=pool)
    helpers.lprint(squad, best=[p.name for p in helpers.best_lineup(squad)])
    print("-->>", helpers.best_lineup_xP(squad))
