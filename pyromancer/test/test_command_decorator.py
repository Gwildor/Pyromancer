from pyromancer.decorators import command
from pyromancer.objects import Match, Line
from pyromancer.test.decorators import mock_connection

MESSAGES = [
    (('Hello {}', 'world'), 'Hello world'),
    (('Hello {} and {}', 'world', 'Mars'), 'Hello world and Mars'),
    (('Hello {}', ['world']), 'Hello world'),
    (('Hello {} and {}', ['world', 'Mars']), 'Hello world and Mars'),
    (('Hello {sphere}', {'sphere': 'world'}), 'Hello world'),
    (('Hello {} and {red_one}', 'world', {'red_one': 'Mars'}),
     'Hello world and Mars'),
    (('Hello {}, {} and {red_one}', 'world', 'moon', {'red_one': 'Mars'}),
     'Hello world, moon and Mars'),
    (('Hello {}, {} and {red_one}', ['world', 'moon'], {'red_one': 'Mars'}),
     'Hello world, moon and Mars'),
]


@mock_connection
def test_command_messaging_return_tuple(c):
    line = Line(':John!JDoe@some.host PRIVMSG #Chan :Some cool message')
    instance = command(r'')
    match = Match(None, line, c)

    for msg, expected in MESSAGES:
        instance.send_messages(msg, match)
        assert c.last == 'PRIVMSG #Chan :{}'.format(expected)


@mock_connection
def test_command_messaging_return_list(c):
    line = Line(':John!JDoe@some.host PRIVMSG #Chan :Some cool message')
    instance = command(r'')
    match = Match(None, line, c)

    instance.send_messages([msg for msg, expected in MESSAGES], match)

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

    instance.send_messages(mock_command(), match)

    for index, (msg, expected) in enumerate(MESSAGES):
        assert c.outbox[index] == 'PRIVMSG #Chan :{}'.format(expected)
