import csv
import functools
import io
import itertools
import os
import typing as T

import requests
from dateutil.parser import parse as dt_parser


import cache
import helpers
import structures


@cache.fcache
def get(url: str) -> requests.Response:
    return requests.get(url)


def bootstrap() -> dict:
    return get("https://fantasy.premierleague.com/api/bootstrap-static/").json()


def position(name: str) -> T.Literal["GKP", "DEF", "MID", "FWD"]:
    for element in bootstrap()["elements"]:
        if f'{element["first_name"]} {element["second_name"]}' == name:
            element_type = bootstrap()["element_types"][element["element_type"] - 1]
            return element_type["singular_name_short"]
    raise ValueError(f"No player named: {name}")


def player_id(name: str) -> int:
    for element in bootstrap()["elements"]:
        if f'{element["first_name"]} {element["second_name"]}' == name:
            return element["id"]
    raise ValueError(f"No player named: {name}")


def player_name(pid: int) -> str:
    for element in bootstrap()["elements"]:
        if element["id"] == pid:
            return f'{element["first_name"]} {element["second_name"]}'
    raise ValueError(f"No player named: {pid}")


def summary(id: int) -> dict:
    return get(f"https://fantasy.premierleague.com/api/element-summary/{id}/").json()


def upcoming_fixutres(name: str) -> list[structures.Fixture]:
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


@functools.cache
def team_name_from_id(id: int) -> str:
    for item in bootstrap()["teams"]:
        if id == item["id"]:
            return item["name"]
    raise ValueError(f"No team name: {id}")


def current_team(player_name: str) -> str:

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


@functools.cache
def remote(url: str) -> dict[str, list[dict]]:
    return {
        name: sorted(
            list(matches),
            key=lambda r: dt_parser(r["kickoff_time"]),
            reverse=True,
        )
        for name, matches in itertools.groupby(
            sorted(
                csv.DictReader(io.StringIO(get(url).text), delimiter=","),
                key=lambda r: r["name"],
            ),
            key=lambda r: r["name"],
        )
    }


def past_matches(player_name: str) -> list[dict]:
    player_name = player_name.lower()
    urls = (
        "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2022-23/gws/merged_gw.csv",
        "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2021-22/gws/merged_gw.csv",
    )
    matches = []
    for url in urls:
        for name, session_matches in remote(url).items():
            name = name.lower()
            if (
                name == player_name
                or all(sub in player_name for sub in name.split())
                or all(sub in name for sub in player_name.split())
            ):
                matches.extend(session_matches)
    return sorted(matches, key=lambda r: dt_parser(r["kickoff_time"]), reverse=True)


@cache.fcache
def players() -> list[structures.Player]:
    pool = list[structures.Player]()
    for player in bootstrap()["elements"]:
        full_name = f'{player["first_name"]} {player["second_name"]}'
        pm = past_matches(full_name)

        backtrace = 3
        # Missing historical data for: {full_name}, setting xP=0,"
        if len(past_points := [int(r["total_points"]) for r in pm]) > backtrace:
            upcoming_difficulty = sum(
                f.difficulty for f in upcoming_fixutres(full_name)[:backtrace]
            ) / (3 * backtrace)
            xp = (
                helpers.xP(past_points=past_points, backtrace=backtrace)
                / upcoming_difficulty
            )
        else:
            xp = 0

        pool.append(
            structures.Player(
                fixutres=upcoming_fixutres(full_name),
                minutes=[int(r["minutes"]) for r in pm],
                name=full_name,
                news=player["news"],
                points=[int(r["total_points"]) for r in pm],
                position=position(full_name),
                price=int(player["now_cost"]),
                selected=[int(r["selected"]) for r in pm],
                team=current_team(full_name),
                webname=player["web_name"],
                xP=xp,
            )
        )

    return sorted(pool, key=lambda x: (x.xP, x.price, x.team, x.name))


def my_team(
    team_id: str = "3483226",
    pl_profile: str = os.environ.get("FPL_COOKIE", ""),
) -> T.Sequence[structures.Player]:
    if not pl_profile:
        raise ValueError("Missing `FPL_COOKIE`.")
    team = requests.get(
        f"https://fantasy.premierleague.com/api/my-team/{team_id}/",
        cookies={"pl_profile": pl_profile},
    ).json()
    names = set(player_name(pick["element"]) for pick in team["picks"])
    return [p for p in players() if p.name in names]


if __name__ == "__main__":
    helpers.lprint(players())
