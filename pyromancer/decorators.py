import re
from types import GeneratorType

from pyromancer.objects import Match


class command(object):

    def __init__(self, patterns, *args, **kwargs):
        if not isinstance(patterns, list):
            patterns = [patterns]

        flags = kwargs.get('flags', 0)
        self.patterns = [re.compile(p, flags) if isinstance(p, str) else p
                         for p in patterns]

        self.use_prefix = kwargs.get('prefix', True)
        self.raw = kwargs.get('raw', False)

    def __call__(self, fn):
        fn.command = self
        self.function = fn
        return fn

    def match(self, line, connection, settings):
        m = self.matches(line, settings)

        if m:
            match = Match(m, line, connection)
            result = self.function(match)

            if result is not None:
                self.send_messages(result, match)

    def matches(self, line, settings):
        if not line.usermsg and not self.raw:
            return

        input = line.full_msg if not self.raw else line.raw

        if self.use_prefix:
            if not input.startswith(settings.command_prefix):
                return

            # todo: add support for tuple of prefixes; this line currently
            # prohibits that support.
            input = input[len(settings.command_prefix):]

        for pattern in self.patterns:
            m = re.search(pattern, input)

            if m:
                return m

    def send_messages(self, result, match):
        if isinstance(result, (list, GeneratorType)):
            messages = result
        else:
            messages = [result]

        for msg in messages:
            if isinstance(msg, tuple):
                last = len(msg) - 1
                msg, args, kwargs = msg[0], list(msg[1:last]), msg[last]

                # If the result is (msg, positional argument,), make sure it
                # still works correctly as expected for the formatting.
                if not isinstance(kwargs, dict):
                    args.append(kwargs)
                    kwargs = {}
            else:
                args, kwargs = [], {}

            match.msg(msg, *args, **kwargs)
