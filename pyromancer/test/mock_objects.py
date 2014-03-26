from pyromancer.objects import Connection


class MockConnection(Connection):

    def __init__(self, *args, **kwargs):
        self.outbox = []

    def write(self, data):
        self.outbox.append(data)

    @property
    def last(self):
        return self.outbox[-1:][0]
