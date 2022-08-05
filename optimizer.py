import itertools
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
) -> T.Sequence[structures.Player]:

    gkp_combinations = sorted(
        (
            (helpers.squad_price(c), helpers.squad_xP(c), c)
            for c in itertools.combinations((p for p in pool if p.position == "GKP"), 2)
        ),
        key=lambda x: x[0],
        reverse=True,
    )
    gkp_min_price = min(p.price for p in pool if p.position == "GKP")
    gkp_combinations = [
        c for c in gkp_combinations if any(p.price <= gkp_min_price for p in c[-1])
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
    def_min_price = min(p.price for p in pool if p.position == "DEF")
    def_combinations = [
        c for c in def_combinations if any(p.price <= def_min_price for p in c[-1])
    ]

    mid_combinations = sorted(
        (
            (helpers.squad_price(c), helpers.squad_xP(c), c)
            for c in itertools.combinations((p for p in pool if p.position == "MID"), 5)
            if constraints.team_constraint(c, 3)
        ),
        key=lambda x: x[1],
        reverse=True,
    )
    mid_min_price = min(p.price for p in pool if p.position == "MID")
    mid_combinations = [
        c for c in mid_combinations if any(p.price <= mid_min_price for p in c[-1])
    ]

    fwd_combinations = sorted(
        (
            (helpers.squad_price(c), helpers.squad_xP(c), c)
            for c in itertools.combinations((p for p in pool if p.position == "FWD"), 3)
        ),
        key=lambda x: x[0],
        reverse=True,
    )
    fwd_min_price = min(p.price for p in pool if p.position == "FWD")
    fwd_combinations = [
        c for c in fwd_combinations if any(p.price <= fwd_min_price for p in c[-1])
    ]

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

    best_squad = tuple[structures.Player, ...]()
    best_lxp = 0.0

    max_mid_price = max(price for price, _, _ in mid_combinations)
    min_mid_price = min(price for price, _, _ in mid_combinations)

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
                    # Sorted, no need to look deeper.
                    if gp + fp + dp + max_mid_price < budget_lower:
                        break
                    # To pricy, fast forward to cheeper
                    if gp + fp + dp + min_mid_price > budget_upper:
                        continue

                    for mp, mxp, m in mid_combinations:
                        # Sorted, no need to look deeper.
                        if gxp + fxp + dxp + mxp < best_lxp:
                            break

                        price = mp + dp + fp + gp

                        squad = g + f + d + m
                        if (
                            budget_lower <= price <= budget_upper
                            and gxp + fxp + dxp + mxp >= best_lxp
                            and constraints.team_constraint(squad, n=3)
                            and (bl := helpers.best_lineup(squad))
                            and (blxp := helpers.squad_xP(bl)) > best_lxp
                        ):
                            best_lxp = blxp
                            # assert gxp + fxp + dxp + mxp >= best_lxp, (gxp + fxp + dxp + mxp, best_lxp)
                            best_squad = squad
                            helpers.lprint(best_squad, [p.name for p in bl])
                            print("-->>", best_lxp)

    # NOTE: without candidates(...) (26316.53seconds) xP = 66.12268150503445
    # NOTE: with candidates(...), alpha=.9(600 seconds) xP = 65.64198652433947
    # assert best_lxp > 66.8
    return best_squad


if __name__ == "__main__":
    import fetch

    pool: list[structures.Player] = []

    best_xp = set()
    for _, z in itertools.groupby(sorted(fetch.players(), key=lambda x:x.position), key=lambda x: x.position):
        z = sorted(z, key=lambda x:x.xP())[-30:]
        for p in z:
            best_xp.add(p)

    shit = set()
    for _, z in itertools.groupby(sorted(fetch.players(), key=lambda x:x.position), key=lambda x: x.position):
        z = sorted(z, key=lambda x:x.xP())[:10]
        for p in z:
            shit.add(p)
    # best_value = set(sorted(fetch.players(), key=lambda x: x.xP()/x.price)[-n:])
    pool = best_xp.union(shit)
    pool = [p for p in pool if not p.news]
    # for _, players in itertools.groupby(
    #     sorted(
    #         (p for p in fetch.players() if not p.news and p.xP() > 0),
    #         key=lambda x: (x.position, round(x.price / x.xP(),1))
    #     ),
    #     key=lambda x:  (x.position, round(x.price / x.xP(),1)),
    # ):
    #     candidates = sorted(list(players), key=lambda x: x.xP())
    #     pool.extend(candidates[-n:])

    helpers.lprint(pool)
    squad = lineup(pool=pool)
    helpers.lprint(squad, best=[p.name for p in helpers.best_lineup(squad)])
    print("-->>", helpers.best_lineup_xP(squad))
