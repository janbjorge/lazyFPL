from __future__ import annotations

import argparse
import itertools

from lazyfpl import fetch, structures

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
        key=lambda x: (
            x.position,
            -(x.xP or 0) / (x.selected or 1),
        ),
    )

    if args.no_news:
        players = [p for p in players if not p.news]

    print(
        structures.Squad(
            list(
                itertools.chain.from_iterable(
                    [
                        list(p)[: args.top]
                        for _, p in itertools.groupby(
                            players,
                            key=lambda x: x.position,
                        )
                    ]
                )
            )
        )
    )
