from distutils.core import setup

import pyromancer

try:
    long_description = open('README.rst').read()
except FileNotFoundError:
    long_description = open('README.md').read()

setup(
    name='Pyromancer',
    version=pyromancer.__version__,
    packages=['pyromancer', 'pyromancer.commands', 'pyromancer.test'],
    description='Simple framework for creating IRC bots',
    long_description=long_description,
    author='Gwildor Sok',
    author_email='gwildorsok@gmail.com',
    url='https://github.com/Gwildor/Pyromancer',
    install_requires=[
        'irc'
    ],
)
