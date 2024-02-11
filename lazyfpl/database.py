# ruff: noqa: E501
from __future__ import annotations

import dataclasses
import datetime
import functools
import pathlib
import sqlite3
import statistics
import typing as T

import pydantic

from lazyfpl import conf

SESSIONS = T.Literal["2021-22", "2022-23", "2023-24"]
CURRENT_SESSION = T.get_args(SESSIONS)[-1]
POSITIONS = T.Literal["GKP", "DEF", "MID", "FWD"]


@dataclasses.dataclass
class Summary:
    mean: float
    std: float
    variance: float

    @staticmethod
    def fromiter(values: T.Iterable[float]) -> Summary:
        """Creates a SampleSummary from an iterable of float values."""
        return Summary(
            mean=statistics.mean(values),
            std=statistics.stdev(values),
            variance=statistics.variance(values),
        )

    def unit_variance_normalization(self, value: float) -> float:
        return (value - self.mean) / self.variance


class Game(pydantic.BaseModel):
    is_home: bool
    kickoff: datetime.datetime
    minutes: int | None
    news: str
    opponent: str
    opponent_short: str
    opponent_strength: int
    player_id: int
    player: str
    points: int | None
    position: POSITIONS
    selected: int
    session: SESSIONS
    team: str
    team_short: str
    team_strength: int
    upcoming: bool
    webname: str


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
def games() -> list[Game]:
    """Retrieves a list of Game objects representing football games from the database."""
    rows = execute(
        """
        select
            is_home,
            kickoff,
            minutes,
            points,
            position,
            session,
            upcoming,
            player_id,
            selected,
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

    return [Game.model_validate(row) for row in rows]


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
def points() -> Summary:
    """SampleSummary of points scored in games."""
    p = [
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
    return Summary.fromiter(p)


@functools.cache
def minutes() -> Summary:
    """SampleSummary of minutes played in games."""
    p = [
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
    return Summary.fromiter(p)
