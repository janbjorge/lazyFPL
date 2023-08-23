import os
import typing

import pydantic


class _Env(pydantic.BaseModel):
    backtrace: int = pydantic.Field(alias="FPL_BACKTRACE", default=3)
    debug: bool = pydantic.Field(alias="FPL_DEBUG", default=False)
    lookahead: int = pydantic.Field(alias="FPL_LOOKAHEAD", default=3)
    teamid: str = pydantic.Field(alias="FPL_TEAMID", default="4270770")
    upsample: int = pydantic.Field(alias="FPL_UPSAMLE", default=100)


backtrace: typing.Final = _Env.parse_obj(os.environ).backtrace
debug: typing.Final = _Env.parse_obj(os.environ).debug
lookahead: typing.Final = _Env.parse_obj(os.environ).lookahead
teamid: typing.Final = _Env.parse_obj(os.environ).teamid
upsample: typing.Final = _Env.parse_obj(os.environ).upsample
