import datetime
import importlib
import re
import socket
import time
from types import GeneratorType

from irc.buffer import DecodingLineBuffer

from pyromancer import utils

_TIMERS = []


class Pyromancer(object):

    def __init__(self, settings_path):
        self.settings = Settings(settings_path)
        self.find_commands()
        self.find_timers()

    def run(self):
        self.connect()
        self.listen()

    def connect(self):
        self.connection = Connection(self.settings.host, self.settings.port,
                                     self.settings.encoding)

        self.online = True
        self.connect_time = datetime.datetime.now()
        self.connection.write('NICK {}\n'.format(self.settings.nick))
        self.connection.write('USER {0} {1} {1} :{2}\n'.format(
            self.settings.nick, self.settings.host, self.settings.real_name))

    def listen(self):
        self.online = True
        ticks = self.settings.ticks

        while self.online:
            self.connection.read()

            for line in self.connection.buffer.lines():
                self.process(line)

            for timer in _TIMERS:
                timer.match(self, self.connection)

            time.sleep(1.0 / ticks)

    def process(self, line):
        line = Line(line)

        if line[0] == 'PING':
            self.connection.write('PONG {}\n'.format(line[1]))

        for c in self.commands:
            c.command.match(line, self.connection, self.settings)

    def find_commands(self):
        self.commands = []

        utils.find_functions(
            self.settings.packages, self.commands, 'commands',
            'disabled_commands', when=lambda f: hasattr(f, 'command'))

    def find_timers(self):
        _TIMERS.clear()

        utils.find_functions(
            self.settings.packages, _TIMERS, 'timers', 'disabled_timers',
            when=lambda f: hasattr(f, 'timer'), ret=lambda f: f.timer)


class Settings(object):

    def __init__(self, path):
        main_settings = importlib.import_module(path)
        self.packages = getattr(main_settings, 'packages', [])
        self.package_settings = {}
        self.package_name, _ = path.split('.', 1)

        if self.package_name not in self.packages:
            self.packages.insert(0, self.package_name)

        for package in self.packages:
            if isinstance(package, tuple):
                package = package[0]

            if package == self.package_name:
                module = main_settings
            else:
                module = importlib.import_module('{}.settings'.format(package))

            self.package_settings[package] = module

        self.global_settings = None
        if 'pyromancer' not in self.packages:
            self.global_settings = importlib.import_module(
                'pyromancer.settings')

    def __getattr__(self, item):
        for package in self.packages:
            if isinstance(package, tuple):
                package = package[0]

            if hasattr(self.package_settings[package], item):
                return getattr(self.package_settings[package], item)

        if hasattr(self.global_settings, item):
            return getattr(self.global_settings, item)

        raise AttributeError('No such setting "{}" found in any of the '
                             'installed packages'.format(item))


class Connection(object):

    def __init__(self, host, port, encoding='utf8'):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.socket.setblocking(False)
        self.encoding = encoding

        self.buffer = DecodingLineBuffer()
        self.buffer.encoding = self.encoding

    def write(self, data):
        self.socket.send('{}\n'.format(data).encode(self.encoding))

    def read(self, bytes=4096):
        try:
            self.buffer.feed(self.socket.recv(bytes))
        except BlockingIOError:
            pass

    def msg(self, target, msg):
        self.write('PRIVMSG {} :{}'.format(target,  msg))


class User(object):
    nick = None
    name = None

    def __init__(self, str):
        if '@' in str:
            self.nick, parts = str.split('!', 1)
            self.name, self.host = parts.split('@', 1)
        else:
            self.host = str

    def __repr__(self):
        return '{0.nick}@{0.host}'.format(self) if self.nick else self.host


class Match(object):
    """
    This class acts as a layer between the code in commands and the other
    objects and should have multiple uses and shortcut functions. An object is
    created for every matching command and is passed on as an argument to the
    command to use. It provides easy access to any captured groups of the
    matching regex.

    Later on, it should provide some utility functions for messaging and other
    things a command may like to do.
    """

    def __init__(self, match, line, connection):
        self.match = match
        self.line = line
        self.connection = connection

    def __getitem__(self, item):
        try:
            return self.match.group(item)
        except IndexError:
            return ''

    def msg(self, message, *args, **kwargs):
        """Shortcut to send a message through the connection.

        This function sends the input message through the connection. A target
        can be defined, else it will send it to the channel or user from the
        input Line, effectively responding on whatever triggered the command
        which calls this function to be called. If raw has not been set to
        True, formatting will be applied using the standard Python Formatting
        Mini-Language, using the additional given args and kwargs, along with
        some additional kwargs, such as the match object to easily access Regex
        matches, color codes and other things.

        http://docs.python.org/3.3/library/string.html#format-string-syntax
        """

        target = kwargs.pop('target', None)
        raw = kwargs.pop('raw', False)

        if not target:
            target = self.line.sender.nick if self.line.pm else \
                self.line.target

        if not raw:
            kw = {
                'm': self,
                'b': chr(2),
                'k': chr(3),
                'u': chr(31),
            }
            kw.update(kwargs)

            try:
                message = message.format(*args, **kw)
            except IndexError:
                if len(args) == 1 and isinstance(args[0], list):
                    # Message might be: msg, [arg1, arg2], kwargs
                    message = message.format(*args[0], **kw)
                else:
                    raise

        self.connection.msg(target, message)

CODE_PATTERN = re.compile(r'\d{3}')


class Line(object):

    def __init__(self, data):
        self.raw = data
        self.datetime = datetime.datetime.now()
        self.parse()

    def __getitem__(self, item):
        try:
            if self.usermsg:
                return self.full_msg.split(' ')[item]
            else:
                return self.parts[item]
        except IndexError:
            return ''

    def __repr__(self):
        return '{0.sender}: {0.full_msg}'.format(self) if self.usermsg else \
            self.raw

    def parse(self):
        self.parts = self.raw.split()
        self.privmsg = self.parts[1] == 'PRIVMSG'
        self.notice = self.parts[1] == 'NOTICE'
        self.usermsg = self.privmsg or self.notice

        if self.usermsg:
            # ":Nick!Name@Host PRIVMSG #Chan :Hello world!"
            self.sender = User(self.parts[0][1:])
            self.target = self.parts[2]
            self.pm = self.target[0] != '#'
            self.full_msg = ' '.join(self.parts[3:])[1:]
        elif CODE_PATTERN.match(self.parts[1]):
            self.code = int(self.parts[1])


class Timer(object):

    def __init__(self, scheduled, msg=None, *args, **kwargs):
        self.scheduled = scheduled
        self.direct = kwargs.pop('direct', False)
        self.remaining = kwargs.pop('count', 0)
        self.function = kwargs.pop('function', None)
        target = kwargs.pop('target', None)

        self.msg_tuple = None
        if target is not None and msg is not None:
            self.msg_tuple = (target, msg, args, kwargs,)

    def match(self, pyromancer, connection):
        if self.matches(pyromancer):
            self.last_time = datetime.datetime.now()
            match = Match(None, None, connection)

            if self.function is not None:
                result = self.function(match)

                if result is not None:
                    self.send_messages(result, match)

            if self.msg_tuple is not None:
                self.send_messages(self.msg_tuple, match)

            if self.remaining > 0:
                self.remaining -= 1

                if self.remaining == 0:
                    _TIMERS.remove(self)

    def matches(self, pyromancer):
        if self.direct:
            self.direct = False
            return True

        next_time = None
        if isinstance(self.scheduled, datetime.datetime):
            next_time = self.scheduled

        if isinstance(self.scheduled, datetime.timedelta):
            if hasattr(self, 'last_time'):
                next_time = self.last_time + self.scheduled
            else:
                next_time = pyromancer.connect_time + self.scheduled

        if next_time is not None:
            return datetime.datetime.now() >= next_time

        return False

    def send_messages(self, result, match):
        if isinstance(result, (list, GeneratorType)):
            messages = result
        else:
            messages = [result]

        for msg in messages:
            if not isinstance(msg, tuple):
                # raise error
                pass
            last = len(msg) - 1
            t, msg, args, kwargs = (msg[0], msg[1], list(msg[2:last]),
                                    msg[last])

            # If the result is (msg, positional argument,), make sure it
            # still works correctly as expected for the formatting.
            if not isinstance(kwargs, dict):
                args.append(kwargs)
                kwargs = {}

            match.msg(msg, *args, target=t, **kwargs)
