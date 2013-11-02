import datetime
import socket

from irc.buffer import DecodingLineBuffer


class Pyromancer(object):

    def __init__(self, settings):
        self.parse_settings(settings)

    def connect(self):
        return Connection(self.host, self.port, self.encoding)

    def run(self):
        self.connection = self.connect()
        self.online = True

        self.connection.write('NICK {}\n'.format(self.nick))
        self.connection.write('USER {0} {1} {1} :{2}\n'.format(self.nick,
                                                               self.host,
                                                               self.real_name))

        while self.online:
            self.connection.read()

            for line in self.connection.buffer.lines():
                line = Line(line)
                print(line)

                if line[0] == 'PING':
                    self.connection.write('PONG {}\n'.format(line[1]))

    def parse_settings(self, settings):
        self.host = settings.get('host', '')
        self.port = settings.get('port', 6667)
        self.encoding = settings.get('encoding', 'utf8')
        self.nick = settings['nick']
        self.ident = settings.get('ident', self.nick)
        self.real_name = settings.get('real_name', self.nick)


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


class Line(object):

    def __init__(self, data):
        self.raw = data
        self.datetime = datetime.datetime.now()
        self.parse()

    def __getitem__(self, item):
        try:
            if self.usermsg:
                word = self.parts[item + 3]

                # First word of text starts with a ":", which we don't want
                return word[1:] if item == 0 else word
            else:
                return self.parts[item]
        except KeyError:
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
