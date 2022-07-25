import csv
import datetime
import io
import itertools
import statistics
import typing as T

import requests
from dateutil.parser import parse as dt_parser


import cache
import helpers
import structures


@cache.fcache(ttl=datetime.timedelta(days=1))
def bootstrap() -> dict:
    return requests.get(
        "https://fantasy.premierleague.com/api/bootstrap-static/"
    ).json()


def player_price(name: str) -> float:
    for element in bootstrap()["elements"]:
        if f'{element["first_name"]} {element["second_name"]}' == name:
            return element["now_cost"]
    raise ValueError(f"No player named: {name}")


def team(player_name: str) -> str:

    match = None
    for item in bootstrap()["elements"]:
        if f'{item["first_name"]} {item["second_name"]}' == player_name:
            match = item

    if not match:
        raise ValueError(f"No player named: {player_name}")

    for item in bootstrap()["teams"]:
        if match["team"] == item["id"]:
            return item["name"]
    raise ValueError(f"No team name: {player_name}")


def merged_team_list(
    url="https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/master_team_list.csv",
) -> T.Generator[dict[str, str], None, None]:
    yield from csv.DictReader(io.StringIO(requests.get(url).text))


@cache.fcache(ttl=datetime.timedelta(days=1))
def players(
    url: str = "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2021-22/gws/merged_gw.csv",
) -> tuple[structures.Player, ...]:
    team_name_lookup = {row["team"]: row["team_name"] for row in merged_team_list()}

    players: list[structures.Player] = []

    for name, matches in itertools.groupby(
        sorted(
            csv.DictReader(io.StringIO(requests.get(url).text), delimiter=","),
            key=lambda r: r["name"],
        ),
        key=lambda r: r["name"],
    ):

        try:
            price = player_price(name)
        except ValueError:
            continue

        matches = sorted(matches, key=lambda r: dt_parser(r["kickoff_time"]))
        players.append(
            structures.Player(
                minutes=[int(r["minutes"]) for r in matches],
                name=name,
                opponent=[team_name_lookup[r["opponent_team"]] for r in matches],
                points=[int(r["total_points"]) for r in matches],
                position=matches[-1]["position"],
                price=price,
                selected=[int(r["selected"]) for r in matches],
                team=team(name),
            )
        )

    return sorted(players, key=lambda x: (x.position, x.price, x.name))


def top_position_players(
    strikers: int,
    midfielders: int,
    defenders: int,
    goalkeeper: int,
) -> T.Generator[
    tuple[T.Literal["GK", "DEF", "MID", "FWD"], tuple[structures.Player, ...]],
    None,
    None,
]:
    for _position, _players in itertools.groupby(
        sorted(players(), key=lambda x: x.position),
        key=lambda x: x.position,
    ):
        if _position == "GK":
            n = goalkeeper
        elif _position == "DEF":
            n = defenders
        elif _position == "MID":
            n = midfielders
        elif _position == "FWD":
            n = strikers
        else:
            raise NotImplementedError(_position)

        _players = tuple(sorted(_players, key=lambda x: x.xP()))
        _mean_tm = statistics.mean(p.tm for p in _players if p.tm > 0)
        _players = tuple(p for p in _players if p.tm > _mean_tm)
        yield _position, _players[-n:]


if __name__ == "__main__":
    pool = []
    for pos, top, buttom in top_position_players():
        pool.extend(top)
        pool.extend(buttom)
        print(pos, len(top), len(buttom))
    helpers.lprint(pool)
