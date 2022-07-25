import typing as T
import itertools
import math

import structures


def total_price(lineup: list[structures.Player]) -> int:
    return sum(p.price for p in lineup)


def total_xP(lineup: T.Sequence[structures.Player]) -> float:
    return round(sum(p.xP() for p in lineup), 1)


def sigmoid_weights(n: int) -> list[float]:
    def sig(x: float) -> float:
        return 1 / (1 + math.exp(-x))

    weights = [sig(x / n) for x in range(n)]
    sum_weights = sum(weights)
    return [w / sum_weights for w in weights]


def weighted_mean(distribution: list[float], weights: list[float]) -> float:
    assert len(distribution) == len(weights)
    return sum(d * w for d, w in zip(distribution, weights)) / sum(weights)


def lprint(lineup: T.List[structures.Player]) -> None:

    if not lineup:
        return

    def position_order(position: str) -> int:
        if position == "GK":
            return 0
        if position == "DEF":
            return 1
        if position == "MID":
            return 2
        if position == "FWD":
            return 3
        raise NotImplementedError(position)

    print("", flush=True)
    header(lineup)
    for pos, players in itertools.groupby(
        sorted(
            lineup, key=lambda x: (position_order(x.position), x.xP()), reverse=True
        ),
        key=lambda x: x.position,
    ):
        players = tuple(players)
        header(players, prefix=f"{pos}(", postfix=")")
        print(f" xP   Price  Team            Player")
        for player in players:
            print(
                f" {player.xP():<4} {player.price/10:<6} {player.team:<{15}} {player.name}"
            )


def header(pool: T.List[structures.Player], prefix="", postfix="") -> None:
    print(
        f"{prefix}Price: {total_price(pool)/10} xP: {total_xP(pool)} n: {len(pool)}{postfix}"
    )
