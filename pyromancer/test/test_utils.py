from datetime import timedelta

from pyromancer import utils
from pyromancer.objects import Timer

example_command = lambda m: m

MESSAGES = [
    ('Hello world', ('Hello world', [], {})),
    (('Hello {}', 'world'), ('Hello {}', ['world'], {})),
    (('Hello {} and {}', 'world', 'Mars'),
     ('Hello {} and {}', ['world', 'Mars'], {})),
    (('Hello {} and {}', ['world', 'Mars']),
     ('Hello {} and {}', [['world', 'Mars']], {})),
    (('Hello {sphere}', {'sphere': 'world'}),
     ('Hello {sphere}', [], {'sphere': 'world'})),
    (('Hello {} and {red_one}', 'world', {'red_one': 'Mars'}),
     ('Hello {} and {red_one}', ['world'], {'red_one': 'Mars'})),
    (('Hello {}, {} and {red_one}', 'world', 'moon', {'red_one': 'Mars'}),
     ('Hello {}, {} and {red_one}', ['world', 'moon'], {'red_one': 'Mars'})),
    (('Hello {}, {} and {red_one}', ['world', 'moon'], {'red_one': 'Mars'}),
     ('Hello {}, {} and {red_one}', [['world', 'moon']], {'red_one': 'Mars'})),
    (('Hello {}', ['world', 'moon']), ('Hello {}', [['world', 'moon']], {})),
    ((timedelta(seconds=3), 'User', 'Hello world'),
     Timer(timedelta(seconds=3), 'Hello world', target='User')),
    ((timedelta(seconds=3), example_command),
     Timer(timedelta(seconds=3), example_command)),
    (Timer(timedelta(seconds=3), example_command),
     Timer(timedelta(seconds=3), example_command))
]

MESSAGES_WITH_TARGET = [
    ('Hello world', (None, 'Hello world', [], {})),
    (('User', 'Hello world'), ('User', 'Hello world', [], {})),
    (('User', 'Hello {}', 'world'), ('User', 'Hello {}', ['world'], {}))
]


def test_processing_messages():
    for result, expected in MESSAGES:
        for r in utils.process_messages(result):
            assert r == expected


def test_processing_messages_with_target():
    for result, expected in MESSAGES_WITH_TARGET:
        for r in utils.process_messages(result, with_target=True):
            assert r == expected
