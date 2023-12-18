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
    args = parser.parse_args()

    players = list(
        itertools.chain(
            *[
                list(p)[: args.top] if args.top else list(p)
                for _, p in itertools.groupby(
                    sorted(
                        fetch.players(),
                        key=lambda x: (x.position, x.xP or 0),
                        reverse=True,
                    ),
                    key=lambda x: x.position,
                )
            ]
        )
    )

    print(structures.Squad(players))
