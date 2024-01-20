from __future__ import annotations

import argparse
import concurrent.futures
import csv
import datetime
import functools
import io
import urllib.parse as up

import pytz
import requests
from dateutil.parser import parse as dtparser
from tqdm.std import tqdm

from lazyfpl import database, structures


def now_tz_utc() -> datetime.datetime:
    """Returns the current time in UTC timezone."""
    return datetime.datetime.now(tz=pytz.utc)


@functools.cache
def bootstrap() -> dict:
    """Fetches data from the Fantasy Premier League API's bootstrap-static endpoint."""
    return requests.get(
        "https://fantasy.premierleague.com/api/bootstrap-static/"
    ).json()


@functools.cache
def summary(id: int) -> dict:
    """Fetches player summary for a given player ID from the
    Fantasy Premier League API."""
    assert isinstance(id, int)
    return requests.get(
        f"https://fantasy.premierleague.com/api/element-summary/{id}/"
    ).json()


@functools.cache
def db_name_pid() -> dict[str, int]:
    """Creates a dictionary mapping player names to their database IDs."""
    return {
        row["name"]: row["id"]
        for row in database.execute(
            """
        SELECT
            id,
            name
        FROM
            player
        """
        )
    }


@functools.cache
def player_id_fuzzer(name: str) -> int | None:
    """Attempts to find a player ID in the database matching the
    given name, with some flexibility for variations."""
    for dname, pid in db_name_pid().items():
        if dname.casefold() == name.casefold():
            return pid
        if all(n in dname.casefold() for n in name.casefold().split()):
            return pid
        if all(n in name.casefold() for n in dname.casefold().split()):
            return pid

    return None


def session_from_url(url: str) -> str:
    """Extracts the session year from a given URL."""
    return up.urlparse(url).path.split("/")[5]


@functools.cache
def past_team_lists() -> dict[str, list[structures.Team]]:
    """Fetches and parses past team data from external sources for different seasons."""
    urls = (
        "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2023-24/teams.csv",
        "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2022-23/teams.csv",
        "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2021-22/teams.csv",
    )

    return {
        session_from_url(url): [
            structures.Team.model_validate(t)
            for t in csv.DictReader(io.StringIO(requests.get(url).text))
        ]
        for url in urls
    }


@functools.cache
def past_team_lookup(tid: int, session: database.SESSIONS) -> str:
    """Finds the team name for a given team ID and session."""
    assert isinstance(tid, int)
    for team in past_team_lists()[session]:
        if team.id == tid:
            return team.name
    raise ValueError(f"No match: {tid} / {session}.")


@functools.cache
def past_game_lists() -> dict[str, list[dict]]:
    """Fetches and parses past game data from external sources for different seasons."""
    urls = (
        "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2023-24/gws/merged_gw.csv",
        "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2022-23/gws/merged_gw.csv",
        "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2021-22/gws/merged_gw.csv",
    )
    return {
        session_from_url(url): list(csv.DictReader(io.StringIO(requests.get(url).text)))
        for url in urls
    }


def initialize_database() -> None:
    """Initializes the database with the necessary tables."""
    database.execute(
        """
        CREATE TABLE team (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            short_name TEXT NOT NULL,
            web_team_id INTEGER NOT NULL,
            session TEXT NOT NULL,
            strength INTEGER NOT NULL,
            UNIQUE(name, session)
        )
    """
    )
    database.execute(
        """
        CREATE TABLE player (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            webname TEXT NOT NULL,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            team_id INTEGER NOT NULL,
            news TEXT NOT NULL,
            model BLOB,
            FOREIGN KEY(team_id) REFERENCES team(id),
            UNIQUE(webname, name, team_id)
        );
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
            player_id INTEGER NOT NULL,
            points INTEGER,
            position TEXT NOT NULL,
            session TEXT NOT NULL,
            team INTEGER NOT NULL,
            upcoming INTEGER NOT NULL,
            selected INTEGER NOT NULL,
            FOREIGN KEY(opponent) REFERENCES team(id),
            FOREIGN KEY(player_id) REFERENCES player(id),
            FOREIGN KEY(team) REFERENCES team(id)
        );
    """
    )


def nuke_database() -> None:
    """Removes all existing tables from the database."""
    database.execute("""DROP TABLE IF EXISTS game;""")
    database.execute("""DROP TABLE IF EXISTS player;""")
    database.execute("""DROP TABLE IF EXISTS team;""")


def populate_teams() -> None:
    """Populates the database with team data."""
    sql = """
        INSERT INTO team (
            name,
            short_name,
            session,
            web_team_id,
            strength
        ) VALUES (?, ?, ?, ?, ?);
    """
    for session, teams in tqdm(
        past_team_lists().items(),
        ascii=True,
        desc="Populates teams        ",
        ncols=80,
        unit_scale=True,
    ):
        for team in teams:
            database.execute(
                sql,
                (
                    team.name,
                    team.short_name,
                    session,
                    team.id,
                    team.strength,
                ),
            )


def populate_players(session: database.SESSIONS = database.CURRENT_SESSION) -> None:
    """Populates the database with player data for the specified session."""
    sql = """
        INSERT INTO player(
            webname,
            name,
            price,
            news,
            team_id
        ) VALUES (
            ?, ?, ?, ?,
            (SELECT id FROM team WHERE session = ? AND web_team_id = ?)
        );
    """
    for ele in tqdm(
        bootstrap()["elements"],
        ascii=True,
        desc="Populate players       ",
        ncols=80,
        unit_scale=True,
    ):
        database.execute(
            sql,
            (
                ele["web_name"],
                f'{ele["first_name"]} {ele["second_name"]}',
                ele["now_cost"],
                ele["news"],
                session,
                ele["team"],
            ),
        )


def populate_games() -> None:
    """Populates the database with game data, including historic and upcoming games."""
    game_sql = """
        INSERT INTO game (
            session,
            upcoming,
            is_home,

            kickoff,
            minutes,
            points,

            position,
            player_id,
            team,
            opponent,

            selected
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?,
            ?,
            (SELECT id FROM team WHERE session = ? AND name = ?),
            (SELECT id FROM team WHERE session = ? AND name = ?),
            ?
        );
    """
    for session, games in past_game_lists().items():
        to_insert = []
        for fixture in tqdm(
            games,
            ascii=True,
            desc=f"Populate games: {session}",
            ncols=80,
            unit_scale=True,
        ):
            historic = structures.HistoricGame.model_validate(fixture)
            if pid := player_id_fuzzer(historic.name):
                to_insert.append(
                    (
                        session,
                        False,
                        historic.was_home,
                        historic.kickoff_time,
                        historic.minutes,
                        historic.total_points,
                        historic.position,
                        pid,
                        session,
                        historic.team,
                        session,
                        past_team_lookup(historic.opponent_team, session),
                        historic.selected,
                    ),
                )
        database.executemany(game_sql, tuple(to_insert))

    now = now_tz_utc()
    upcoming_games: list[int] = [
        e["id"] for e in bootstrap()["events"] if dtparser(e["deadline_time"]) > now
    ]

    jobs = list[concurrent.futures.Future]()

    def pooled_summary(
        id: int,
        fullname: str,
        team: str,
    ) -> tuple[dict, str, str]:
        return summary(id)["fixtures"], fullname, team

    with concurrent.futures.ThreadPoolExecutor() as pool:
        for ele in bootstrap()["elements"]:
            jobs.append(
                pool.submit(
                    pooled_summary,
                    ele["id"],
                    " ".join((ele["first_name"], ele["second_name"])),
                    upcoming_team_id_to_name(ele["team"]),
                )
            )

        for done in tqdm(
            concurrent.futures.as_completed(jobs),
            ascii=True,
            desc="Populate upcoming games",
            ncols=80,
            total=len(jobs),
            unit_scale=True,
        ):
            fixtures, fullname, team = done.result()
            for fixture in fixtures:
                upcoming = structures.UpcommingGame.model_validate(fixture)
                if not upcoming.event_name:
                    continue

                if upcoming.event in upcoming_games:
                    team_h = upcoming_team_id_to_name(upcoming.team_h)
                    team_a = upcoming_team_id_to_name(upcoming.team_a)
                    is_home = team == team_h
                    opponent = list({team, team_a, team_h} - {team})[0]
                    database.execute(
                        game_sql,
                        (
                            database.CURRENT_SESSION,
                            True,
                            is_home,
                            upcoming.kickoff_time,
                            None,
                            None,
                            upcoming_position(fullname),
                            player_id_fuzzer(fullname),
                            database.CURRENT_SESSION,
                            team,
                            database.CURRENT_SESSION,
                            opponent,
                            -1,
                        ),
                    )


@functools.cache
def upcoming_team_id_to_name(id: int) -> str:
    """Converts a team's ID to its name for upcoming games."""
    for item in bootstrap()["teams"]:
        if id == item["id"]:
            return item["name"]
    raise ValueError(f"No team name: {id}")


@functools.cache
def upcoming_position(name: str) -> database.POSITIONS:
    """Determines the position of a player based on their name for upcoming games."""
    for element in bootstrap()["elements"]:
        if f'{element["first_name"]} {element["second_name"]}' == name:
            element_type = bootstrap()["element_types"][element["element_type"] - 1]
            return element_type["singular_name_short"]
    raise ValueError(f"No player named: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="Populator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.parse_args()

    nuke_database()
    initialize_database()
    populate_teams()
    populate_players()
    populate_games()


if __name__ == "__main__":
    main()
