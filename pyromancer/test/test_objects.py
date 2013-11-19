from pyromancer.objects import User, Line


def test_user_with_nick():
    user_str = u'Abc09_-\\[]{}^`|!RealName@some.host'
    user = User(user_str)

    assert user.host == 'some.host'
    assert user.name == 'RealName'
    assert user.nick == u'Abc09_-\\[]{}^`|'


def test_user_without_nick():
    user_str = u'some.host'
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
