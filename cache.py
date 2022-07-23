import datetime
import functools
import hashlib
import inspect
import pathlib
import pickle
import typing


def make_key(obj: typing.Any) -> str:

    if isinstance(obj, list):
        return make_key("".join(make_key(v) for v in obj))

    if isinstance(obj, tuple):
        return make_key("".join(make_key(v) for v in obj))

    if isinstance(obj, dict):
        return make_key("".join(f"{make_key(k)}{make_key(v)}" for k, v in obj.items()))

    return hashlib.sha1(str(obj).encode()).hexdigest()


def fcache(ttl: datetime.timedelta):
    def outer(fn):

        default_args_hsh = make_key(
            {
                k: v.default
                for k, v in inspect.signature(fn).parameters.items()
                if v.default is not inspect.Parameter.empty
            }
        )
        source_hsh = make_key(inspect.getsource(fn))
        folder = pathlib.Path(__file__).parent / ".fcache"

        @functools.cache
        def inner(*args, **kw):

            key = make_key(
                "".join(
                    (
                        make_key(args),
                        make_key(kw),
                        default_args_hsh,
                        source_hsh,
                    )
                )
            )
            sub = folder / key[0:2] / key[2:4] / key[4:6]
            cache = sub / f"{key}.pkl"

            if not sub.exists():
                sub.mkdir(parents=True, exist_ok=True)

            if cache.exists() and ttl > datetime.timedelta(seconds=0):

                with cache.open("rb") as fd:
                    cached = pickle.load(fd)

                if cached["exp"] >= datetime.datetime.now():
                    return cached["rv"]

            rv = fn(*args, *kw)

            with cache.open("wb") as fd:
                pickle.dump({"exp": datetime.datetime.now() + ttl, "rv": rv}, fd)

            return rv

        return inner

    return outer
