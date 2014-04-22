import datetime
import re

from pyromancer.decorators import timer
from pyromancer.objects import User, Line, Match, Timer, Channel
from pyromancer.test.decorators import mock_connection


def test_user_str_parsing():
    user_str = 'Abc09_-\\[]{}^`|!RealName@some.host'
    user = User(user_str)

    assert user.host == 'some.host'
    assert user.name == 'RealName'
    assert user.nick == 'Abc09_-\\[]{}^`|'

    user = User('AName')
    assert user.host is None
    assert user.name is None
    assert user.nick == 'AName'


@mock_connection
def test_user_get_function(c):
    c.me = User('Test')
    match = Match(None, None, c)

    assert c.users == [c.me]
    assert User.get('Test', c) is c.me
    assert User.get('Test!A@B', c) is c.me
    assert User.get('Test', match) is c.me
    assert User.get('Test', None) is not c.me
    assert User.get('Test2', c) is not c.me


@mock_connection
def test_channel_get_function(c):
    c.me = User('')

    chan = Channel('#test')
    assert c.channels == []

    c.me.channels.append(chan)
    assert c.channels == [chan]

    assert Channel.get('#test', c) is chan
    assert Channel.get('#test2', c) is not chan

    match = Match(None, None, c)
    assert Channel.get('#test', match) is chan

    assert Channel.get('#test', None) is not chan


def test_line_parsing_with_privmsg():
    line_str = ':John!JDoe@some.shot PRIVMSG #Chan :Some cool message'
    line = Line(line_str)

    assert line.privmsg is True
    assert line.notice is False
    assert line.usermsg is True
    assert line.sender.nick == 'John'
    assert line.target == '#Chan'
    assert line.pm is False
    assert line.full_msg == 'Some cool message'
    assert line[0] == 'Some'
    assert line[1:] == ['cool', 'message']
    assert line[3] == ''


@mock_connection
def test_connection_msg_function(c):
    c.msg('#Chan', 'A nice message!')

    assert len(c.outbox) == 1
    assert c.outbox[0] == 'PRIVMSG #Chan :A nice message!'


def test_match_getitem():
    m = re.search(r'(\w+) (\d+)', 'A Hello 2 u!')
    match = Match(m, None, None)

    assert match[0] == 'Hello 2'
    assert match[1] == 'Hello'
    assert match[2] == '2'
    assert match[3] == ''


@mock_connection
def test_match_msg_with_privmsg(c):
    line = Line(':John!JDoe@some.host PRIVMSG #Chan :Some cool message')
    match = Match(None, line, c)
    match.msg('A {} reply', 'cool')

    assert c.outbox[0] == 'PRIVMSG #Chan :A cool reply'

    line = Line(':John!JDoe@some.host PRIVMSG TestBot :Some cool message')
    match = Match(None, line, c)
    match.msg('A {} reply', 'cool')

    assert c.outbox[1] == 'PRIVMSG John :A cool reply'

    match.msg('A private message', target='SomeUser')

    assert c.outbox[2] == 'PRIVMSG SomeUser :A private message'

    match.msg('A {}formatted message', 'mis', raw=True)

    assert c.outbox[3] == 'PRIVMSG John :A {}formatted message'


def test_timer_matches_function():
    now = datetime.datetime.now()
    connect_time = now - datetime.timedelta(seconds=4)

    timer_with_last_time = Timer(datetime.timedelta(seconds=3))
    timer_with_last_time.last_time = connect_time

    timers = [
        (Timer(datetime.timedelta(seconds=3)), True),
        (Timer(datetime.timedelta(seconds=5)), False),
        (Timer(datetime.timedelta(seconds=5), direct=True), True),
        (timer_with_last_time, True),
        (Timer(now - datetime.timedelta(days=1)), True),
        (Timer(now + datetime.timedelta(days=1)), False),
        (Timer(now + datetime.timedelta(days=1),
               direct=True), True),
    ]

    for t, expected in timers:
        assert t.matches(connect_time) is expected


def test_timer_decorator():
    function = lambda m: m
    timer_instance = timer(datetime.timedelta(seconds=3))
    timer_instance(function)

    assert isinstance(function.timer, Timer)
    assert function.timer.function is function
    assert function.timer.scheduled == datetime.timedelta(seconds=3)


@mock_connection
def test_messaging_from_timer(c):
    instance = Timer(None)
    match = Match(None, None, c)
    timers = []

    instance.send_messages((datetime.timedelta(seconds=3), 'User', 'Hi'),
                           match, timers)
    assert len(timers) == 1
    assert isinstance(timers[0], Timer)
    assert timers[0].scheduled == datetime.timedelta(seconds=3)
    assert timers[0].msg_tuple == ('User', 'Hi', (), {},)

    instance.send_messages(('User', 'Hello {}', 'world'), match, timers)
    assert c.last == 'PRIVMSG User :Hello world'
