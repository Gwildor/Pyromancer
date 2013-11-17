from pyromancer.decorators import command


@command(r'hi$')
def hi(match):
    match.msg('Hello!')


@command(r'hi (.*)')
def greeting(match):
    match.msg('Hello {m[1]}!')
