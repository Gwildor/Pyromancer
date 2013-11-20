from pyromancer.objects import Connection


class MockConnection(Connection):

    def __init__(self, *args, **kwargs):
        self.outbox = []

    def write(self, data):
        self.outbox.append(data)
