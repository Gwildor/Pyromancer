import datetime
import re

import pytest

from pyromancer.decorators import command
from pyromancer.exceptions import CommandException
from pyromancer.objects import Match, Line, Timer
from pyromancer.test.decorators import mock_connection
from pyromancer.test.mock_objects import MockObject

MESSAGES = [
    ('Hello world', 'Hello world'),
    (('Hello {}', 'world'), 'Hello world'),
    (('Hello {} and {}', 'world', 'Mars'), 'Hello world and Mars'),
    (('Hello {} and {}', ['world', 'Mars']), 'Hello world and Mars'),
    (('Hello {sphere}', {'sphere': 'world'}), 'Hello world'),
    (('Hello {} and {red_one}', 'world', {'red_one': 'Mars'}),
     'Hello world and Mars'),
    (('Hello {}, {} and {red_one}', 'world', 'moon', {'red_one': 'Mars'}),
     'Hello world, moon and Mars'),
    (('Hello {}, {} and {red_one}', ['world', 'moon'], {'red_one': 'Mars'}),
     'Hello world, moon and Mars'),
    (('Hello {}', ['world', 'moon']), "Hello ['world', 'moon']"),
]


def test_command_decorator_set_function():
    instance = command(r'')
    function = lambda m: m
    instance(function)

    assert isinstance(function.command, command)
    assert function.command.function is function


@mock_connection
def test_command_messaging_return_tuple(c):
    line = Line(':John!JDoe@some.host PRIVMSG #Chan :Some cool message')
    instance = command(r'')
    match = Match(None, line, c)

    for msg, expected in MESSAGES:
        instance.send_messages(msg, match, [])
        assert c.last == 'PRIVMSG #Chan :{}'.format(expected)


@mock_connection
def test_command_messaging_return_list(c):
    line = Line(':John!JDoe@some.host PRIVMSG #Chan :Some cool message')
    instance = command(r'')
    match = Match(None, line, c)

    instance.send_messages([msg for msg, expected in MESSAGES], match, [])

    for index, (msg, expected) in enumerate(MESSAGES):
        assert c.outbox[index] == 'PRIVMSG #Chan :{}'.format(expected)


@mock_connection
def test_command_messaging_yielding(c):
    def mock_command():
        for msg, expected in MESSAGES:
            yield msg

    line = Line(':John!JDoe@some.host PRIVMSG #Chan :Some cool message')
    instance = command(r'')
    match = Match(None, line, c)

    instance.send_messages(mock_command(), match, [])

    for index, (msg, expected) in enumerate(MESSAGES):
        assert c.outbox[index] == 'PRIVMSG #Chan :{}'.format(expected)


def test_command_appends_timers():
    instance = command(r'')
    match = Match(None, None, None)
    timers = []

    instance.send_messages((datetime.timedelta(seconds=3), 'User', 'Hi'),
                           match, timers)
    assert len(timers) == 1
    assert isinstance(timers[0], Timer)
    assert timers[0].scheduled == datetime.timedelta(seconds=3)
    assert timers[0].msg_tuple == ('User', 'Hi', (), {},)


def test_command_matches_patterns():
    line = Line(':John!JDoe@some.host PRIVMSG #Chan :Some cool message')
    settings = MockObject(command_prefix='!')

    instance = command(r'^Some', prefix=False)
    assert bool(instance.matches(line, settings)) is True

    instance = command(r'message$', prefix=False)
    assert bool(instance.matches(line, settings)) is True

    instance = command(r'^Some cool message$', prefix=False)
    assert bool(instance.matches(line, settings)) is True

    instance = command(r'mESsagE', prefix=False, flags=re.IGNORECASE)
    assert bool(instance.matches(line, settings)) is True

    instance = command(r'Some')
    assert bool(instance.matches(line, settings)) is False

    settings = MockObject(command_prefix='S')

    instance = command(r'^ome')
    assert bool(instance.matches(line, settings)) is True

    instance = command(r'cool')
    assert bool(instance.matches(line, settings)) is True

    line = Line(':irc.example.net 376 A :End of MOTD command')

    instance = command(r'example', prefix=False)
    assert bool(instance.matches(line, settings)) is False

    instance = command(r'example', raw=True, prefix=False)
    assert bool(instance.matches(line, settings)) is True


def test_command_matches_code():
    with pytest.raises(CommandException):
        command()

    with pytest.raises(CommandException):
        command(code='Foo')

    settings = MockObject(command_prefix='!')
    instance = command(code=376)

    line = Line(':irc.example.net 376 A :End of MOTD command')
    assert line.code == 376
    assert bool(instance.matches(line, settings)) is True

    line = Line(':irc.example.net 375 A :- irc.example.net message of the day')
    assert line.code == 375
    assert bool(instance.matches(line, settings)) is False


def test_command_matches_command():
    # A command is a 4 to 5 character all-capital string received from the
    # server. Examples: JOIN, QUIT, NICK, etc.
    settings = MockObject(command_prefix='!')
    instance = command(command='PART')

    line = Line(':John!JDoe@some.host PART #Chan :"Bye !"')
    assert line.command == 'PART'
    assert bool(instance.matches(line, settings)) is True

    line = Line(':John!JDoe@some.host NICK Paul"')
    assert line.command == 'NICK'
    assert bool(instance.matches(line, settings)) is False
