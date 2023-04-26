import argparse
import collections as C
import heapq
import itertools
import statistics
import typing as T

from tqdm.std import tqdm

import constraints
import fetch
import helpers
import structures


def position_combinations(
    pool: T.Sequence["structures.Player"],
    combinations: int,
) -> list[tuple[int, float, tuple["structures.Player", ...]]]:
    assert combinations > 0
    return sorted(
        (
            (helpers.squad_price(c), helpers.squad_xP(c), c)
            for c in itertools.combinations(pool, combinations)
        ),
        key=lambda x: (x[1], x[0]),
        reverse=True,
    )


def must_include(
    combinations: list[tuple[int, float, tuple["structures.Player", ...]]],
    include: T.Sequence["structures.Player"],
) -> list[tuple[int, float, tuple["structures.Player", ...]]]:
    return (
        [c for c in combinations if all(i in c[-1] for i in include)]
        if include
        else combinations
    )


def lineup(
    pool: T.Sequence["structures.Player"],
    budget_lower: int = 900,
    budget_upper: int = 1_000,
    include: T.Sequence["structures.Player"] = tuple(),
    n_squads: int = 1_000,
    max_players_per_team: int = 3,
) -> T.Sequence[T.Sequence["structures.Player"]]:

    gkp_combinations = must_include(
        position_combinations(
            pool=[p for p in pool if p.position == "GKP"],
            combinations=2,
        ),
        [p for p in include if p.position == "GKP"],
    )

    def_combinations = must_include(
        position_combinations(
            pool=[p for p in pool if p.position == "DEF"],
            combinations=5,
        ),
        [p for p in include if p.position == "DEF"],
    )

    mid_combinations = must_include(
        position_combinations(
            pool=[p for p in pool if p.position == "MID"],
            combinations=5,
        ),
        [p for p in include if p.position == "MID"],
    )

    fwd_combinations = must_include(
        position_combinations(
            pool=[p for p in pool if p.position == "FWD"],
            combinations=3,
        ),
        [p for p in include if p.position == "FWD"],
    )

    # All combinations sorted from higest -> lowest xP.

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

    best_squads = list[tuple[tuple[float, int], tuple[structures.Player, ...]]]()
    best_squad_xp = 0.0

    max_mid_price = max(price for price, _, _ in mid_combinations)
    min_mid_price = min(price for price, _, _ in mid_combinations)
    max_mid_xp = max(xp for _, xp, _ in mid_combinations)

    max_def_price = max(price for price, _, _ in def_combinations)
    min_def_price = min(price for price, _, _ in def_combinations)
    max_def_xp = max(xp for _, xp, _ in def_combinations)

    alpha = 1.1
    sequence: int = 0

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

                if gxp + fxp + max_def_xp + max_mid_xp < best_squad_xp:
                    continue

                if gp + fp + min_def_price + min_mid_price > budget_upper:
                    continue

                if gp + fp + max_def_price + max_mid_price < budget_upper:
                    continue

                if (
                    max(C.Counter(p.team for p in g + f).values())
                    > max_players_per_team
                ):
                    continue

                for dp, dxp, d in def_combinations:

                    if gxp + fxp + dxp + max_mid_xp < best_squad_xp:
                        break

                    if gp + fp + dp + min_mid_price > budget_upper:
                        continue

                    if gp + fp + dp + max_mid_price < budget_lower:
                        continue

                    if (
                        max(C.Counter(p.team for p in g + f + d).values())
                        > max_players_per_team
                    ):
                        continue

                    for mp, mxp, m in mid_combinations:

                        if gxp + fxp + dxp + mxp < best_squad_xp:
                            break

                        if (
                            budget_lower <= mp + dp + fp + gp <= budget_upper
                            and constraints.team_constraint(
                                squad := g + f + d + m, n=max_players_per_team
                            )
                            and (oxp := helpers.overall_xP(squad)) > best_squad_xp
                        ):
                            sequence += 1
                            if len(best_squads) >= n_squads:
                                heapq.heappushpop(
                                    best_squads, ((oxp, sequence), squad)
                                )
                                best_squad_xp = (
                                    statistics.mean(v for (v, *_), _ in best_squads)
                                    * alpha
                                )
                            else:
                                heapq.heappush(
                                    best_squads, ((oxp, sequence), squad)
                                )

    return sorted((s for _, s in best_squads), key=helpers.overall_xP)


def position_price_candidates(
    pool: T.Sequence["structures.Player"],
    topn: int = 5,
) -> T.Sequence["structures.Player"]:

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

    parser.add_argument(
        "--budget-lower",
        type=int,
        default=900,
        help="(default: %(default)s)",
    )
    parser.add_argument(
        "--budget-upper",
        type=int,
        default=1_000,
        help="(default: %(default)s)",
    )
    parser.add_argument(
        "--gkp-def-not-same-team",
        action="store_true",
        help="(default: %(default)s)",
    )
    parser.add_argument(
        "--include",
        nargs="+",
        default=[],
        help="(default: %(default)s)",
    )
    parser.add_argument(
        "--keep-squad",
        type=int,
        default=100,
        help="(default: %(default)s)",
    )
    parser.add_argument(
        "--max-def-per-team",
        type=int,
        default=3,
        help="(default: %(default)s)",
    )
    parser.add_argument(
        "--min-mtm",
        type=float,
        default=0.0,
        help="(default: %(default)s)",
    )
    parser.add_argument(
        "--min-xp",
        type=float,
        default=0.0,
        help="(default: %(default)s)",
    )
    parser.add_argument(
        "--no-news",
        action="store_true",
        help="(default: %(default)s)",
    )
    parser.add_argument(
        "--remove",
        nargs="+",
        default=[],
        help="(default: %(default)s)",
    )
    parser.add_argument(
        "--top-position-price",
        type=int,
        default=0,
        help="(default: %(default)s)",
    )

    args = parser.parse_args()

    pool = [p for p in fetch.players() if p.mtm >= args.min_mtm and p.xP >= args.min_xp]

    if args.no_news:
        pool = [p for p in pool if not p.news]

    remove: set[str] = set(r.lower() for r in args.remove)
    pool = [p for p in pool if p.webname.lower() not in remove]

    if args.top_position_price:
        pool = list(
            position_price_candidates(
                pool=pool,
                topn=args.top_position_price,
            )
        )

    include = list(
        set(
            p
            for p in fetch.players()
            if p.webname in args.include
            or p.name in args.include
            or p.team in args.include
        )
    )
    pool += include

    # Just in case
    pool = list(set(pool))

    helpers.lprint(pool)
    squads = lineup(
        pool=pool,
        budget_lower=args.budget_lower,
        budget_upper=args.budget_upper,
        include=include,
        n_squads=args.keep_squad,
    )

    if args.gkp_def_not_same_team:
        squads = [s for s in squads if constraints.gkp_def_same_team(s)]

    if args.max_def_per_team:
        squads = [
            s
            for s in squads
            if max(C.Counter(p.team for p in s if p.position == "DEF").values())
            <= args.max_def_per_team
        ]

    for squad in squads:
        helpers.lprint(squad, best=[p.name for p in helpers.best_lineup(squad)])
        print(
            f"lxp: {helpers.best_lineup_xP(squad):.2f} "
            + f"gxp: {helpers.squad_xP(squad):.2f} "
            + f"oxp: {helpers.overall_xP(squad):.2f}\n"
        )


if __name__ == "__main__":
    main()
