from __future__ import annotations

import pathlib
import typing

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class _Env(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    backtrace: int = Field(
        alias="FPL_BACKTRACE",
        default=3,
        gt=0,
    )
    db: pathlib.Path = Field(
        alias="FPL_DATABASE",
        default=pathlib.Path(__file__).parent.parent
        / pathlib.Path(".database.sqlite3"),
    )
    debug: bool = Field(
        alias="FPL_DEBUG",
        default=False,
    )
    lookahead: int = Field(
        alias="FPL_LOOKAHEAD",
        default=3,
        gt=0,
    )
    profile: str = Field(
        alias="FPL_PROFILE",
        default="",
    )
    sessionid: str = Field(
        alias="FPL_SESSIONID",
        default="",
    )
    tabulate_format: str = Field(
        alias="FPL_TABULATE_FORMAT",
        default="tsv",
    )
    teamid: str = Field(
        alias="FPL_TEAMID",
        default="",
    )


backtrace: typing.Final = _Env().backtrace
db: typing.Final = _Env().db
debug: typing.Final = _Env().debug
lookahead: typing.Final = _Env().lookahead
profile: typing.Final = _Env().profile
sessionid: typing.Final = _Env().sessionid
tabulate_format: typing.Final = _Env().tabulate_format
teamid: typing.Final = _Env().teamid
