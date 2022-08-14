import functools
import os
import pathlib
import sqlite3


def dbfile(
    file: str = os.environ.get("FPL_DATABASE", "database.sqlite3")
) -> pathlib.Path:
    return pathlib.Path(file)


@functools.cache
def connect(file: pathlib.Path = dbfile()):
    return sqlite3.connect(file)


def execute(sql: str, parameters: tuple = tuple()) -> None:
    with connect() as conn:
        conn.execute(sql, parameters)
