# ruff: noqa: E501
from __future__ import annotations

import functools
import pathlib
import sqlite3

from lazyfpl import conf, structures


@functools.cache
def connect(file: pathlib.Path = conf.db) -> sqlite3.Connection:
    """Establishes a SQLite database connection using the provided file path."""
    return sqlite3.connect(file)


def execute(sql: str, parameters: tuple = ()) -> list[dict]:
    """Executes a SQL query and returns the result as a list of dictionaries."""
    with connect() as connection:
        cursor = connection.execute(sql, parameters)
        if desc := [x[0] for x in cursor.description or []]:
            return [dict(zip(desc, row)) for row in cursor.fetchall()]
        return []


def executemany(sql: str, parameters: tuple = ()) -> list[dict]:
    """Executes a SQL query and returns the result as a list of dictionaries."""
    with connect() as connection:
        cursor = connection.executemany(sql, parameters)
        if desc := [x[0] for x in cursor.description or []]:
            return [dict(zip(desc, row)) for row in cursor.fetchall()]
        return []


@functools.cache
def games() -> list[structures.Game]:
    """Retrieves a list of Game objects representing football games from the database."""
    rows = execute(
        """
        SELECT
            g.gw,
            g.is_home,
            g.kickoff,
            g.minutes,
            g.player_id,
            g.points,
            g.position,
            g.selected,
            g.session,
            g.upcoming,
            p.name            AS player,
            p.news            AS news,
            p.webname         AS webname,
            t.name            AS team,
            t.strength        AS team_strength,
            t.short_name      AS team_short,
            opp.name          AS opponent,
            opp.strength      AS opponent_strength,
            opp.short_name    AS opponent_short
        FROM
            game g
        JOIN
            player p ON p.id = g.player_id
        JOIN
            team t ON t.id = g.team
        JOIN
            team opp ON opp.id = g.opponent
    """
    )

    return [structures.Game.model_validate(row) for row in rows]


def price(pid: int) -> int:
    """Fetches and returns the price of a player based on their ID."""
    rows = execute(
        """
        SELECT
            price
        FROM
            player
        WHERE
            id = ?
    """,
        (pid,),
    )
    return rows[0]["price"]


def webname(pid: int) -> str:
    """Retrieves and returns the web name of a player based on their ID."""
    rows = execute(
        """
        SELECT
            webname
        FROM
            player
        WHERE
            id = ?
    """,
        (pid,),
    )
    return rows[0]["webname"]


def save_model(player_id: int, model: bytes) -> None:
    """Saves a machine learning model to the database for a given player ID."""
    execute(
        """
        UPDATE
            player
        SET
            model = ?
        WHERE
            id = ?
    """,
        (model, player_id),
    )


def load_model(player_id: int) -> bytes:
    """Loads and returns a machine learning model from the database for a given player ID."""
    return execute(
        """
        SELECT
            model
        FROM
            player
        WHERE
            id =?
    """,
        (player_id,),
    )[0]["model"]


@functools.cache
def points() -> structures.Summary:
    """SampleSummary of points scored in games."""
    return structures.Summary.fromiter(
        [
            row["points"]
            for row in execute(
                """
        SELECT
            points
        FROM
            game
        WHERE
            points is not null
    """
            )
        ]
    )


@functools.cache
def minutes() -> structures.Summary:
    """SampleSummary of minutes played in games."""
    return structures.Summary.fromiter(
        [
            row["minutes"]
            for row in execute(
                """
        SELECT
            minutes
        FROM
            game
        WHERE
            minutes is not null
    """
            )
        ]
    )
