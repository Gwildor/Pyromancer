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
    install_requires=[],
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Communications',
        'Topic :: Communications :: Chat',
        'Topic :: Communications :: Chat :: Internet Relay Chat',
        'Topic :: Internet',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Application Frameworks'
    ]
)
