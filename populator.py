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
    name = name.lower()
    for dname, pid in db_name_pid().items():
        dname = dname.lower()
        if dname == name:
            pid
        if all(n in dname for n in name.split()):
            return pid
        if all(n in name for n in dname.split()):
            return pid
    raise KeyError(name)


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


def structure() -> None:
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
                    team["name"],
                    session,
                    team["id"],
                    team["strength_attack_away"],
                    team["strength_attack_home"],
                    team["strength_defence_away"],
                    team["strength_defence_home"],
                    team["strength_overall_away"],
                    team["strength_overall_home"],
                ),
            )


def populate_players(session: T.Literal["2022-23"] = "2022-23") -> None:
    sql = """
        INSERT INTO player(
            webname,
            name,
            price,
            team_id
        ) VALUES (
            ?, ?, ?,
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
                session,
                ele["team"],
            ),
        )


def populate_games(current_session="2022-23") -> None:
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
    for session, games in past_game_lists().items():
        for game in tqdm(
            games,
            ascii=True,
            bar_format="{percentage:3.0f}% | {bar:20} {r_bar}",
            unit_divisor=1_000,
            unit_scale=True,
        ):
            try:
                pid = player_id_fuzzer(game["name"])
            except KeyError:
                continue
            try:
                database.execute(
                    game_sql,
                    (
                        session,
                        False,
                        game["was_home"],
                        dt_parser(game["kickoff_time"]).timestamp(),
                        game["minutes"],
                        game["total_points"],
                        game["position"],
                        pid,
                        session,
                        game["team"],
                        session,
                        past_team_lookup(int(game["opponent_team"]), session),
                    ),
                )
            except database.sqlite3.IntegrityError:
                # The player does not play this year.
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

    upcoming_games = set[int](
        e["id"] for e in bootstrap()["events"] if not e["chip_plays"]
    )
    for ele in tqdm(
        bootstrap()["elements"],
        ascii=True,
        bar_format="{percentage:3.0f}% | {bar:20} {r_bar}",
        unit_divisor=1_000,
        unit_scale=True,
    ):
        fullname = f'{ele["first_name"]} {ele["second_name"]}'
        if ele["news"]:
            continue
        team = upcoming_team_id_to_name(ele["team"])
        for upcoming in summary(ele["id"])["fixtures"]:
            # A past game, data allready logged.
            if upcoming["event"] in upcoming_games:
                team_h = upcoming_team_id_to_name(upcoming["team_h"])
                team_a = upcoming_team_id_to_name(upcoming["team_a"])
                is_home = team == team_h
                opponent = list({team, team_a, team_h} - {team})[0]
                database.execute(
                    game_sql,
                    (
                        current_session,
                        True,
                        is_home,
                        dt_parser(upcoming["kickoff_time"]).timestamp(),
                        None,
                        None,
                        upcoming_position(fullname),
                        player_id_fuzzer(fullname),
                        current_session,
                        team,
                        current_session,
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
def upcoming_position(name: str) -> T.Literal["GKP", "DEF", "MID", "FWD"]:
    for element in bootstrap()["elements"]:
        if f'{element["first_name"]} {element["second_name"]}' == name:
            element_type = bootstrap()["element_types"][element["element_type"] - 1]
            return element_type["singular_name_short"]
    raise ValueError(f"No player named: {name}")


if __name__ == "__main__":
    structure()
    populate_teams()
    populate_players()
    populate_games()