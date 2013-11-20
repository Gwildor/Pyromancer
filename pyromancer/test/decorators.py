from pyromancer.test.mock_objects import MockConnection


def mock_connection(fn):

    def wrapper(*args, **kwargs):
        connection = MockConnection()
        fn(connection, *args, **kwargs)

    return wrapper
