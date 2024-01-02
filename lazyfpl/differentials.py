from __future__ import annotations

import argparse

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

    players = sorted(
        [
            p
            for p in fetch.players()
            if p.selected > args.min_selected
            and (p.xP or 0) > args.min_xp
            and p.mtm() > args.min_mtm
        ],
        key=lambda x: (
            -helpers.position_order(x.position),
            -(x.xP or 0) / (x.selected or 1),
        ),
    )

    if args.no_news:
        players = [p for p in players if not p.news]

    print(
        helpers.tabulater(
            [p.display() for p in players],
        ),
    )
