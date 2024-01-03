from __future__ import annotations

import argparse
import itertools

from lazyfpl import fetch, helpers

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--top",
        "-t",
        default=None,
        help="Top N players per position. (default: %(default)s)",
        type=int,
    )
    parser.add_argument(
        "--no-news",
        action="store_true",
        help="Drop players with news attched to them. (default: %(default)s)",
    )
    args = parser.parse_args()

    players = sorted(
        fetch.players(),
        key=lambda x: (helpers.position_order(x.position), x.xP or 0),
        reverse=True,
    )

    if args.no_news:
        players = [p for p in players if not p.news]

    players = list(
        itertools.chain.from_iterable(
            [
                list(p)[: args.top]
                for _, p in itertools.groupby(
                    players,
                    key=lambda x: helpers.position_order(x.position),
                )
            ]
        )
    )
    bis = helpers.best_lineup(players)

    print(
        helpers.tabulater(
            [dict({"BIS": "X" if p in bis else ""} | p.display()) for p in players],
        ),
    )
