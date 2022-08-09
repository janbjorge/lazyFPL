import typing as T
import argparse

import constraints
import fetch
import helpers
import optimizer
import structures


def transfer(
    current: T.List[structures.Player],
    best: T.List[structures.Player],
    best_lxp: float,
    pool: T.List[structures.Player],
    budget: int,
    done_transfers: int,
    max_transfers: int,
) -> T.List[structures.Player]:

    if (done_transfers == max_transfers and
        helpers.squad_price(current) <= budget
        and helpers.best_lineup_xP(current) > best_lxp
        and constraints.team_constraint(current, n=3)):
            return current
    elif done_transfers > max_transfers:
        return []

    for transfer_in in pool:
        for idx, _ in enumerate(current):

            out = current[idx]

            if transfer_in.name == out.name or transfer_in.position != out.position:
                continue

            tmp = current.copy()
            tmp[idx] = transfer_in

            best = transfer(
                current=tmp,
                best=best,
                best_lxp=helpers.best_lineup_xP(best),
                pool=pool,
                budget=budget,
                done_transfers=done_transfers+1,
                max_transfers=max_transfers,
            ) or best

    return best


def main() -> None:

    parser = argparse.ArgumentParser(
        prog="Transfer optimizer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--max_transfers", type=int, required=True)
    parser.add_argument("--topn", type=int, required=True)

    args = parser.parse_args()

    pool = sorted(fetch.players(), key=lambda x:x.xP(), reverse=True)[:args.topn]
    print(f"pool size: {len(pool)}")
    team = list(fetch.my_team())
    best = transfer(
        current=team,
        best=team,
        best_lxp=helpers.best_lineup_xP(team),
        pool=pool,
        budget=helpers.squad_price(team),
        done_transfers=0,
        max_transfers=args.max_transfers,
    )
    transfer_out = sorted((p for p in best if p not in team), key=lambda x:x.position)
    transfer_in = sorted((p for p in team if p not in best), key=lambda x:x.position)

    max_len_out_name = max(len(p.name) for p in transfer_out)
    for t_out, t_in in zip(transfer_in, transfer_out):
        print(f"{t_out.name:<{max_len_out_name}}({t_out.xP():.2f})  -->>  {t_in.name}({t_in.xP():.2f})")

    print(f"lxp gain: {(helpers.best_lineup_xP(best) - helpers.best_lineup_xP(team)):.2f}")


if __name__ == "__main__":
    main()
