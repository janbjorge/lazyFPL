import os

import pydantic


class _Env(pydantic.BaseModel):
    debug: bool = pydantic.Field(alias="FPL_DEBUG", default=False)
    lookahead: int = pydantic.Field(alias="FPL_LOOKAHEAD", default=3)
    backtrace: int = pydantic.Field(alias="FPL_BACKTRACE", default=3)


env = _Env.parse_obj(os.environ)
