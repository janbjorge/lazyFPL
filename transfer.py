import typing as T
import argparse

from tqdm import tqdm

import constraints
import fetch
import helpers
import structures


def transfer(
    current: T.List[structures.Player],
    best: T.List[structures.Player],
    best_lxp: float,
    pool: T.List[structures.Player],
    budget: int,
    done_transfers: int,
    max_transfers: int,
    remove: set[structures.Player],
    add: set[structures.Player],
) -> T.List[structures.Player]:

    if (
        done_transfers == max_transfers
        and helpers.squad_price(current) <= budget
        and constraints.team_constraint(current, n=3)
        and helpers.best_lineup_xP(current) > best_lxp
    ):
        if remove and any(r in current for r in remove):
            return []
        if add and not all(a in current for a in add):
            return []
        print("-" * 100)
        helpers.lprint(current)
        return current
    elif done_transfers >= max_transfers:
        return []

    pool = [p for p in pool if p not in current]

    if done_transfers == 0:
        _pool = tqdm(
            pool,
            bar_format="{percentage:3.0f}% | {bar:20} {r_bar}",
            unit_scale=True,
            unit_divisor=1_000,
            ascii=True,
        )
    else:
        _pool = pool

    for t_in in _pool:
        for idx, _ in enumerate(current):

            t_out = current[idx]

            if t_in.position != t_out.position:
                continue

            tmp = current.copy()
            tmp[idx] = t_in

            best = (
                transfer(
                    current=tmp,
                    best=best,
                    best_lxp=helpers.best_lineup_xP(best),
                    pool=pool,
                    budget=budget,
                    done_transfers=done_transfers + 1,
                    max_transfers=max_transfers,
                    remove=remove,
                    add=add,
                )
                or best
            )

    return best


def main() -> None:

    parser = argparse.ArgumentParser(
        prog="Transfer optimizer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--max_transfers", "-m", type=int, required=True)
    parser.add_argument("--topn", "-t", type=int, required=True)
    parser.add_argument("--remove", nargs="+", default=[])
    parser.add_argument("--add", nargs="+", default=[])

    args = parser.parse_args()

    pool = sorted(fetch.players(), key=lambda x: x.xP, reverse=True)[: args.topn]
    print(">>> Pool")
    helpers.lprint(pool)

    print("\n>>>> Current team")
    team = list(fetch.my_team())
    helpers.lprint(team, best=[p.name for p in helpers.best_lineup(team)])

    remove = set(
        p for p in fetch.players() if p.name in args.remove or p.webname in args.remove
    )
    assert len(remove) == len(args.remove), (remove, args.remove)
    add = set(p for p in fetch.players() if p.name in args.add or p.webname in args.add)
    assert len(add) == len(args.add), (add, args.add)

    best = transfer(
        current=team,
        best=team,
        best_lxp=helpers.best_lineup_xP(team),
        pool=list(set(pool + list(add))),
        budget=helpers.squad_price(team),
        done_transfers=0,
        max_transfers=args.max_transfers,
        remove=remove,
        add=add,
    )

    transfers_in = sorted((p for p in best if p not in team), key=lambda x: x.position)
    transfers_out = sorted((p for p in team if p not in best), key=lambda x: x.position)

    max_len_in_name = max(len(p.webname) for p in transfers_in)
    max_len_in_team = max(len(p.team) for p in transfers_in)

    max_len_out_name = max(len(p.webname) for p in transfers_out)
    max_len_out_team = max(len(p.team) for p in transfers_out)

    print("\n>>>> Suggest transfers")
    for o, i in zip(transfers_out, transfers_in):
        print(
            f"{o.position}: {o.webname:<{max_len_out_name}} {o.team:<{max_len_out_team}} {o.xP:<5.2f}"
            "  -->>  "
            f"{i.webname:<{max_len_in_name}} {i.team:<{max_len_in_team}} {i.xP:.2f}"
        )
    print(
        f"lxp gain: {(helpers.best_lineup_xP(best) - helpers.best_lineup_xP(team)):.2f}"
    )


if __name__ == "__main__":
    main()
