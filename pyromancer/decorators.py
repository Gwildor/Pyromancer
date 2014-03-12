from functools import wraps
import re

from pyromancer.objects import Match


class command(object):

    def __init__(self, pattern, *args, **kwargs):
        self.pattern = re.compile(pattern)

    def __call__(self, fn):

        @wraps(fn)
        def wrapper(*fn_args, **fn_kwargs):
            fn(*fn_args, **fn_kwargs)

        wrapper.command = self
        self.function = wrapper
        return wrapper

    def match(self, line, connection):
        if not line.usermsg:
            return

        m = re.search(self.pattern, line.full_msg)
        if m:
            match = Match(m, line, connection)
            self.function(match)
