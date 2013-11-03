from functools import wraps
import re


def command(match, *args, **kwargs):
    match = re.compile(match)

    def decorator(fn):

        @wraps(fn)
        def wrapper(*fn_args, **fn_kwargs):
            fn(*fn_args, **fn_kwargs)

        wrapper.match = match
        return wrapper

    return decorator
