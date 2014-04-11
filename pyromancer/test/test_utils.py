from datetime import timedelta

from pyromancer import utils
from pyromancer.objects import Timer

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
     Timer(timedelta(seconds=3), 'Hello world', target='User'))
]


def test_processing_messages():
    for result, expected in MESSAGES:
        for r in utils.process_messages(result):
            assert r == expected
