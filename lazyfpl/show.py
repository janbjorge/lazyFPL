from __future__ import annotations

import itertools

from lazyfpl import fetch, helpers


def main(top: int, no_news: bool) -> None:
    players = sorted(
        fetch.players(),
        key=lambda x: (helpers.position_order(x.position), x.xP or 0),
        reverse=True,
    )

    if no_news:
        players = [p for p in players if not p.news]

    players = list(
        itertools.chain.from_iterable(
            [
                list(p)[:top]
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
