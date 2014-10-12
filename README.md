[![Build Status](http://img.shields.io/travis/Gwildor/Pyromancer.svg)](https://travis-ci.org/Gwildor/Pyromancer)
[![Latest Version](http://img.shields.io/pypi/v/Pyromancer.svg)](https://pypi.python.org/pypi/Pyromancer)
[![Coverage Status](http://img.shields.io/coveralls/Gwildor/Pyromancer.svg)](https://coveralls.io/r/Gwildor/Pyromancer)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](https://tldrlegal.com/license/mit-license)

Simple framework for creating IRC bots.

### Example

init.py:

```python
from pyromancer.objects import Pyromancer

p = Pyromancer('test.settings')
p.run()
```

test/settings.py:

```python
host = '1.2.3.4'
port = 6667
nick = 'PyromancerBot'
encoding = 'ISO-8859-1'
```

### Custom commands
Writing own commands is fairly simple. Create a folder which will be the package name, with a file named `commands.py` in it to hold the commands. In `commands.py`, you can register functions to be a command with the built-in command decorator.

#### Example

File layout:

```
test/
    __init__.py
    commands.py
    settings.py
init.py
```

commands.py:

```python
from pyromancer.decorators import command


@command(r'bye (.*)')
def bye(match):
    return 'Bye {m[1]}!'
```

On IRC:

```
<User> bye everyone
<Bot> Bye everyone!
```

Pyromancer scans automatically for functions decorated using the commands decorator, so all your commands in `commands.py` are used automatically.

You can also create a directory named `commands` with submodules containing the commands. Just make sure that you import either the modules or all of the commands in the `__init__.py` file.

#### The `command` decorator

You must apply this to a function to mark it as a command. It will be used when scanning for and collecting commands.

##### Parameters

* `patterns` - a regular expression or a list of expressions. When a list is given, all patterns are attempted when matching the input, and only when all patterns in the list fail to match, the command is not executed.
```python
@command(['hi', 'hello'])
def hi(match):
    return 'Hello!'
```

* `prefix` - a boolean which defaults to `True`. When true, the command pattern is only attempted to match when the message line starts with the prefix defined in the settings of the bot. This is useful for commands which are very bot-like (in contrary to commands which look and behave like natural language). Using a boolean and a setting allows the same command to be triggered in different ways, depending on the settings of the bot which installed the command package.

* `raw` - a boolean which defaults to `False`. When true, the raw input line sent from the server is used for matching the pattern, instead of the message. Useful for matching lines which are not a message from an user, such as nick or topic changes.

#### Messaging from a command

Messaging from inside the function which makes up the command is as easy as can be for simple use cases, but can be done in numerous ways for the more complex situations.

Most of the times, arguments are passed to the `Match.msg` function, which applies formatting by default and provides some additional utilities. The most important of those is that when no target has been passed on as an argument, it will use either the channel or the user (in case of a PM) whose input line triggered the command to be executed as the target, effectively replying.

##### Parameters

* `message` - the message to be send to the server. Formatting will be applied using any additional `args` and `kwargs`, so you can apply the full power of the [Python Format Mini-Language](http://docs.python.org/3.3/library/string.html#format-string-syntax) on the message.

* `args` and `kwargs` - arguments to be passed on through the formatting which is applied on `message`.

##### Methods of messaging

* Return a `message`
```python
@command(r'bye (.*)')
def bye(match):
    return 'Bye {m[1]}!'
```

* Return a tuple of `message` and optional `args` and `kwargs` to be used when formatting `message`. `args` can be both a list of arguments, or simply all the middle elements of the tuple.
```python
def gibberish(match):
    return 'A = {}, B = {}, C = {c_char}', 'a', 'b', {'c_char': 'c'}
```

* Yield a `message` or a tuple of `message` and optional `args` and `kwargs`. Yielding can be done as much as you want, which is the easiest way of sending multiple messages from one command.
```python
@command(r'say (.*)')
def say(match):
    for part in match[1].split(', '):
        yield 'Saying {}', part
```

* Return a list of `message` or a tuple of `message` and optional `args` and `kwargs`.
```python
def hi(match):
    return ['Hi', 'Hello']
```

* Use `Match.msg`. This is the only way to benefit from the non-default functionalities provided by this function.
```python
def raw(match):
    match.msg('Raw {} message {m[1]}', raw=True)
```

##### Extra parameters for `Match.msg`

* `target` - the target to send the message to. If not provided, it will attempt to use either the channel or user whose input line triggered the command, which effectively results in replying.

* `raw` - defaults to `False`. When true, no formatting is applied on `message`.

### Timers

You can register timers in a custom `timers` module, or you can create them from inside commands or other timers. When creating or registering a timer, you can either specify a `timedelta` or `datetime` object to schedule the timer. When specifying a timedelta, you can also specify the amount of times the timer should execute, which defaults to infinite. Timers can send messages based on arguments given upon initialization, but also call a callable which in itself can send messages or initialize new timers.

When messaging from a timer, you must always specify a target to send the message to before the message (when returning a message tuple), or with the `target` argument on the `Match` instance when using the `Match.msg` method. Because there is no line which triggered the timer, nothing can be used to decide where to send the message to when the target is not specified.

#### Example of timers through a module

timers.py:

```python
from datetime import datetime, timedelta

from pyromancer.decorators import timer


@timer(timedelta(seconds=3), count=5)
def say_time(match):
    return 'User', "It's {}", datetime.now()
```

#### Example of timers through messaging

commands.py:

```python
from datetime import datetime, timedelta

from pyromancer.decorators import timer


@command(r'start_timer')
def start_timer(match):
    return timedelta(seconds=3), 'User', "It's {}", datetime.now()
```

You can also return a `Timer` instance, or specify a callable as the second item of the returned tuple, which is then called like any function with the `timer` decorator.

### Using a database

  [3]: http://docs.sqlalchemy.org/en/latest/core/engines.html?highlight=create_engine#sqlalchemy.create_engine
  [4]: http://docs.sqlalchemy.org/en/latest/orm/extensions/declarative.html#sqlalchemy.ext.declarative.declarative_base
  [5]: http://docs.sqlalchemy.org/en/latest/orm/session.html

To enable the integrated database support, you have to set the `database` setting to a string which holds the URL to the database, as accepted by [SQLAlchemy's create_engine][3] function. Then, in a `models` module, you can import the [declarative base][4] to construct your model, and import the [Session][5] for querying.

#### Example with a simple model and timer

This example creates a table named `test` in a SQLite `test.db` file, and creates an entry with the current date and time every three seconds, and a command which returns the count of entries in the table.

settings.py:

```python
database = 'sqlite:///test.db'
```

models.py:

```python
from sqlalchemy import Column, DateTime, Integer

from pyromancer.database import Base


class Test(Base):
    __tablename__ = 'test'

    id = Column(Integer, primary_key=True)
    value = Column(DateTime)
```

timers.py:

```python
from datetime import datetime, timedelta

from pyromancer.database import Session
from pyromancer.decorators import timer

from .models import Test


@timer(timedelta(seconds=3))
def hi(match):
    session = Session()
    session.add(Test(value=datetime.now()))
    session.commit()
```

commands.py:

```python
from pyromancer.database import Session
from pyromancer.decorators import command

from .models import Test


@command(r'timers')
def timers(match):
    session = Session()
    return 'Timer count: {}', session.query(Test).count()
```

### Dependencies

* [irc][1]
* [SQLAlchemy][2], if you want to enable the use of a database.


  [1]: https://pypi.python.org/pypi/irc
  [2]: http://www.sqlalchemy.org
  
### Support

Python 2.7 and 3.0 - 3.4 are supported. Note that development occurs on Python 3.

### To do

* Figure out how to do translation of messages through the `Match.msg` function.

### Changelist

#### 1.0 - WIP

* Add timers.
* Add integrated database support.
* Add command module which tracks channels and users.
* Change color code parameter in message formatting to `c` (was `k` by mistake).
* Switch to MIT license.

##### Yet to do for 1.0:
* Clean up code and raise test coverage.

#### 0.4 - 2014-03-30

* Add support for Python 2.7.
* Add more tests.
* Fix messaging with positional arguments given as a list not working.
* Add ability to create commands for raw code lines by specifying a code to match.
* Add ability to do easy message formatting for colored, underlined and bold text.

#### 0.3 - 2014-03-22

* Change settings to be a Python module instead of a dictionary.
* Change package loading.
* Enable the commands from the package of which the settings are in by default.
* Add ability to process raw input lines.
* Add option to use precompiled regular expressions in the command decorator.
* Add option to pass flags for compiling the regular expressions in the command decorator.
* Fix returning message from command not working.

#### 0.2 - 2014-03-14

* Add tests.
* Add multiple and easier ways to send messages from a command.
* Add support for multiple patterns for the same command.
* Add a configurable command prefix setting for the more bot-like commands.
* Trying to access a word in a `Line` now correctly returns an empty string when the index does not exist.
* Fix passing positional arguments to `Match.msg` not working properly.

#### 0.1 - 2013-11-17

* Initial release.
