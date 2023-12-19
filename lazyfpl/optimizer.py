import argparse
import collections
import heapq
import itertools
import typing as T

from lazyfpl import constraints, fetch, structures, helpers
from tqdm.std import tqdm


def position_combinations(
    pool: list["structures.Player"],
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
    include: list["structures.Player"],
) -> list[tuple[int, float, tuple["structures.Player", ...]]]:
    return (
        [c for c in combinations if all(i in c[-1] for i in include)]
        if include
        else combinations
    )


def lineup(
    pool: list["structures.Player"],
    budget_lower: int = 900,
    budget_upper: int = 1_000,
    include: T.Sequence["structures.Player"] = (),
    n_squads: int = 100_000,
    max_players_per_team: int = 3,
    alpha: float = 0.8,
) -> list[structures.Squad]:
    assert 0 <= alpha <= 1.0

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

    best_squads = list[tuple[tuple[float, float, int], tuple[structures.Player, ...]]]()
    best_squad_xp = (
        sum(
            (
                helpers.squad_xP(fwd_combinations[0][-1]),
                helpers.squad_xP(mid_combinations[0][-1]),
                helpers.squad_xP(def_combinations[0][-1]),
                helpers.squad_xP(gkp_combinations[0][-1]),
            )
        )
        * alpha
    )

    max_mid_price = max(price for price, _, _ in mid_combinations)
    min_mid_price = min(price for price, _, _ in mid_combinations)
    max_mid_xp = max(xp for _, xp, _ in mid_combinations)

    max_def_price = max(price for price, _, _ in def_combinations)
    min_def_price = min(price for price, _, _ in def_combinations)
    max_def_xp = max(xp for _, xp, _ in def_combinations)

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
                    # Could use break, but messes up tqdm.
                    continue

                if gp + fp + min_def_price + min_mid_price > budget_upper:
                    continue

                if gp + fp + max_def_price + max_mid_price < budget_lower:
                    continue

                if (
                    max(collections.Counter(p.team for p in g + f).values())
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
                        max(collections.Counter(p.team for p in g + f + d).values())
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
                                    best_squads,
                                    (
                                        (round(oxp), mp + dp + fp + gp, sequence),
                                        squad,
                                    ),
                                )
                                best_squad_xp = max(
                                    max(v for (_, v, _), _ in best_squads) * alpha,
                                    best_squad_xp,
                                )
                            else:
                                heapq.heappush(
                                    best_squads,
                                    (
                                        (round(oxp), mp + dp + fp + gp, sequence),
                                        squad,
                                    ),
                                )

    return [
        structures.Squad(heapq.heappop(best_squads)[-1])
        for _ in range(len(best_squads))
    ]


def position_price_candidates(
    pool: list["structures.Player"],
    topn: int,
) -> T.Iterator["structures.Player"]:
    for _, players in itertools.groupby(
        sorted(pool, key=lambda x: (x.position, x.price)),
        key=lambda x: (x.position, x.price),
    ):
        toadd = []
        team = set[str]()
        for player in sorted(players, key=lambda x: x.xP or 0, reverse=True):
            if player.team not in team:
                toadd.append(player)
                team.add(player.team)
        yield from toadd[:topn]


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
        default=100_000,
        help="(default: %(default)s)",
    )
    parser.add_argument(
        "--max-def-per-team",
        type=int,
        default=3,
        help="(default: %(default)s)",
    )
    parser.add_argument(
        "--max-players-per-team",
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

    pool = [p for p in fetch.players() if p.xP is not None]
    pool = [p for p in pool if p.mtm() >= args.min_mtm and p.xP >= args.min_xp]

    if args.no_news:
        pool = [p for p in pool if not p.news]

    player_names = {p.webname.lower() for p in pool}
    remove: set[str] = {r.lower() for r in args.remove if r.lower() in player_names}
    pool = [p for p in pool if p.webname.lower() not in remove]

    team_names = {p.team.lower() for p in pool}
    remove_team: set[str] = {r.lower() for r in args.remove if r.lower() in team_names}
    pool = [p for p in pool if p.team.lower() not in remove_team]

    if args.top_position_price:
        pool = list(
            set(
                position_price_candidates(
                    pool=pool,
                    topn=args.top_position_price,
                )
            )
        )

    include = list(
        {
            p
            for p in fetch.players()
            if p.webname in args.include
            or p.name in args.include
            or p.team in args.include
        }
    )
    pool += include

    # Just in case
    pool = list(set(pool))

    print(structures.Squad(pool))
    squads = lineup(
        pool=pool,
        budget_lower=args.budget_lower,
        budget_upper=args.budget_upper,
        include=include,
        max_players_per_team=args.max_players_per_team,
        n_squads=args.keep_squad,
    )

    if args.gkp_def_not_same_team:
        squads = [s for s in squads if constraints.gkp_def_same_team(s.players)]

    if args.max_def_per_team:
        squads = [
            s
            for s in squads
            if max(
                collections.Counter(p.team for p in s if p.position == "DEF").values()
            )
            <= args.max_def_per_team
        ]

    for player, cnt in collections.Counter(
        p for squad in squads for p in squad.players
    ).items():
        print(player, round(cnt / len(squads) * 100, 2))

    print("\n\n".join(str(s) for s in squads[-10:]))

    mincxp = min(s.CxP() for s in squads)
    maxxcp = max(s.CxP() for s in squads)
    minss = min(s.sscore() for s in squads)
    maxss = max(s.sscore() for s in squads)
    mints = min(s.tsscore() for s in squads)
    maxts = max(s.tsscore() for s in squads)

    print("")
    print(
        f"Min CxP: {mincxp:.1f}",
        f"Max CxP: {maxxcp:.1f}",
        f"Max-Min CxP: {(maxxcp-mincxp):.1f}",
    )
    print(
        f"Min ss: {minss:d}",
        f"Max ss: {maxss:d}",
        f"Max-Min ss: {(maxss-minss):d}",
    )
    print(
        f"Min ts: {mints:.2f}",
        f"Max ts: {maxts:.2f}",
        f"Max-Min ts: {(maxts-mints):.2f}",
    )


if __name__ == "__main__":
    main()
