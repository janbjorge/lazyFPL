import os
import typing

import pydantic


class _Env(pydantic.BaseModel):
    backtrace: int = pydantic.Field(alias="FPL_BACKTRACE", default=3)
    debug: bool = pydantic.Field(alias="FPL_DEBUG", default=False)
    lookahead: int = pydantic.Field(alias="FPL_LOOKAHEAD", default=3)
    profile: str = pydantic.Field(alias="FPL_PROFILE", default="")
    teamid: str = pydantic.Field(alias="FPL_TEAMID", default="4270770")


backtrace: typing.Final = _Env.parse_obj(os.environ).backtrace
debug: typing.Final = _Env.parse_obj(os.environ).debug
lookahead: typing.Final = _Env.parse_obj(os.environ).lookahead
profile: typing.Final = _Env.parse_obj(os.environ).profile
teamid: typing.Final = _Env.parse_obj(os.environ).teamid
