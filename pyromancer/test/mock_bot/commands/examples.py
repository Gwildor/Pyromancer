from pyromancer.decorators import command


@command(r'hi$', prefix=False)
def hi(match):
    match.msg('Hello!')


@command(r'hi (.*)')
def greeting(match):
    match.msg('Hello {m[1]}!')


@command([r'say (.*)', r'tell (.*)'])
def say(match):
    for part in match[1].split(', '):
        yield 'Saying {}', part


@command(r'colors')
def colors(match):
    return '{u}{c}04C{c}05o{c}06l{c}o{c}07r{c}08{c}09s{c}!'
