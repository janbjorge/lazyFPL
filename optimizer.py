import argparse
import collections as C
import itertools
import math
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
    budget_lower: int = 900,
    budget_upper: int = 1_000,
    gxp_lxp_ratio: float = 1.05,
    include: T.Sequence[structures.Player] = tuple(),
) -> T.Sequence[structures.Player]:

    assert gxp_lxp_ratio >= 1

    gkp_combinations = sorted(
        (
            (helpers.squad_price(c), helpers.squad_xP(c), c)
            for c in itertools.combinations((p for p in pool if p.position == "GKP"), 2)
        ),
        key=lambda x: x[1],
        reverse=True,
    )
    if include_gkps := [p for p in include if p.position == "GKP"]:
        gkp_combinations = [
            c for c in gkp_combinations if any(p in include_gkps for p in c[-1])
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
    if include_defs := [p for p in include if p.position == "DEF"]:
        def_combinations = [
            c for c in def_combinations if any(p in include_defs for p in c[-1])
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
    if include_mids := [p for p in include if p.position == "MID"]:
        mid_combinations = [
            c for c in mid_combinations if any(p in include_mids for p in c[-1])
        ]

    fwd_combinations = sorted(
        (
            (helpers.squad_price(c), helpers.squad_xP(c), c)
            for c in itertools.combinations((p for p in pool if p.position == "FWD"), 3)
        ),
        key=lambda x: x[1],
        reverse=True,
    )
    if include_fwds := [p for p in include if p.position == "FWD"]:
        fwd_combinations = [
            c for c in fwd_combinations if any(p in include_fwds for p in c[-1])
        ]

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
    max_gxp = sum(
        (
            max(xp for _, xp, _ in gkp_combinations),
            max(xp for _, xp, _ in def_combinations),
            max(xp for _, xp, _ in mid_combinations),
            max(xp for _, xp, _ in fwd_combinations),
        )
    )
    best_lxp = max_gxp / gxp_lxp_ratio

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
        while (
            not best_squad
            and not math.isclose(best_lxp, 0.0, abs_tol=0.1)
            and not math.isclose(max_gxp, 0.0, abs_tol=0.1)
        ):

            best_lxp *= 0.95
            max_gxp *= 0.95

            bar.clear()
            bar.reset()
            bar.write(f"best_lxp={best_lxp:.2f}, min_gxp={max_gxp:.2f}")

            for gp, gxp, g in gkp_combinations:
                for fp, fxp, f in fwd_combinations:
                    bar.update(len(def_combinations) * len(mid_combinations))

                    if gxp + fxp + max_def_xp + max_mid_xp < max_gxp:
                        continue

                    if max(C.Counter(p.team for p in g + f).values()) > 3:
                        continue

                    for dp, dxp, d in def_combinations:

                        if gxp + fxp + dxp + max_mid_xp < max_gxp:
                            break

                        if gp + fp + dp + max_mid_price < budget_lower:
                            continue

                        if gp + fp + dp + min_mid_price > budget_upper:
                            continue

                        if max(C.Counter(p.team for p in g + f + d).values()) > 3:
                            continue

                        if constraints.gkp_def_same_team(g + d):
                            continue

                        # One defender per team
                        if max(C.Counter(p.team for p in d).values()) > 1:
                            continue

                        for mp, mxp, m in mid_combinations:

                            if gxp + fxp + dxp + mxp < max_gxp:
                                break

                            if (
                                budget_lower <= mp + dp + fp + gp <= budget_upper
                                and gxp + fxp + dxp + mxp >= best_lxp
                                and constraints.team_constraint(
                                    squad := g + f + d + m, n=3
                                )
                                and (bl := helpers.best_lineup(squad))
                                and (blxp := helpers.squad_xP(bl)) > best_lxp
                                and (blxp + gxp + fxp + dxp + mxp) / 2.0 > best_lxp
                            ):
                                best_lxp = (blxp + gxp + fxp + dxp + mxp) / 2.0
                                best_squad = squad
                                max_gxp = best_lxp * gxp_lxp_ratio
                                assert max_gxp >= best_lxp
                                helpers.lprint(best_squad, [p.name for p in bl])
                                print(
                                    f"-->> lxp={best_lxp:.2f}, gxp={gxp + fxp + dxp + mxp:.2f}, min_gxp={max_gxp:.2f}"
                                )

    return best_squad


def position_price_candidates(
    pool: T.Sequence[structures.Player],
    topn: int = 5,
) -> T.Sequence[structures.Player]:

    new: list[structures.Player] = []

    for _, players in itertools.groupby(
        sorted(pool, key=lambda x: (x.position, x.price)),
        key=lambda x: (x.position, x.price),
    ):
        candidates = sorted(list(players), key=lambda x: x.xP, reverse=True)
        new.extend(candidates[:topn])

    # Just in case.
    return list(set(new))


def main():
    parser = argparse.ArgumentParser(
        prog="Lineup optimizer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--budget-lower", type=int, default=900)
    parser.add_argument("--budget-upper", type=int, default=1_000)
    parser.add_argument("--gxp-lxp-ratio", type=float, default=1.1)
    parser.add_argument("--include", nargs="+", default=[])
    parser.add_argument("--min-mtm", type=float, default=0.0)
    parser.add_argument("--min-xp", type=float, default=0.0)
    parser.add_argument("--remove", nargs="+", default=[])
    parser.add_argument("--top-position-price", type=int, default=0)

    args = parser.parse_args()

    pool = [
        p
        for p in fetch.players()
        if p.mtm >= args.min_mtm and p.xP >= args.min_xp and not p.news
    ]

    remove = set(r.lower() for r in args.remove)
    pool = [p for p in pool if p.webname.lower() not in remove]

    if args.top_position_price:
        pool = position_price_candidates(
            pool=pool,
            topn=args.top_position_price,
        )

    include = tuple(
        set(
            p
            for p in fetch.players()
            if p.webname in args.include or p.name in args.include
        )
    )
    assert len(include) == len(args.include), (include, args.include)
    pool.extend([p for p in pool if p.name in include])

    # Just in case
    pool = list(set(pool))

    helpers.lprint(pool)
    squad = lineup(
        pool=pool,
        budget_lower=args.budget_lower,
        budget_upper=args.budget_upper,
        gxp_lxp_ratio=args.gxp_lxp_ratio,
        include=include,
    )

    helpers.lprint(squad, best=[p.name for p in helpers.best_lineup(squad)])
    print("-->>", helpers.best_lineup_xP(squad))


if __name__ == "__main__":
    main()
