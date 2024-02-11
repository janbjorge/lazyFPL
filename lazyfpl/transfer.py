from __future__ import annotations

import argparse
import collections
import itertools
from typing import Generator, NamedTuple, Sequence

from lazyfpl import fetch, helpers, optimizer, structures


class Transfer(NamedTuple):
    bought: optimizer.PositionCombination
    sold: optimizer.PositionCombination


def display(trans: Transfer) -> None:
    """Displays the changes between the old and new player sequences,
    including transfers in and out."""
    sold = sorted(
        (p for p in trans.sold.players),
        key=lambda x: helpers.position_order(x.position),
    )
    bought = sorted(
        (p for p in trans.bought.players),
        key=lambda x: helpers.position_order(x.position),
    )

    max_len_in_name = max(len(p.webname) for p in bought)
    max_len_in_team = max(len(p.team) for p in bought)

    max_len_out_name = max(len(p.webname) for p in sold)
    max_len_out_team = max(len(p.team) for p in sold)

    print("-" * 75)

    for s, b in zip(sold, bought):
        print(
            f"{s.position}: {s.webname:<{max_len_out_name}} "
            f"- {s.team:<{max_len_out_team}} {s.xP or 0.0:<5.1f}"
            "  -->>  "
            f"{b.webname:<{max_len_in_name}} - "
            f"{b.team:<{max_len_in_team}} {b.xP or 0.0:.1f}"
        )
    print(f"xP gain: {(trans.bought.xP-trans.sold.xP):.1f}")


def transfer(
    current: Sequence[structures.Player],
    pool: Sequence[structures.Player],
    add: Sequence[structures.Player],
    remove: Sequence[structures.Player],
    max_transfers: int,
    max_budget: int = 1000,
    max_players_per_team: int = 3,
) -> Generator[Transfer, None, None]:
    """Generates transfer options for a given squad within specified
    constraints and preferences."""

    sold = {
        n: tuple(
            optimizer.PositionCombination(
                helpers.squad_price(c), helpers.squad_xP(c), c
            )
            for c in sorted(
                itertools.combinations(current, n),
                key=helpers.squad_price,
            )
        )
        for n in range(1, max_transfers + 1)
    }

    if remove:
        for n, combinations in sold.items():
            sold[n] = tuple(
                c for c in combinations if all(r in c.players for r in remove)
            )

    pool = [p for p in pool if p not in current]
    bought = {
        n: tuple(
            optimizer.PositionCombination(
                helpers.squad_price(c), helpers.squad_xP(c), c
            )
            for c in sorted(
                itertools.combinations(pool, n),
                key=helpers.squad_price,
            )
        )
        for n in range(1, max_transfers + 1)
    }
    if add:
        for n, combinations in bought.items():
            bought[n] = tuple(
                c for c in combinations if all(a in c.players for a in add)
            )

    min_bought_price = {
        n: min(c.price for c in combinations) for n, combinations in bought.items()
    }

    for n, combinations in sold.items():
        print(f"Sell combinations:   {n} - {len(combinations)}")

    for n, combinations in bought.items():
        print(f"Bought combinations: {n} - {len(combinations)}")

    current_squad_price = helpers.squad_price(current)
    current_team_tally = collections.Counter(p.team for p in current)

    for nin, bought_combinations in bought.items():
        for sold_combination in sold[nin]:
            if (
                current_squad_price - sold_combination.price + min_bought_price[nin]
                > max_budget
            ):
                continue

            for bought_combination in bought_combinations:
                if bought_combination.xP < sold_combination.xP:
                    continue

                if (
                    current_squad_price
                    - sold_combination.price
                    + bought_combination.price
                    > max_budget
                ):
                    continue

                team_tally = (
                    current_team_tally
                    + collections.Counter(p.team for p in bought_combination.players)
                    - collections.Counter(p.team for p in sold_combination.players)
                )
                if max(team_tally.values()) > max_players_per_team:
                    continue

                bought_sold_position_tally = collections.Counter(
                    p.position for p in bought_combination.players
                ) - collections.Counter(p.position for p in sold_combination.players)

                if bought_sold_position_tally:
                    continue

                yield Transfer(
                    bought_combination,
                    sold_combination,
                )


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

    if args.min_xp:
        pool = [p for p in pool if p.xP >= args.min_xp]

    if args.min_mtm:
        pool = [p for p in pool if p.mtm() >= args.min_mtm]

    if args.no_news:
        pool = [p for p in pool if not p.news]

    if args.add:
        pool += [p for p in fetch.players() if p.webname in args.add]

    print(">>> Pool")
    print(structures.Squad(pool))

    print("\n>>>> Current team")
    team = fetch.my_team()
    print(team)
    print()

    transfers = sorted(
        transfer(
            current=team.players,
            pool=list(set(pool)),
            add=[p for p in pool if p.webname in args.add] if args.add else [],
            remove=[p for p in team.players if p.webname in args.remove]
            if args.remove
            else [],
            max_transfers=args.max_transfers,
        ),
        key=lambda x: x.bought.xP - x.sold.xP,
    )[-100:]

    for trans in transfers:
        display(trans)


if __name__ == "__main__":
    main()
