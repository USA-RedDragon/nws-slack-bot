from sqlalchemy import create_engine
from orm import init_db

_db = None


def get_engine():
    global _db
    if _db is None:
        _db = create_engine('sqlite+pysqlite:///data/wx.db', echo=True)
        init_db(_db)
    return _db
