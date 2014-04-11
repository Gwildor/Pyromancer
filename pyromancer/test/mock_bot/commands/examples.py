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
    return '{u}{k}04C{k}05o{k}06l{k}o{k}07r{k}08{k}09s{k}!'
