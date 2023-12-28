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


@dataclasses.dataclass(frozen=True)
class SampleSummary:
    mean: float
    std: float
    variance: float

    @staticmethod
    def fromiter(values: T.Iterable[float]) -> "SampleSummary":
        """Creates a SampleSummary from an iterable of float values."""
        return SampleSummary(
            mean=statistics.mean(values),
            std=statistics.stdev(values),
            variance=statistics.variance(values),
        )

    def normalize(self, value: float) -> float:
        """Normalizes a value based on the mean and variance of the sample."""
        return (value - self.mean) / self.variance


@dataclasses.dataclass(frozen=True)
class Strenghts:
    strength_attack_away: SampleSummary
    strength_attack_home: SampleSummary
    strength_defence_away: SampleSummary
    strength_defence_home: SampleSummary
    strength_overall_away: SampleSummary
    strength_overall_home: SampleSummary


class Game(pydantic.BaseModel):
    is_home: bool
    kickoff: datetime.datetime
    minutes: T.Optional[int]
    news: str
    opponent: str
    player_id: int
    player: str
    points: T.Optional[int]
    position: POSITIONS
    session: SESSIONS
    team: str
    upcoming: bool
    webname: str
    team_strength_attack_home: int
    team_strength_attack_away: int
    team_strength_defence_home: int
    team_strength_defence_away: int
    team_strength_overall_home: int
    team_strength_overall_away: int
    opponent_strength_attack_home: int
    opponent_strength_attack_away: int
    opponent_strength_defence_home: int
    opponent_strength_defence_away: int
    opponent_strength_overall_home: int
    opponent_trength_overall_away: int


@functools.cache
def connect(file: pathlib.Path = conf.db) -> sqlite3.Connection:
    """Establishes a SQLite database connection using the provided file path."""
    return sqlite3.connect(file)


def execute(sql: str, parameters: tuple = ()) -> list[dict]:
    """Executes a SQL query and returns the result as a list of dictionaries."""
    with connect() as conn:
        cursor = conn.execute(sql, parameters)
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
            (select name from player where id = game.player_id)                    as player,
            (select news from player where id = game.player_id)                    as news,
            (select webname from player where id = game.player_id)                 as webname,
            (select name from team where opponent = team.id)                       as opponent,
            (select name from team where team = team.id)                           as team,
            (select strength_attack_home from team where team.id = game.team)      as team_strength_attack_home,
            (select strength_attack_away from team where team.id = game.team)      as team_strength_attack_away,
            (select strength_defence_home from team where team.id = game.team)     as team_strength_defence_home,
            (select strength_defence_away from team where team.id = game.team)     as team_strength_defence_away,
            (select strength_overall_home from team where team.id = game.team)     as team_strength_overall_home,
            (select strength_overall_away from team where team.id = game.team)     as team_strength_overall_away,
            (select strength_attack_home from team where team.id = game.opponent)  as opponent_strength_attack_home,
            (select strength_attack_away from team where team.id = game.opponent)  as opponent_strength_attack_away,
            (select strength_defence_home from team where team.id = game.opponent) as opponent_strength_defence_home,
            (select strength_defence_away from team where team.id = game.opponent) as opponent_strength_defence_away,
            (select strength_overall_home from team where team.id = game.opponent) as opponent_strength_overall_home,
            (select strength_overall_away from team where team.id = game.opponent) as opponent_trength_overall_away
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
def points() -> SampleSummary:
    """Caches and returns a SampleSummary of points scored in games."""
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
    return SampleSummary.fromiter(p)


@functools.cache
def minutes() -> SampleSummary:
    """Caches and returns a SampleSummary of minutes played in games."""
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
    return SampleSummary.fromiter(p)


@functools.cache
def strengths() -> Strenghts:
    """Caches and returns a Strenghts object with aggregated team strengths."""
    rows = execute(
        """
        SELECT
            strength_attack_away,
            strength_attack_home,
            strength_defence_away,
            strength_defence_home,
            strength_overall_away,
            strength_overall_home
        FROM
            team
    """
    )
    return Strenghts(
        strength_attack_away=SampleSummary.fromiter(
            [r["strength_attack_away"] for r in rows]
        ),
        strength_attack_home=SampleSummary.fromiter(
            [r["strength_attack_home"] for r in rows]
        ),
        strength_defence_away=SampleSummary.fromiter(
            [r["strength_defence_away"] for r in rows]
        ),
        strength_defence_home=SampleSummary.fromiter(
            [r["strength_defence_home"] for r in rows]
        ),
        strength_overall_away=SampleSummary.fromiter(
            [r["strength_overall_away"] for r in rows]
        ),
        strength_overall_home=SampleSummary.fromiter(
            [r["strength_overall_home"] for r in rows]
        ),
    )
