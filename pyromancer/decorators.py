from functools import wraps
import re


class command(object):

    def __init__(self, pattern, *args, **kwargs):
        self.pattern = re.compile(pattern)

    def __call__(self, fn):

        @wraps(fn)
        def wrapper(*fn_args, **fn_kwargs):
            fn(*fn_args, **fn_kwargs)

        wrapper.command = self
        return wrapper

    def match(self, line):
        if not line.usermsg:
            return

        return re.search(self.pattern, line.full_msg)
