from functools import wraps
import re
from types import GeneratorType

from pyromancer.objects import Match


class command(object):

    def __init__(self, pattern, *args, **kwargs):
        self.pattern = re.compile(pattern)

    def __call__(self, fn):

        @wraps(fn)
        def wrapper(*fn_args, **fn_kwargs):
            return fn(*fn_args, **fn_kwargs)

        wrapper.command = self
        self.function = wrapper
        return wrapper

    def match(self, line, connection):
        if not line.usermsg:
            return

        m = re.search(self.pattern, line.full_msg)
        if not m:
            return

        match = Match(m, line, connection)
        result = self.function(match)

        if isinstance(result, (list, GeneratorType)):
            messages = result
        elif isinstance(result, tuple):
            messages = [result]
        else:
            messages = []

        for msg in messages:
            if isinstance(msg, tuple):
                msg, *args, kwargs = msg

                # If the reuslt is (msg, positional argument,), make sure it
                # still works correctly as expected for the formatting.
                if not isinstance(kwargs, dict):
                    args.append(kwargs)
                    kwargs = {}
            else:
                args, kwargs = [], {}

            match.msg(msg, *args, **kwargs)
