from pyromancer.decorators import command


@command(r'hi$')
def hi(match):
    match.msg('Hello!')


@command(r'hi (.*)')
def greeting(match):
    match.msg('Hello {m[1]}!')


@command([r'say (.*)', r'tell (.*)'])
def say(match):
    for part in match[1].split(', '):
        yield 'Saying {}', part
