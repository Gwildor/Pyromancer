import datetime
import importlib
import inspect
import socket
import time

from irc.buffer import DecodingLineBuffer


class Pyromancer(object):

    def __init__(self, settings_path):
        self.settings = Settings(settings_path)
        self.find_commands()

    def connect(self):
        return Connection(self.settings.host, self.settings.port,
                          self.settings.encoding)

    def run(self):
        self.connection = self.connect()
        self.online = True

        self.connection.write('NICK {}\n'.format(self.settings.nick))
        self.connection.write('USER {0} {1} {1} :{2}\n'.format(
            self.settings.nick, self.settings.host, self.settings.real_name))

        ticks = self.settings.ticks
        while self.online:
            self.connection.read()

            for line in self.connection.buffer.lines():
                line = Line(line)

                if line[0] == 'PING':
                    self.connection.write('PONG {}\n'.format(line[1]))

                for c in self.commands:
                    c.command.match(line, self.connection, self.settings)

            time.sleep(1.0 / ticks)

    def find_commands(self):
        self.commands = []

        for package in self.settings.packages:
            module = importlib.import_module('{}.commands'.format(package))

            modules = [('', module,)]
            modules.extend(inspect.getmembers(module, inspect.ismodule))

            for name, module in modules:
                functions = inspect.getmembers(module, inspect.isfunction)

                self.commands.extend(f for fn, f in functions
                                     if hasattr(f, 'command'))


class Settings(object):

    def __init__(self, path):
        self.main_settings = importlib.import_module(path)
        self.packages = self.main_settings.packages
        self.package_settings = {}

        if 'pyromancer' not in self.packages:
            self.packages.append('pyromancer')

        for package in self.packages:
            self.package_settings[package] = importlib.import_module(
                '{}.settings'.format(package))

    def __getattr__(self, item):
        if hasattr(self.main_settings, item):
            return getattr(self.main_settings, item)

        for package in self.packages:
            if hasattr(self.package_settings[package], item):
                return getattr(self.package_settings[package], item)

        raise AttributeError('No such setting {} found in any of the '
                             'installed packages'.format(item))


class Connection(object):

    def __init__(self, host, port, encoding='utf8'):
        self.socket = socket.socket()
        self.socket.connect((host, port))
        self.encoding = encoding

        self.buffer = DecodingLineBuffer()
        self.buffer.encoding = self.encoding

    def write(self, data):
        self.socket.send('{}\n'.format(data).encode(self.encoding))

    def read(self, bytes=4096):
        self.buffer.feed(self.socket.recv(bytes))

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
            message = message.format(*args, m=self, **kwargs)

        self.connection.msg(target, message)


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
