Simple IRC bot implementation.

Example:

```python
from pyromancer.objects import Pyromancer

HOST = '1.2.3.4'
PORT = 6667
NICK = 'PyromancerBot'

settings = {'host': HOST, 'port': PORT, 'nick': NICK, 'encoding': 'ISO-8859-1'}

p = Pyromancer(settings)
p.run()
```
