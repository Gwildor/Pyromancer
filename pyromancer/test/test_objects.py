import re

from pyromancer.objects import User, Line, Match
from pyromancer.test.decorators import mock_connection


def test_user_with_nick():
    user_str = 'Abc09_-\\[]{}^`|!RealName@some.host'
    user = User(user_str)

    assert user.host == 'some.host'
    assert user.name == 'RealName'
    assert user.nick == 'Abc09_-\\[]{}^`|'


def test_user_without_nick():
    user_str = 'some.host'
    user = User(user_str)

    assert user.host == 'some.host'
    assert user.name is None
    assert user.nick is None


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
    line = Line(':John!JDoe@some.shot PRIVMSG #Chan :Some cool message')
    match = Match(None, line, c)
    match.msg('A {} reply', 'cool')

    assert c.outbox[0] == 'PRIVMSG #Chan :A cool reply'

    line = Line(':John!JDoe@some.shot PRIVMSG TestBot :Some cool message')
    match = Match(None, line, c)
    match.msg('A {} reply', 'cool')

    assert c.outbox[1] == 'PRIVMSG John :A cool reply'

    match.msg('A private message', target='SomeUser')

    assert c.outbox[2] == 'PRIVMSG SomeUser :A private message'

    match.msg('A {}formatted message', 'mis', raw=True)

    assert c.outbox[3] == 'PRIVMSG John :A {}formatted message'
