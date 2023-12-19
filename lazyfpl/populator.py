import csv
import datetime
import argparse
import functools
import io
import traceback
import urllib.parse as up

import pydantic
import pytz
import requests
from dateutil.parser import parse as dtparser
from tqdm.std import tqdm

from lazyfpl import conf, database, structures


def now_tz_utc() -> datetime.datetime:
    return datetime.datetime.now(tz=pytz.utc)


@functools.cache
def bootstrap() -> dict:
    return requests.get(
        "https://fantasy.premierleague.com/api/bootstrap-static/"
    ).json()


@functools.cache
def summary(id: int) -> dict:
    assert isinstance(id, int)
    return requests.get(
        f"https://fantasy.premierleague.com/api/element-summary/{id}/"
    ).json()


@functools.cache
def db_name_pid() -> dict[str, int]:
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
def player_id_fuzzer(name: str) -> int:
    for dname, pid in db_name_pid().items():
        if dname.casefold() == name.casefold():
            return pid
        if all(n in dname.casefold() for n in name.casefold().split()):
            return pid
        if all(n in name.casefold() for n in dname.casefold().split()):
            return pid

    raise KeyError(name)


def session_from_url(url: str) -> str:
    return up.urlparse(url).path.split("/")[5]


@functools.cache
def past_team_lists() -> dict[str, list["structures.Team"]]:
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
    assert isinstance(tid, int)
    for team in past_team_lists()[session]:
        if team.id == tid:
            return team.name
    raise ValueError(f"No match: {tid} / {session}.")


@functools.cache
def past_game_lists() -> dict[str, list[dict]]:
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
    database.execute(
        """
        CREATE TABLE team (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            web_team_id INTEGER NOT NULL,
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
            FOREIGN KEY(opponent) REFERENCES team(id),
            FOREIGN KEY(player_id) REFERENCES player(id),
            FOREIGN KEY(team) REFERENCES team(id)
        );
    """
    )


def nuke_database() -> None:
    database.execute("""DROP TABLE game;""")
    database.execute("""DROP TABLE player;""")
    database.execute("""DROP TABLE team;""")


def populate_teams() -> None:
    sql = """
        INSERT INTO team (
            name,
            session,
            web_team_id,
            strength_attack_away,
            strength_attack_home,
            strength_defence_away,
            strength_defence_home,
            strength_overall_away,
            strength_overall_home
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    for session, teams in past_team_lists().items():
        for team in teams:
            database.execute(
                sql,
                (
                    team.name,
                    session,
                    team.id,
                    team.strength_attack_away,
                    team.strength_attack_home,
                    team.strength_defence_away,
                    team.strength_defence_home,
                    team.strength_overall_away,
                    team.strength_overall_home,
                ),
            )


def populate_players(session: database.SESSIONS = database.CURRENT_SESSION) -> None:
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
        bar_format="{percentage:3.0f}% | {bar:20} {r_bar}",
        unit_divisor=1_000,
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
            opponent
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?,
            ?,
            (SELECT id FROM team WHERE session = ? AND name = ?),
            (SELECT id FROM team WHERE session = ? AND name = ?)
        );
    """
    no_pid = set[str]()  # Print once per player name, avoid cli-spam.
    for session, games in past_game_lists().items():
        for game in tqdm(
            games,
            ascii=True,
            bar_format="{percentage:3.0f}% | {bar:20} {r_bar}",
            unit_divisor=1_000,
            unit_scale=True,
        ):
            # Dafuq pydantic?!
            game.pop(None, None)

            try:
                historic = structures.HistoricGame.model_validate(game)
            except pydantic.ValidationError as e:
                if conf.debug:
                    traceback.print_exception(e)
                continue

            try:
                pid = player_id_fuzzer(historic.name)
            except KeyError as e:
                if conf.debug and historic.name not in no_pid:
                    traceback.print_exception(e)
                no_pid.add(historic.name)
                continue

            try:
                database.execute(
                    game_sql,
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
                    ),
                )
            except database.sqlite3.IntegrityError as e:
                # The player does not play this year.
                if conf.debug:
                    traceback.print_exception(e)
                continue

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

    now = now_tz_utc()
    upcoming_games: list[int] = [
        e["id"] for e in bootstrap()["events"] if dtparser(e["deadline_time"]) > now
    ]
    for ele in tqdm(
        bootstrap()["elements"],
        ascii=True,
        bar_format="{percentage:3.0f}% | {bar:20} {r_bar}",
        unit_divisor=1_000,
        unit_scale=True,
    ):
        fullname = f'{ele["first_name"]} {ele["second_name"]}'
        team = upcoming_team_id_to_name(ele["team"])
        for game in summary(ele["id"])["fixtures"]:
            try:
                upcoming = structures.UpcommingGame.model_validate(game)
            except pydantic.ValidationError as e:
                if conf.debug:
                    traceback.print_exception(e)
                continue

            # A past game, data allready logged.
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
                    ),
                )


@functools.cache
def upcoming_team_id_to_name(id: int) -> str:
    for item in bootstrap()["teams"]:
        if id == item["id"]:
            return item["name"]
    raise ValueError(f"No team name: {id}")


@functools.cache
def upcoming_position(name: str) -> database.POSITIONS:
    for element in bootstrap()["elements"]:
        if f'{element["first_name"]} {element["second_name"]}' == name:
            element_type = bootstrap()["element_types"][element["element_type"] - 1]
            return element_type["singular_name_short"]
    raise ValueError(f"No player named: {name}")


def main():
    parser = argparse.ArgumentParser(
        prog="Populator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--fresh", action="store_true")
    parsed = parser.parse_args()

    if parsed.fresh:
        nuke_database()

    initialize_database()
    populate_teams()
    populate_players()
    populate_games()


if __name__ == "__main__":
    main()
