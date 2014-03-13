from functools import wraps
import re
from types import GeneratorType

from pyromancer.objects import Match


class command(object):

    def __init__(self, patterns, *args, **kwargs):
        if not isinstance(patterns, list):
            patterns = [patterns]

        self.patterns = [re.compile(p) for p in patterns]

        self.use_prefix = kwargs.get('prefix', True)

    def __call__(self, fn):

        @wraps(fn)
        def wrapper(*fn_args, **fn_kwargs):
            return fn(*fn_args, **fn_kwargs)

        wrapper.command = self
        self.function = wrapper
        return wrapper

    def match(self, line, connection, prefix):
        if not line.usermsg:
            return

        if self.use_prefix:
            if not line.full_msg.startswith(prefix):
                return

            # todo: add support for tuple of prefixes; this line currently
            # prohibits that support.
            input = line.full_msg[len(prefix):]
        else:
            input = line.full_msg

        m = None
        for pattern in self.patterns:
            m = re.search(pattern, input)

            if m:
                break

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

                # If the result is (msg, positional argument,), make sure it
                # still works correctly as expected for the formatting.
                if not isinstance(kwargs, dict):
                    args.append(kwargs)
                    kwargs = {}
            else:
                args, kwargs = [], {}

            match.msg(msg, *args, **kwargs)
