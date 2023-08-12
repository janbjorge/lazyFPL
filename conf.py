import os
import typing

import pydantic


class _Env(pydantic.BaseModel):
    backtrace: int = pydantic.Field(alias="FPL_BACKTRACE", default=3)
    debug: bool = pydantic.Field(alias="FPL_DEBUG", default=False)
    lookahead: int = pydantic.Field(alias="FPL_LOOKAHEAD", default=3)
    teamid: str = pydantic.Field(alias="FPL_TEAMID", default="4270770")


_env = _Env.parse_obj(os.environ)

backtrace: typing.Final = _env.backtrace
debug: typing.Final = _env.debug
lookahead: typing.Final = _env.lookahead
teamid: typing.Final = _env.teamid
