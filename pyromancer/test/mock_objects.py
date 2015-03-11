from pyromancer.objects import Connection, User


class MockObject(object):

    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)


class MockConnection(Connection):

    def __init__(self, *args, **kwargs):
        self.outbox = []
        self.me = User('')

    def write(self, data):
        self.outbox.append(data)

    @property
    def last(self):
        return self.outbox[-1:][0]
