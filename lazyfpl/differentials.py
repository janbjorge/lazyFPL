from __future__ import annotations

from itertools import chain, groupby

from lazyfpl import fetch, helpers


def main(
    min_mtm: float,
    min_selected: int,
    min_xp: float,
    no_news: bool,
    top: int,
) -> None:
    pool = fetch.players()

    if no_news:
        pool = [p for p in pool if not p.news]

    pool = sorted(
        [
            p
            for p in pool
            if p.selected > min_selected and (p.xP or 0) > min_xp and p.mtm() > min_mtm
        ],
        key=lambda x: (
            -helpers.position_order(x.position),
            -(x.xP or 0) / (x.selected or 1),
        ),
    )

    pool = list(
        chain.from_iterable(
            list(x)[:top]
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
