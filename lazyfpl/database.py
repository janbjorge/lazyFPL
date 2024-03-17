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
        select
            gw,
            is_home,
            kickoff,
            minutes,
            player_id,
            points,
            position,
            selected,
            session,
            upcoming,
            (select name from player where id = game.player_id)                    as player,
            (select news from player where id = game.player_id)                    as news,
            (select webname from player where id = game.player_id)                 as webname,
            (select name from team where team = team.id)                           as team,
            (select strength from team where team.id = game.team)                  as team_strength,
            (select short_name from team where team.id = game.team)                as team_short,
            (select name from team where opponent = team.id)                       as opponent,
            (select strength from team where team.id = game.opponent)              as opponent_strength,
            (select short_name from team where opponent = team.id)                 as opponent_short
        from
            game
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
