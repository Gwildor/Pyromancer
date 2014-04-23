from pyromancer.decorators import command
from pyromancer.objects import User, Channel


@command(command='PART')
def part(match):
    chan = match.line.channel
    user = match.line.sender
    user.channels.remove(chan)
    chan.users.remove(user)


@command(command='NICK')
def nick(match):
    match.line.sender.nick = match.line[2].lstrip(':')


@command(command='KICK')
def kick(match):
    user = User.get(match.line[3], match)
    match.line.channel.users.remove(user)


@command(command='JOIN')
def join(match):
    chan = match.line.channel
    user = match.line.sender
    chan.users.append(user)
    user.channels.append(chan)

    if user is match.connection.me:
        match.connection.write('WHO {}'.format(chan.name))


@command(command='QUIT')
def quit(match):
    for chan in match.line.sender.channels:
        chan.users.remove(match.line.sender)


@command(code=352)
def who_entry(match):
    user = User.get(match.line[7], match)

    if user.host is None:
        # User is new to us, so let's set info we know
        user.host = match.line[5]

    chan = Channel.get(match.line[3], match)
    if user not in chan.users:
        chan.users.append(user)

    if chan not in user.channels:
        user.channels.append(chan)
