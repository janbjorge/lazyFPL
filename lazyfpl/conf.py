import os
import typing
import pathlib

import pydantic


class _Env(pydantic.BaseModel):
    backtrace: int = pydantic.Field(
        alias="FPL_BACKTRACE",
        default=3,
        gt=0,
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
    teamid: str = pydantic.Field(
        alias="FPL_TEAMID",
        default="4270770",
    )
    db: pathlib.Path = pydantic.Field(
        alias="FPL_DATABASE",
        default=pathlib.Path(".database.sqlite3"),
    )


backtrace: typing.Final = _Env.model_validate(os.environ).backtrace
db: typing.Final = _Env.model_validate(os.environ).db
debug: typing.Final = _Env.model_validate(os.environ).debug
lookahead: typing.Final = _Env.model_validate(os.environ).lookahead
profile: typing.Final = _Env.model_validate(os.environ).profile
teamid: typing.Final = _Env.model_validate(os.environ).teamid
