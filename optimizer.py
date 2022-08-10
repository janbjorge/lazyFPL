import argparse
import itertools
import typing as T

from tqdm import (
    tqdm,
)

import constraints
import fetch
import helpers
import structures


def lineup(
    pool: T.Sequence[structures.Player],
    budget_lower: int = 950,
    budget_upper: int = 1_000,
    min_xp_gkp_combination: float = 0.0,
    min_xp_def_combination: float = 20.0,
    min_xp_mid_combination: float = 20.0,
    min_xp_fwd_combination: float = 0.0,
    min_lxp: float = 100.0,
    min_gxp_lxp_ratio: float = 1.05,
) -> T.Sequence[structures.Player]:

    assert min_gxp_lxp_ratio > 1
    min_gxp = min_lxp * min_gxp_lxp_ratio

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
        key=lambda x: x[1],
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
    best_lxp = min_lxp

    max_mid_price = max(price for price, _, _ in mid_combinations)
    min_mid_price = min(price for price, _, _ in mid_combinations)
    max_mid_xp = max(xp for _, xp, _ in mid_combinations)

    max_def_xp = max(xp for _, xp, _ in def_combinations)

    with tqdm(
        total=total,
        bar_format="{percentage:3.0f}% | {bar:20} {r_bar}",
        unit_scale=True,
        unit_divisor=1_000,
        ascii=True,
    ) as bar:
        while not best_squad:
            bar.clear()
            for gp, gxp, g in gkp_combinations:
                for fp, fxp, f in fwd_combinations:
                    bar.update(len(def_combinations) * len(mid_combinations))

                    if gxp + fxp + max_def_xp + max_mid_xp < min_gxp:
                        continue

                    for dp, dxp, d in def_combinations:

                        if gxp + fxp + dxp + max_mid_xp < min_gxp:
                            break

                        if gp + fp + dp + max_mid_price < budget_lower:
                            continue

                        if gp + fp + dp + min_mid_price > budget_upper:
                            continue

                        if not constraints.team_constraint(g + f + d, n=4):
                            continue

                        for mp, mxp, m in mid_combinations:

                            if gxp + fxp + dxp + mxp < min_gxp:
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
                                min_gxp = best_lxp * min_gxp_lxp_ratio
                                assert min_gxp > best_lxp
                                helpers.lprint(best_squad, [p.name for p in bl])
                                print(
                                    f"-->> lxp={best_lxp:.2f}, gxp={gxp + fxp + dxp + mxp:.2f}, min_gxp={min_gxp:.2f}"
                                )
        best_lxp *= .95
        min_gxp *= .95

    return best_squad


def position_price_candidates(topn: int = 5) -> T.Sequence[structures.Player]:

    pool: list[structures.Player] = []

    for _, players in itertools.groupby(
        sorted(
            (p for p in fetch.players() if not p.news),
            key=lambda x: (x.position, x.price),
        ),
        key=lambda x: (x.position, x.price),
    ):
        candidates = sorted(list(players), key=lambda x: x.xP, reverse=True)
        pool.extend(candidates[:topn])

    # Just in case.
    return list(set(pool))


def main():
    parser = argparse.ArgumentParser(
        prog="Lineup optimizer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--budget_lower", type=int, default=950)
    parser.add_argument("--budget_upper", type=int, default=1_000)

    parser.add_argument("--min_xp_gkp_combination", type=float, default=0.0)
    parser.add_argument("--min_xp_def_combination", type=float, default=20.0)
    parser.add_argument("--min_xp_mid_combination", type=float, default=20.0)
    parser.add_argument("--min_xp_fwd_combination", type=float, default=0.0)

    parser.add_argument("--min_lxp", type=float, default=60.0)
    parser.add_argument("--min_gxp_lxp_ratio", type=float, default=1.1)

    parser.add_argument("--top_position_price_candidates", type=int, default=5)

    parser.add_argument("--remove", nargs="+", default=[])
    parser.add_argument("--include", nargs="+", default=[])

    args = parser.parse_args()

    pool = position_price_candidates(topn=args.top_position_price_candidates)

    remove = set(r.lower() for r in args.remove)
    pool = [p for p in pool if p.webname.lower() not in remove]

    include = set(i.lower() for i in args.include)
    pool.extend([p for p in pool if p.name in include])

    # Just in case
    pool = list(set(pool))

    helpers.lprint(pool)
    squad = lineup(
        pool=pool,
        budget_lower=args.budget_lower,
        budget_upper=args.budget_upper,
        min_xp_gkp_combination=args.min_xp_gkp_combination,
        min_xp_def_combination=args.min_xp_def_combination,
        min_xp_fwd_combination=args.min_xp_fwd_combination,
        min_xp_mid_combination=args.min_xp_mid_combination,
        min_lxp=args.min_lxp,
        min_gxp_lxp_ratio=args.min_gxp_lxp_ratio,
    )

    helpers.lprint(squad, best=[p.name for p in helpers.best_lineup(squad)])
    print("-->>", helpers.best_lineup_xP(squad))


if __name__ == "__main__":
    main()
