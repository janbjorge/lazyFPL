import itertools
import typing as T

from tqdm import (
    tqdm,
)

import constraints
import helpers
import structures


def candidates(
    combinations: T.Sequence[tuple[int, float, tuple[structures.Player, ...]]],
    lower_budget: int,
    upper_budget: int,
    min_xp: float,
    caller: str,
) -> T.Sequence[tuple[int, float, tuple[structures.Player, ...]]]:
    xp_candidates = set[tuple[int, float, tuple[structures.Player, ...]]]()
    price_candidates = set[tuple[int, float, tuple[structures.Player, ...]]]()
    for price, xP, c in combinations:
        if xP >= min_xp:
            xp_candidates.add((price, xP, c))
        if lower_budget <= price <= upper_budget:
            price_candidates.add((price, xP, c))
    rv = sorted(
        xp_candidates.intersection(price_candidates),
        key=lambda x: x[1],
    )
    if caller:
        print(caller, len(combinations), len(rv), len(rv)/len(combinations))
    return rv


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
        key=lambda x: x[1],
    )

    def_combinations = sorted(
        (
            (helpers.squad_price(c), helpers.squad_xP(c), c)
            for c in itertools.combinations((p for p in pool if p.position == "DEF"), 5)
            if constraints.team_constraint(c, 3)
        ),
        key=lambda x: x[1],
    )

    mid_combinations = sorted(
        (
            (helpers.squad_price(c), helpers.squad_xP(c), c)
            for c in itertools.combinations((p for p in pool if p.position == "MID"), 5)
            if constraints.team_constraint(c, 3)
        ),
        key=lambda x: x[1],
    )

    fwd_combinations = sorted(
        (
            (helpers.squad_price(c), helpers.squad_xP(c), c)
            for c in itertools.combinations((p for p in pool if p.position == "FWD"), 3)
        ),
        key=lambda x: x[1],
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

    best_squad = tuple[structures.Player, ...]()
    best_lxp = 0.0

    max_def_price = max(price for price, _, _ in def_combinations)
    min_def_price = min(price for price, _, _ in def_combinations)
    min_def_xp = min(xp for _, xp, _ in def_combinations)

    max_mid_price = max(price for price, _, _ in mid_combinations)
    min_mid_price = min(price for price, _, _ in mid_combinations)
    min_mid_xp = min(xp for _, xp, _ in mid_combinations)

    import statistics
    fwd_leeway = statistics.stdev((xp for _, xp, _ in fwd_combinations)) * 1/2
    mid_leeway = statistics.stdev((xp for _, xp, _ in mid_combinations)) * 1/2
    def_leeway = statistics.stdev((xp for _, xp, _ in def_combinations)) * 1/2

    with tqdm(
        total=total,
        bar_format="{percentage:3.0f}% | {bar:20} {r_bar}",
        unit_scale=True,
        unit_divisor=1_000,
        ascii=True,
    ) as bar:
        for gp, gxp, g in gkp_combinations:
            for fp, fxp, f in fwd_combinations:
                for dp, dxp, d in candidates(
                    combinations=def_combinations,
                    lower_budget=budget_lower - (gp + fp + max_mid_price),
                    upper_budget=budget_upper - (gp + fp + min_mid_price),
                    min_xp=0,
                    caller="def_combinations",
                ):
                    for mp, mxp, m in candidates(
                        combinations=mid_combinations,
                        lower_budget=budget_lower - (gp + fp + dp),
                        upper_budget=budget_upper - (gp + fp + dp),
                        min_xp=best_lxp - (gxp + fxp + dxp) - mid_leeway,
                        caller="mid_combinations",
                    ):
                        squad = g + f + d + m
                        if (
                            constraints.team_constraint(squad, n=3)
                            and budget_lower <= gp + fp + dp + mp <= budget_upper
                            and (bl := helpers.best_lineup(squad))
                            and (blxp := helpers.squad_xP(bl)) > best_lxp
                        ):
                            best_lxp = blxp
                            assert gxp + fxp + dxp + mxp >= best_lxp
                            best_squad = squad
                            helpers.lprint(best_squad, [p.name for p in bl])
                            # 63.73304186539482 9.373986486486487 11.105067567567568 21.551785714285717 25.146803315920966
                            print("-->>", best_lxp)
                bar.update(len(def_combinations) * len(mid_combinations))

    return best_squad


if __name__ == "__main__":
    import sys
    import fetch

    n = 3 if len(sys.argv) == 1 else int(sys.argv[1])

    # Top 3 players per position and price
    pool: list[structures.Player] = []
    for _, y in itertools.groupby(
        sorted(
            (p for p in fetch.players() if not p.news and p.xP() > 0),
            key=lambda x: (x.position, x.price),
        ),
        key=lambda x: (x.position, x.price),
    ):
        pool.extend(sorted(list(y), key=lambda x: x.xP())[-n:])

    helpers.lprint(pool)
    squad = lineup(pool=pool)
    helpers.lprint(squad, best=[p.name for p in helpers.best_lineup(squad)])
    print("-->>", helpers.best_lineup_xP(squad))
