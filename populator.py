from dateutil.parser import parse as dt_parser
import csv
import functools
import io
import typing as T

from tqdm import tqdm
import requests

import database


@functools.cache
def bootstrap() -> dict:
    return requests.get(
        "https://fantasy.premierleague.com/api/bootstrap-static/"
    ).json()


def summary(id: int) -> dict:
    assert isinstance(id, int)
    return requests.get(
        f"https://fantasy.premierleague.com/api/element-summary/{id}/"
    ).json()


def past_team_lists() -> dict[str, list[dict]]:
    urls = (
        (
            "2022-23",
            "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2022-23/teams.csv",
        ),
        (
            "2021-22",
            "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2021-22/teams.csv",
        ),
    )
    return {
        session: list(csv.DictReader(io.StringIO(requests.get(url).text)))
        for session, url in urls
    }


@functools.cache
def past_team_lookup(tid: int, session: str) -> str:
    assert isinstance(tid, int)
    for team in past_team_lists()[session]:
        if int(team["id"]) == tid:
            return team["name"]
    raise ValueError(f"No match: {tid} / {session}.")


def past_game_lists() -> dict[str, list[dict]]:
    urls = (
        (
            "2022-23",
            "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2022-23/gws/merged_gw.csv",
        ),
        (
            "2021-22",
            "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2021-22/gws/merged_gw.csv",
        ),
    )
    return {
        session: list(csv.DictReader(io.StringIO(requests.get(url).text)))
        for session, url in urls
    }


def structure():
    database.execute(
        """
        CREATE TABLE team (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            session TEXT NOT NULL,
            strength_attack_away INTEGER NOT NULL,
            strength_attack_home INTEGER NOT NULL,
            strength_defence_away INTEGER NOT NULL,
            strength_defence_home INTEGER NOT NULL,
            strength_overall_away INTEGER NOT NULL,
            strength_overall_home INTEGER NOT NULL,
            UNIQUE(name, session)
        )
    """
    )
    database.execute(
        """
        CREATE TABLE game (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            is_home INTEGER NOT NULL,
            kickoff REAL NOT NULL,
            minutes INTEGER,
            opponent INTEGER NOT NULL,
            player TEXT NOT NULL,
            points INTEGER,
            position TEXT NOT NULL,
            session TEXT NOT NULL,
            team INTEGER NOT NULL,
            upcoming INTEGER NOT NULL,
            FOREIGN KEY(team) REFERENCES team(id),
            FOREIGN KEY(opponent) REFERENCES team(id)
        );
    """
    )


def populate_teams():
    sql = """
        INSERT INTO team (
            name,
            session,
            strength_attack_away,
            strength_attack_home,
            strength_defence_away,
            strength_defence_home,
            strength_overall_away,
            strength_overall_home
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """
    for session, teams in past_team_lists().items():
        for team in teams:
            database.execute(
                sql,
                (
                    team["name"],
                    session,
                    team["strength_attack_away"],
                    team["strength_attack_home"],
                    team["strength_defence_away"],
                    team["strength_defence_home"],
                    team["strength_overall_away"],
                    team["strength_overall_home"],
                ),
            )


def populate_games():
    sql = """
        INSERT INTO game (
            is_home,
            kickoff,
            minutes,

            opponent,
            player,
            points,

            team,
            position,
            session,
            upcoming
        ) VALUES (
            ?,
            ?,
            ?,

            (SELECT id FROM team WHERE session = ? AND name = ?),
            ?,
            ?,

            (SELECT id FROM team WHERE session = ? AND name = ?),
            ?,
            ?,
            ?
        );
    """
    for session, games in past_game_lists().items():
        for game in tqdm(
            games,
            ascii=True,
            bar_format="{percentage:3.0f}% | {bar:20} {r_bar}",
            unit_divisor=1_000,
            unit_scale=True,
        ):
            database.execute(
                sql,
                (
                    game["was_home"],
                    dt_parser(game["kickoff_time"]).timestamp(),
                    game["minutes"],
                    session,
                    past_team_lookup(int(game["opponent_team"]), session),
                    game["name"],
                    game["total_points"],
                    session,
                    game["team"],
                    game["position"],
                    session,
                    False,
                ),
            )
    database.execute(
        """
        UPDATE
            game
        SET
            position = "GKP"
        WHERE
            position = "GK"
    """
    )

    bootstrap = requests.get(
        "https://fantasy.premierleague.com/api/bootstrap-static/"
    ).json()
    session = "2022-23"
    for ele in tqdm(
        bootstrap["elements"],
        ascii=True,
        bar_format="{percentage:3.0f}% | {bar:20} {r_bar}",
        unit_divisor=1_000,
        unit_scale=True,
    ):
        fullname = f'{ele["first_name"]} {ele["second_name"]}'
        team = upcoming_team_id_to_name(ele["team"])
        for upcoming in summary(ele["id"])["fixtures"]:
            team_h = upcoming_team_id_to_name(upcoming["team_h"])
            team_a = upcoming_team_id_to_name(upcoming["team_a"])
            is_home = team == team_h
            database.execute(
                sql,
                (
                    is_home,
                    dt_parser(upcoming["kickoff_time"]).timestamp(),
                    None,
                    session,
                    team_a if is_home else team_h,
                    fullname,
                    None,
                    session,
                    team,
                    upcoming_position(fullname),
                    session,
                    True,
                ),
            )


@functools.cache
def upcoming_team_id_to_name(id: int) -> str:
    for item in bootstrap()["teams"]:
        if id == item["id"]:
            return item["name"]
    raise ValueError(f"No team name: {id}")


@functools.cache
def upcoming_position(name: str) -> T.Literal["GKP", "DEF", "MID", "FWD"]:
    for element in bootstrap()["elements"]:
        if f'{element["first_name"]} {element["second_name"]}' == name:
            element_type = bootstrap()["element_types"][element["element_type"] - 1]
            return element_type["singular_name_short"]
    raise ValueError(f"No player named: {name}")


if __name__ == "__main__":
    structure()
    populate_teams()
    populate_games()
