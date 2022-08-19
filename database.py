import functools
import os
import pathlib
import sqlite3
import datetime
import typing as T

import pydantic


class Game(pydantic.BaseModel):
    is_home: bool
    kickoff: datetime.datetime
    minutes: T.Optional[int]
    opponent: str
    player_id: int
    player: str
    points: T.Optional[int]
    position: T.Literal["GKP", "DEF", "MID", "FWD"]
    session: T.Literal["2021-22", "2022-23"]
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


def dbfile(
    file: str = os.environ.get("FPL_DATABASE", "database.sqlite3")
) -> pathlib.Path:
    return pathlib.Path(file)


@functools.cache
def connect(file: pathlib.Path = dbfile()):
    return sqlite3.connect(file)


def execute(sql: str, parameters: tuple = tuple()) -> list[dict]:
    with connect() as conn:
        cursor = conn.execute(sql, parameters)
        if desc := [x[0] for x in cursor.description or []]:
            return [dict(zip(desc, row)) for row in cursor.fetchall()]
        return []


@functools.cache
def games() -> list[Game]:
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
            (select webname from player where id = game.player_id)                 as webname,
            (select name from player where id = game.player_id)                    as player,
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

    return [Game.parse_obj(row) for row in rows]


def price(pid: int) -> int:
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