from __future__ import annotations

import argparse
from itertools import chain, groupby

from lazyfpl import fetch, helpers

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--min-mtm",
        type=float,
        default=0.0,
        help="(default: %(default)s)",
    )
    parser.add_argument(
        "--min-selected",
        "-mc",
        default=1_000,
        help=(
            "Player must be selected by at least this amunt of"
            "managers. (default: %(default)s)"
        ),
        type=int,
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
        help="Drop players with news attched to them. (default: %(default)s)",
    )
    parser.add_argument(
        "--top",
        "-t",
        default=None,
        help="Top N players per position. (default: %(default)s)",
        type=int,
    )
    args = parser.parse_args()

    pool = fetch.players()

    if args.no_news:
        pool = [p for p in pool if not p.news]

    pool = sorted(
        [
            p
            for p in pool
            if p.selected > args.min_selected
            and (p.xP or 0) > args.min_xp
            and p.mtm() > args.min_mtm
        ],
        key=lambda x: (
            -helpers.position_order(x.position),
            -(x.xP or 0) / (x.selected or 1),
        ),
    )

    pool = list(
        chain.from_iterable(
            list(x)[: args.top]
            for _, x in groupby(
                pool,
                key=lambda x: helpers.position_order(x.position),
            )
        )
    )

    print(
        helpers.tabulater(
            [
                p.display()
                for p in sorted(
                    pool,
                    key=lambda x: (
                        -helpers.position_order(x.position),
                        -(x.xP or 0),
                    ),
                )
            ],
        ),
    )
