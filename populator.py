from dateutil.parser import parse as dt_parser
import csv
import functools
import io
import os
import pathlib
import sqlite3

import requests

import cache


def dbfile(
    file: str = os.environ.get("FPL_DATABASE", "database.sqlite3")
) -> pathlib.Path:
    return pathlib.Path(file)


@functools.cache
def connect(file: pathlib.Path = dbfile()):
    return sqlite3.connect(file)


def execute(sql: str, parameters: tuple = tuple()) -> None:
    with connect() as conn:
        conn.execute(sql, parameters)


@cache.fcache
def team_lists() -> dict[str, list[dict]]:
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


def team_lookup(tid: int, session: str) -> str:
    assert isinstance(tid, int)
    for team in team_lists()[session]:
        if int(team["id"]) == tid:
            return team["name"]
    raise ValueError(f"No match: {tid} / {session}.")


@cache.fcache
def game_lists() -> dict[str, list[dict]]:
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
    execute(
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
    execute(
        """
        CREATE TABLE game (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            is_home INTEGER NOT NULL,
            kickoff REAL NOT NULL,
            minutes INTEGER NOT NULL,
            opponent INTEGER NOT NULL,
            player TEXT NOT NULL,
            points INTEGER NOT NULL,
            position TEXT NOT NULL,
            session TEXT NOT NULL,
            team INTEGER NOT NULL,
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
    for session, teams in team_lists().items():
        for team in teams:
            execute(
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
            session
        ) VALUES (
            ?,
            ?,
            ?,

            (SELECT id FROM team WHERE session = ? AND name = ?),
            ?,
            ?,

            (SELECT id FROM team WHERE session = ? AND name = ?),
            ?,
            ?
        );
    """
    for session, games in game_lists().items():
        for game in games:
            execute(
                sql,
                (
                    game["was_home"],
                    dt_parser(game["kickoff_time"]).timestamp(),
                    game["minutes"],
                    session,
                    team_lookup(int(game["opponent_team"]), session),
                    game["name"],
                    game["total_points"],
                    session,
                    game["team"],
                    game["position"],
                    session,
                ),
            )
    execute(
        """
        UPDATE
            game
        SET
            position = "GKP"
        WHERE
            position = "GK"
    """
    )


if __name__ == "__main__":
    structure()
    populate_teams()
    populate_games()
