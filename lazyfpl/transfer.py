import argparse
import heapq
import itertools
import typing as T

from tqdm.std import tqdm
from lazyfpl import constraints, fetch, helpers, structures


def display(
    old: T.Sequence["structures.Player"],
    new: T.Sequence["structures.Player"],
    log: tqdm,
) -> None:
    transfers_in = sorted((p for p in new if p not in old), key=lambda x: x.position)
    transfers_out = sorted((p for p in old if p not in new), key=lambda x: x.position)

    max_len_in_name = max(len(p.webname) for p in transfers_in)
    max_len_in_team = max(len(p.team) for p in transfers_in)

    max_len_out_name = max(len(p.webname) for p in transfers_out)
    # max_len_out_team = max(len(p.team) for p in transfers_out)

    log.write("-" * 75)
    for o, i in zip(transfers_out, transfers_in):
        log.write(
            f"{o.position}: {o.webname:<{max_len_out_name}} "
            "{o.team:<{max_len_out_team}} {o.xP:<5.1f}"
            "  -->>  "
            f"{i.webname:<{max_len_in_name}} {i.team:<{max_len_in_team}} {i.xP:.1f}"
        )
    log.write(f"OxP gain: {(helpers.overall_xP(new) - helpers.overall_xP(old)):.1f}")
    log.write(f"TS  gain: {(helpers.tsscore(new) - helpers.tsscore(old)):.1f}")


def transfer(
    current: T.Sequence["structures.Player"],
    pool: T.Sequence["structures.Player"],
    remove: T.Sequence["structures.Player"],
    add: T.Sequence["structures.Player"],
    max_transfers: int,
    max_candidates: int,
    bar: tqdm,
):
    max_budget = helpers.squad_price(current)
    min_budget = max_budget * 0.8
    candidates = list[tuple[tuple[float, float, int], tuple[structures.Player, ...]]]()

    squad_base = {
        n: tuple(
            (c, helpers.squad_price(c))
            for c in sorted(
                itertools.combinations(current, len(current) - n),
                key=helpers.squad_price,
            )
        )
        for n in range(1, max_transfers + 1)
    }
    squad_base = {
        n: tuple(
            (players, cost)
            for players, cost in squad_cost
            if all(r not in players for r in remove)
        )
        for n, squad_cost in squad_base.items()
    }

    transfer_in = {
        n: tuple(
            (c, helpers.squad_price(c))
            for c in sorted(
                itertools.combinations(pool, n),
                key=helpers.squad_price,
            )
        )
        for n in range(1, max_transfers + 1)
    }
    transfer_in = {
        n: tuple(
            (players, cost)
            for players, cost in squad_cost
            if all(a in players for a in add)
        )
        for n, squad_cost in transfer_in.items()
    }

    min_max_tranfer_in = {
        n: (
            min(c for _, c in transfer_in[n]),
            max(c for _, c in transfer_in[n]),
        )
        for n in transfer_in
    }

    bar.total = sum(
        len(transfer_in[n]) * len(squad_base[n]) for n in range(1, max_transfers + 1)
    )

    sequence: int = 0

    for n in range(1, max_transfers + 1):
        for base, base_cost in squad_base[n]:
            min_c, max_c = min_max_tranfer_in[n]
            assert min_c <= max_c
            if max_c + base_cost < min_budget:
                bar.update(len(transfer_in[n]))
                continue
            if min_c + base_cost > max_budget:
                bar.update(len(transfer_in[n]))
                continue

            for t_in, t_in_cost in transfer_in[n]:
                cost = base_cost + t_in_cost
                if cost > max_budget:
                    break
                if cost < min_budget:
                    continue

                squad = base + t_in

                if add and all(a not in squad for a in add):
                    continue

                if (
                    helpers.valid_squad(squad)
                    and constraints.team_constraint(squad, 3)
                    and len(set(squad)) == 15
                ):
                    oxp = round(helpers.overall_xP(squad), 1)
                    inv = round(1 / (1 + helpers.tsscore(squad)), 3)
                    sequence += 1
                    if len(candidates) >= max_candidates:
                        heapq.heappushpop(
                            candidates,
                            (
                                (inv, oxp, sequence),
                                squad,
                            ),
                        )
                    else:
                        heapq.heappush(
                            candidates,
                            (
                                (inv, oxp, sequence),
                                squad,
                            ),
                        )

            bar.update(len(transfer_in[n]))

    return [
        structures.Squad(heapq.heappop(candidates)[-1]) for _ in range(len(candidates))
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="Transfer picker.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--add",
        nargs="+",
        default=[],
        help="(default: %(default)s)",
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        default=[],
        help="(default: %(default)s)",
    )
    parser.add_argument(
        "--max-candidates",
        default=100,
        type=int,
        help="(default: %(default)s)",
    )
    parser.add_argument(
        "--max-transfers",
        type=int,
        required=True,
        help="(default: %(default)s)",
    )
    parser.add_argument(
        "--min-mtm",
        default=0.0,
        type=float,
        help="(default: %(default)s)",
    )
    parser.add_argument(
        "--min-xp",
        default=0.0,
        type=float,
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

    args = parser.parse_args()

    pool = [p for p in fetch.players() if p.xP is not None]

    if args.exclude:
        pool = [p for p in pool if p.webname not in args.exclude]
        pool = [p for p in pool if p.team not in args.exclude]

    if args.min_xp > 0:
        pool = [p for p in pool if p.xP >= args.min_xp]

    if args.min_mtm > 0:
        pool = [p for p in pool if p.mtm() >= args.min_mtm]

    if args.no_news:
        pool = [p for p in pool if not p.news]

    pool = sorted(pool, key=lambda p: p.xP or 0)
    print(">>> Pool")
    print(structures.Squad(pool))

    print("\n>>>> Current team")
    team = fetch.my_team()
    print(team)

    with tqdm(
        bar_format="{percentage:3.0f}% | {bar:20} {r_bar}",
        unit_scale=True,
        unit_divisor=1_000,
        ascii=True,
    ) as bar:
        for new_squad in transfer(
            current=team.players,
            pool=pool,
            max_transfers=args.max_transfers,
            max_candidates=args.max_candidates,
            bar=bar,
            remove=[
                p
                for p in team.players
                if p.webname in args.remove or p.team in args.remove
            ]
            + [p for p in team.players if args.no_news and p.news],
            add=[p for p in pool if p.webname in args.add or p.team in args.add],
        ):
            display(team.players, new_squad, bar)


if __name__ == "__main__":
    main()
