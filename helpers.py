import typing as T
import itertools
import math

import structures


def total_price(lineup: list[structures.Player]) -> int:
    return sum(p.price for p in lineup)


def total_xP(lineup: T.Sequence[structures.Player]) -> float:
    return round(sum(p.xP() for p in lineup), 2)


def valid_formation(
    lineup: T.Sequence[structures.Player],
    eligible: tuple[tuple[int, int, int, int], ...] = (
        # gk, def, mid, fwd
        (1, 3, 4, 3),
        (1, 3, 5, 2),
        (1, 4, 3, 3),
        (1, 4, 4, 2),
        (1, 4, 5, 1),
        (1, 5, 2, 3),
        (1, 5, 3, 2),
        (1, 5, 4, 1),
    ),
) -> bool:
    sgk = sum(1 for p in lineup if p.position == "GK")
    sdf = sum(1 for p in lineup if p.position == "DEF")
    smd = sum(1 for p in lineup if p.position == "MID")
    sfw = sum(1 for p in lineup if p.position == "FWD")
    return (sgk, sdf, smd, sfw) in eligible


def best_lineup(
    team: list[structures.Player],
) -> list[structures.Player]:
    return max(
        itertools.combinations(team, 11),
        key=lambda c: valid_formation(c) * total_xP(c),
    )


def best_lineup_xP(lineup: list[structures.Player]) -> float:
    return total_xP(best_lineup(lineup))


def sigmoid_weights(n: int) -> list[float]:
    def sig(x: float) -> float:
        return 1 / (1 + math.exp(-x))

    weights = [sig(x / n) for x in range(n)]
    sum_weights = sum(weights)
    return [w / sum_weights for w in weights]


def weighted_mean(distribution: list[float], weights: list[float]) -> float:
    assert len(distribution) == len(weights)
    return sum(d * w for d, w in zip(distribution, weights)) / sum(weights)


def lprint(lineup: list[structures.Player], best: list[str] | None = None) -> None:

    if not best:
        best = []

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
        print(f" xP    Price  Team            Player")
        for player in players:
            print(
                f" {player.xP():<5.2f} {player.price/10:<6} {player.team:<{15}} {player.name} {'X' if player.name in best else ''}"
            )


def header(pool: list[structures.Player], prefix="", postfix="") -> None:
    print(
        f"{prefix}Price: {total_price(pool)/10} xP: {total_xP(pool):.1f} n: {len(pool)}{postfix}"
    )
