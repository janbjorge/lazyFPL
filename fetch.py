import csv
import io
import itertools
import typing as T

import requests
from dateutil.parser import parse as dt_parser


import cache
import helpers
import structures


@cache.fcache
def bootstrap() -> dict:
    return requests.get(
        "https://fantasy.premierleague.com/api/bootstrap-static/"
    ).json()


def player_price(name: str) -> float:
    for element in bootstrap()["elements"]:
        if f'{element["first_name"]} {element["second_name"]}' == name:
            return element["now_cost"]
    raise ValueError(f"No player named: {name}")


def player_id(name: str) -> int:
    for element in bootstrap()["elements"]:
        if f'{element["first_name"]} {element["second_name"]}' == name:
            return element["id"]
    raise ValueError(f"No player named: {name}")


@cache.fcache
def summary(id: int) -> dict:
    return requests.get(
        f"https://fantasy.premierleague.com/api/element-summary/{id}/"
    ).json()


def fixtures(name: str) -> tuple[structures.Fixture, ...]:
    return sorted(
        (
            structures.Fixture(
                at_home=f["is_home"],
                away=team_name_from_id(f["team_a"]),
                difficulty=f["difficulty"],
                home=team_name_from_id(f["team_h"]),
                kickoff_time=dt_parser(f["kickoff_time"]),
            )
            for f in summary(player_id(name))["fixtures"]
        ),
        key=lambda x: x.kickoff_time,
    )


@cache.fcache
def team_name_from_id(id: int) -> str:
    for item in bootstrap()["teams"]:
        if id == item["id"]:
            return item["name"]
    raise ValueError(f"No team name: {id}")


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


@cache.fcache
def players(
    url: str = "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2021-22/gws/merged_gw.csv",
) -> tuple[structures.Player, ...]:
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
                fixutres=fixtures(name),
                minutes=[int(r["minutes"]) for r in matches],
                name=name,
                points=[int(r["total_points"]) for r in matches],
                position=matches[-1]["position"],
                price=price,
                selected=[int(r["selected"]) for r in matches],
                team=team(name),
            )
        )

    return sorted(players, key=lambda x: (x.xP(), x.name))


def player(name: str) -> structures.Player:
    for p in players():
        if p.name.lower() == name.lower():
            return p
    raise ValueError(f"Unkown name {name}")


if __name__ == "__main__":
    helpers.lprint(players())
