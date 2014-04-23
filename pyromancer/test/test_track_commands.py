from pyromancer.commands import track
from pyromancer.objects import Line, User
from pyromancer.test.decorators import mock_connection
from pyromancer.test.mock_objects import MockObject


@mock_connection
def test_join_command(c):
    settings = MockObject(command_prefix='!')

    def match(line):
        assert track.join.command.matches(line, settings) is True
        track.join.command.match(line, [], c, settings)

    c.me = User('Pyro')

    line = Line(':Pyro!Hello@world JOIN :#Chan', c)
    assert line.sender is c.me

    match(line)
    assert len(c.me.channels) == 1
    assert c.me.channels[0] is line.channel
    assert c.last == 'WHO #Chan'

    channel = c.me.channels[0]
    line = Line(':User1!Hello@world JOIN #Chan', c)
    assert line.command == 'JOIN'
    assert line.channel == channel

    match(line)

    assert channel.users == [c.me, line.sender]
    assert line.sender.channels == [channel]
