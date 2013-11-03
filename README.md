Simple IRC bot implementation.

### Example

```python
from pyromancer.objects import Pyromancer

HOST = '1.2.3.4'
PORT = 6667
NICK = 'PyromancerBot'

settings = {'host': HOST, 'port': PORT, 'nick': NICK, 'encoding': 'ISO-8859-1',
            'packages': ['.test_examples']}

p = Pyromancer(settings)
p.run()
```

### Custom commands
Writing own commands is fairly simple. Create a folder which will be the package name, with a folder named "commands" in it and a module to hold the commands in there. In your module, you can register functions to be a command with the built-in command decorator. After that you need to register it in your settings, and you can use it.

#### Example

File layout:

```
test/
    commands/
        __init__.py
        test_commands.py
    __init__.py
init.py
```

test_commands.py:

```python
from pyromancer.decorators import command

@command(r'bye (.*)')
def bye(match):
    match.connection.msg(match.line.sender.nick, 'Bye {}!'.format(match[1]))
```

init.py:

```python
settings['packages'] = ['test.test_commands']
```

On IRC:

```
<User> bye everyone
<Bot> Bye everyone!
```

Pyromancer scans the modules in the settings automatically for functions decorated using the commands decorator, so all your commands in `test_commands.py` are used automatically.
