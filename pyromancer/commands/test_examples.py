from pyromancer.decorators import command


@command(r'hi$')
def hi(match):
    match.connection.msg(match.line.sender.nick, 'Hello!')

@command(r'hi (.*)')
def greeting(match):
    match.connection.msg(match.line.sender.nick, 'Hello {}!'.format(match[1]))
