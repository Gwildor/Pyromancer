from distutils.core import setup

import pyromancer

setup(
    name='Pyromancer',
    version=pyromancer.__version__,
    packages=['pyromancer', 'pyromancer.commands'],
    description='Simple IRC bot implementation / framework',
    long_description=open('README.md').read(),
    author='Gwildor Sok',
    author_email='gwildorsok@gmail.com',
    url='https://github.com/Gwildor/Pyromancer',
    install_requires=[
        'irc'
    ],
)
