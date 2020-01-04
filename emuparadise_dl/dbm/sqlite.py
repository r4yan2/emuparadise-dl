import sqlite3

class SQLiteDBM(object):
    create_stmt = """
CREATE TABLE %s (
FID INTEGER PRIMARY KEY,
GID TEXT NOT NULL,
NAME TEXT NOT NULL,
SYSTEM TEXT,
SIZE TEXT
)
"""

    insert_stmt = """
INSERT INTO %s VALUES (NULL,"%s","%s","%s","%s")
"""

    get_results_stmt = """
SELECT FID,NAME,SYSTEM,SIZE FROM %s
"""

    get_rom_stmt = """
SELECT GID FROM %s WHERE FID = %d
"""

    def __init__(self):
        db = sqlite3.connect(":memory:")
        self.cur = db.cursor()
        self.tables = dict()

    def create(self, obj):
        cls = obj.__class__
        name = cls.__name__
        self.tables[cls] = name
        self.cur.execute(self.create_stmt % name)

    def write(self, obj, item):
        cls = obj.__class__
        name = cls.__name__
        args = (name,) + tuple(item.values())
        self.cur.execute(self.insert_stmt % args)

    def get_results(self, cls):
        name = cls.__name__
        res = self.cur.execute(self.get_results_stmt % name)
        return [e for e in res]

    def query(self, fid):
        for cls, table in self.tables:
            res = self.cur.execute(query % (fid, table))
            if res:
                return cls, res
        return False, False

