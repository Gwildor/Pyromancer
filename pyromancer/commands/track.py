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

    if not user.auth:
        match.connection.write('WHOIS {}'.format(nick))


@command(command='QUIT')
def quit(match):
    for chan in match.line.sender.channels:
        chan.users.remove(match.line.sender)


@command(code=353)
def names(match):
    chan = Channel.get(match.line[4], match)

    if not chan:
        chan = Channel(match.line[4])

    for nick in match.line[5:]:
        nick = nick.lstrip(':!~&@%+')
        user = User.get(nick, match)

        if not user:
            user = User(nick)

        chan.users.append(user)
        user.channels.append(chan)

        if not user.auth:
            match.connection.write('WHOIS {}'.format(nick))


@command(code=311)
def whois_host_and_name(match):
    user = User.get(match.line[3], match)
    user.host = match.line[5]


@command(code=330)
def whois_auth(match):
    user = User.get(match.line[3], match)
    user.auth = match.line[4]
