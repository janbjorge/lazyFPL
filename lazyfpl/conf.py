from __future__ import annotations

import os
import pathlib
import typing

import pydantic


class _Env(pydantic.BaseModel):
    backtrace: int = pydantic.Field(
        alias="FPL_BACKTRACE",
        default=3,
        gt=0,
    )
    db: pathlib.Path = pydantic.Field(
        alias="FPL_DATABASE",
        default=pathlib.Path(__file__).parent.parent
        / pathlib.Path(".database.sqlite3"),
    )
    debug: bool = pydantic.Field(
        alias="FPL_DEBUG",
        default=False,
    )
    lookahead: int = pydantic.Field(
        alias="FPL_LOOKAHEAD",
        default=3,
        gt=0,
    )
    profile: str = pydantic.Field(
        alias="FPL_PROFILE",
        default="",
    )
    tabulate_format: str = pydantic.Field(
        alias="FPL_TABULATE_FORMAT",
        default="tsv",
    )
    teamid: str = pydantic.Field(
        alias="FPL_TEAMID",
        default="",
    )


backtrace: typing.Final = _Env.model_validate(os.environ).backtrace
db: typing.Final = _Env.model_validate(os.environ).db
debug: typing.Final = _Env.model_validate(os.environ).debug
lookahead: typing.Final = _Env.model_validate(os.environ).lookahead
profile: typing.Final = _Env.model_validate(os.environ).profile
tabulate_format: typing.Final = _Env.model_validate(os.environ).tabulate_format
teamid: typing.Final = _Env.model_validate(os.environ).teamid
