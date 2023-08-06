import argparse
import itertools
import typing as T

from tqdm.std import tqdm

import constraints
import fetch
import helpers
import structures


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
    max_len_out_team = max(len(p.team) for p in transfers_out)

    log.write("-" * 75)
    for o, i in zip(transfers_out, transfers_in):
        log.write(
            f"{o.position}: {o.webname:<{max_len_out_name}} {o.team:<{max_len_out_team}} {o.xP:<5.2f}"
            "  -->>  "
            f"{i.webname:<{max_len_in_name}} {i.team:<{max_len_in_team}} {i.xP:.2f}"
        )
    log.write(f"lxp gain: {(helpers.overall_xP(new) - helpers.overall_xP(old)):.2f}")


def transfer(
    current: T.List["structures.Player"],
    pool: T.List["structures.Player"],
    max_transfers: int,
    bar: tqdm,
):

    max_budget = helpers.squad_price(current)
    min_budget = max_budget * 0.9

    squad_base = dict[int, tuple[tuple[tuple[structures.Player, ...], int], ...]]()
    for n in range(1, max_transfers + 1):
        squad_base[n] = tuple(
            (c, helpers.squad_price(c))
            for c in sorted(
                itertools.combinations(current, len(current) - n),
                key=helpers.squad_price,
            )
        )

    transfer_in = dict[int, tuple[tuple[tuple[structures.Player, ...], int], ...]]()
    for n in range(1, max_transfers + 1):
        transfer_in[n] = tuple(
            (c, helpers.squad_price(c))
            for c in sorted(
                itertools.combinations(pool, n),
                key=helpers.squad_price,
            )
        )

    total = 0
    for n in range(1, max_transfers + 1):
        for _ in squad_base[n]:
            total += len(transfer_in[n])
    bar.total = total

    current_oxp = helpers.overall_xP(current)

    for n in range(1, max_transfers + 1):
        for base, base_cost in squad_base[n]:
            for t_in, t_in_cost in transfer_in[n]:
                cost = base_cost + t_in_cost
                if cost > max_budget:
                    break
                if cost < min_budget:
                    continue
                squad = base + t_in

                if (
                    helpers.overall_xP(squad) > current_oxp
                    and helpers.valid_squad(squad)
                    and len(set(squad)) == 15
                    and constraints.team_constraint(squad, 3)
                ):
                    yield squad
            bar.update(len(transfer_in[n]))


def main() -> None:

    parser = argparse.ArgumentParser(
        prog="Transfer picker.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--add", nargs="+", default=[])
    parser.add_argument("--max-transfers", type=int, required=True)
    parser.add_argument("--min-mtm", default=0.0, type=float)
    parser.add_argument("--min-xp", default=0.0, type=float)
    parser.add_argument("--remove", nargs="+", default=[])
    parser.add_argument("--top", type=int, default=0)

    args = parser.parse_args()

    pool = [
        p
        for p in fetch.players()
        if p.xP >= args.min_xp and p.mtm() >= args.min_mtm and not p.news
    ]
    pool = sorted(pool, key=lambda p: p.xP)
    pool = pool[-args.top :]
    print(">>> Pool")
    helpers.lprint(pool)

    print(">>>> Current team")
    team = list(fetch.my_team())
    helpers.lprint(team, best=[p.name for p in helpers.best_lineup(team)])

    add = set(p for p in fetch.players() if p.name in args.add or p.webname in args.add)
    assert len(add) == len(args.add), (add, args.add)

    remove = set(
        p for p in fetch.players() if p.name in args.remove or p.team in args.remove
    )

    oxp = helpers.overall_xP(team)

    with tqdm(
        bar_format="{percentage:3.0f}% | {bar:20} {r_bar}",
        unit_scale=True,
        unit_divisor=1_000,
        ascii=True,
    ) as bar:
        for new in sorted(
            (
                n
                for n in transfer(
                    current=team,
                    pool=list(set(pool + list(add))),
                    max_transfers=args.max_transfers,
                    bar=bar,
                )
                if (
                    (not add or all(a in n for a in add))
                    and (not remove or not any(r in n for r in remove))
                    and helpers.overall_xP(n) > oxp
                )
            ),
            key=helpers.overall_xP,
        )[-(args.top or 25) :]:
            display(team, new, bar)


if __name__ == "__main__":
    main()
