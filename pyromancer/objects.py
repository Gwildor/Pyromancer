import datetime
import importlib
import re
import socket
import time

from pyromancer import utils


class Pyromancer(object):

    def __init__(self, settings_path):
        self.settings = Settings(settings_path)
        self.setup_database()
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
        self.connection.me.nick = self.settings.nick

    def listen(self):
        self.online = True
        ticks = self.settings.ticks

        while self.online:
            self.connection.read()

            for line in self.connection.buffer.lines():
                self.process(line)

            for timer in self.timers:
                timer.match(self.timers, self.connect_time, self.connection,
                            self.settings)

            time.sleep(1.0 / ticks)

    def process(self, line):
        line = Line(line, self.connection)

        if line[0] == 'PING':
            self.connection.write('PONG {}\n'.format(line[1]))

        for c in self.commands:
            c.command.match(line, self.timers, self.connection, self.settings)

    def find_commands(self):
        self.commands = []

        utils.find_functions(
            self.settings.packages, self.commands, 'commands',
            'disabled_commands', when=lambda f: hasattr(f, 'command'))

    def find_timers(self):
        self.timers = []

        utils.find_functions(
            self.settings.packages, self.timers, 'timers', 'disabled_timers',
            when=lambda f: hasattr(f, 'timer'), ret=lambda f: f.timer)

    def setup_database(self):
        if self.settings.database:
            from sqlalchemy import create_engine

            from pyromancer.database import Session, Base

            engine = create_engine(self.settings.database)
            Session.configure(bind=engine)

            for package in self.settings.packages:
                if isinstance(package, tuple):
                    package = package[0]

                module_name = '{}.models'.format(package)

                try:
                    importlib.import_module(module_name)
                except ImportError:
                    continue

            Base.metadata.create_all(bind=engine)


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


class LineBuffer(object):
    """Line buffer based on irc library's DecodingLineBuffer.

    See https://bitbucket.org/jaraco/irc
    """
    line_sep_exp = re.compile(b'\r?\n')

    def __init__(self, encoding='utf-8'):
        self.buffer = b''
        self.encoding = encoding

    def feed(self, bytes):
        self.buffer += bytes

    def lines(self):
        lines = self.line_sep_exp.split(self.buffer)
        # save the last, unfinished, possibly empty line
        self.buffer = lines.pop()

        for line in lines:
            yield line.decode(self.encoding, 'strict')

    def __iter__(self):
        return self.lines()

    def __len__(self):
        return len(self.buffer)


class Connection(object):

    def __init__(self, host, port, encoding='utf8'):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.socket.setblocking(False)
        self.encoding = encoding

        self.buffer = LineBuffer(self.encoding)

        self.me = User('')

    @property
    def users(self):
        users = [self.me]
        for chan in self.me.channels:
            users.extend(chan.users)

        return list(set(users))

    @property
    def channels(self):
        return self.me.channels

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
    name = None
    host = None

    def __init__(self, str):
        if '@' in str:
            self.nick, self.name, self.host = self.split_user_str(str)
        else:
            self.nick = str

        self.channels = []

    def __repr__(self):
        return '{0.nick}@{0.host}'.format(self) if self.nick else self.host

    @staticmethod
    def split_user_str(str):
        nick, parts = str.split('!', 1)
        name, host = parts.split('@', 1)
        return nick.lstrip(':'), name, host

    @classmethod
    def get(cls, str, pool):
        if isinstance(pool, Match):
            pool = pool.connection

        if isinstance(pool, Connection):
            pool = pool.users

        if pool is None:
            pool = []

        if '@' in str:
            nick, _, _ = cls.split_user_str(str)
        else:
            nick = str

        for user in pool:
            if user.nick == nick:
                return user

        return cls(str)


class Channel(object):

    def __init__(self, name):
        self.name = name.lstrip(':')
        self.users = []

    def __repr__(self):
        return self.name

    @classmethod
    def get(cls, name, pool):
        if isinstance(pool, Match):
            pool = pool.connection

        if isinstance(pool, Connection):
            pool = pool.channels

        if pool is None:
            pool = []

        name = name.lstrip(':')

        for chan in pool:
            if chan.name == name:
                return chan

        return cls(name)


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

    def __init__(self, match, line, connection, settings=None):
        self.match = match
        self.line = line
        self.connection = connection
        self.settings = settings

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
                'c': chr(3),
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
COMMAND_PATTERN = re.compile(r'[A-Z]{4,5}')


class Line(object):

    def __init__(self, data, connection=None):
        self.raw = data.lstrip(':')
        self.datetime = datetime.datetime.now()
        self.connection = connection
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
            self.target = self.parts[2]
            self.pm = self.target[0] != '#'
            self.full_msg = ' '.join(self.parts[3:])[1:]
        elif CODE_PATTERN.match(self.parts[1]):
            self.code = int(self.parts[1])
        elif COMMAND_PATTERN.match(self.parts[1]):
            self.command = self.parts[1]

        if self.usermsg or getattr(self, 'command', None):
            self.sender = User.get(self.parts[0], self.connection)

            self.channel = None
            if not getattr(self, 'pm', False):
                self.channel = Channel.get(self.parts[2], self.connection)


class Timer(object):

    def __init__(self, scheduled, msg_or_command=None, *args, **kwargs):
        self.scheduled = scheduled
        self.direct = kwargs.pop('direct', False)
        self.remaining = kwargs.pop('count', 0)
        target = kwargs.pop('target', None)

        self.msg_tuple = None
        self.function = None

        if callable(msg_or_command):
            self.function = msg_or_command
        else:
            if target is not None and msg_or_command is not None:
                self.msg_tuple = (target, msg_or_command, args, kwargs,)

    def __eq__(self, other):
        return (self.scheduled == other.scheduled and
                self.function is other.function and
                self.msg_tuple == other.msg_tuple)

    def match(self, timers, connect_time, connection, settings):
        if self.matches(connect_time):
            self.last_time = datetime.datetime.now()
            match = Match(None, None, connection, settings)

            if self.function is not None:
                result = self.function(match)

                if result is not None:
                    self.send_messages(result, match, timers)

            if self.msg_tuple is not None:
                self.send_messages(self.msg_tuple, match, timers)

            if self.remaining > 0:
                self.remaining -= 1

                if self.remaining == 0:
                    timers.remove(self)

    def matches(self, connect_time):
        if self.direct:
            self.direct = False
            return True

        if isinstance(self.scheduled, datetime.datetime):
            next_time = self.scheduled

        if isinstance(self.scheduled, datetime.timedelta):
            if hasattr(self, 'last_time'):
                next_time = self.last_time + self.scheduled
            else:
                next_time = connect_time + self.scheduled

        return datetime.datetime.now() >= next_time

    def send_messages(self, result, match, timers):
        for r in utils.process_messages(result, with_target=True):
            if isinstance(r, Timer):
                timers.append(r)
            else:
                match.msg(r[1], *r[2], target=r[0], **r[3])
