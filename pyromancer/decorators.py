import re

from pyromancer import utils
from pyromancer.exceptions import CommandException
from pyromancer.objects import Match, Timer


class command(object):

    def __init__(self, patterns=None, *args, **kwargs):
        if patterns is None:
            patterns = []

        if not isinstance(patterns, list):
            patterns = [patterns]

        flags = kwargs.get('flags', 0)
        self.patterns = [re.compile(p, flags) if isinstance(p, str) else p
                         for p in patterns]

        self.use_prefix = kwargs.get('prefix', True)
        self.raw = kwargs.get('raw', False)
        self.code = kwargs.get('code')
        self.command = kwargs.get('command')

        if self.code is not None and not isinstance(self.code, int):
            raise CommandException('The code argument must be an integer.')

        if self.code or self.command:
            self.raw = True

        if not self.code and not self.command and len(patterns) == 0:
            raise CommandException(
                'Either a (a list of) pattern(s), a three-digit code or an'
                'all-capital command must be specified as first argument for '
                'the command decorator.')

    def __call__(self, fn):
        fn.command = self
        self.function = fn
        return fn

    def match(self, line, timers, connection, settings):
        m = self.matches(line, settings)

        if m:
            match = Match(m, line, connection, settings)
            result = self.function(match)

            if result is not None:
                self.send_messages(result, match, timers)

    def matches(self, line, settings):
        if not line.usermsg and not self.raw:
            return

        if self.code and getattr(line, 'code', None) == self.code:
            return True

        if self.command and getattr(line, 'command', None) == self.command:
            return True

        input = line.full_msg if not self.raw else line.raw

        if self.use_prefix and settings.command_prefix:
            if not input.startswith(settings.command_prefix):
                return

            # todo: add support for tuple of prefixes; this line currently
            # prohibits that support.
            input = input[len(settings.command_prefix):]

        for pattern in self.patterns:
            m = re.search(pattern, input)

            if m:
                return m

    def send_messages(self, result, match, timers):
        for r in utils.process_messages(result):
            if isinstance(r, Timer):
                timers.append(r)
            else:
                match.msg(r[0], *r[1], **r[2])


class timer(object):

    def __init__(self, *args, **kwargs):
        self.initargs = args
        self.initkwargs = kwargs

    def __call__(self, fn):
        fn.timer = Timer(*self.initargs, msg_or_command=fn, **self.initkwargs)
        return fn
