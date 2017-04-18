import os
from florin.db import Base, get_engine, init


TEST_DBFILE = 'test.sqlite'


class TestApp(object):
    pass


app = TestApp()


from florin.db import get_engine, Base
engine = get_engine(TEST_DBFILE)
Base.metadata.create_all(engine)
init(app, TEST_DBFILE)
