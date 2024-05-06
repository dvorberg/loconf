import dataclasses, datetime
from sqlclasses import sql

from . import config, sqldebug

class Database(object):
    """
    Abstract base class for CV databases
    """
    def store(self, cab:int, cvs:list[int], revision_comment=""):
        raise NotImplementedError()

    def get(self, cab:int, cv:int):
        raise NotImplementedError()

    def get_all(self, cab:int):
        raise NotImplementedError()

class CursorWrapper(object):
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, params=()):
        if config.sqldebug:
            s = query % tuple([ str(p) for p in params ])
            sqldebug(s)
        return self.cursor.execute(query, params)

    def __getattr__(self, name):
        return getattr(self.cursor, name)

@dataclasses.dataclass
class Revision(object):
    id: int
    address: int
    comment: str
    ctime: datetime.datetime

class PostgresDatabase(Database):
    def __init__(self, params):
        import psycopg2
        self.params = params
        self.backend = sql.Backend(psycopg2, None)
        self._ds = None

    @property
    def ds(self):
        import psycopg2
        if self._ds is None:
            self._ds = psycopg2.connect(**self.params)
        return self._ds

    def connect(self):
        # This will call the ds() property method above.
        self.ds

    def cursor(self):
        return CursorWrapper(self.ds.cursor())

    def execute(self, *query, cursor=None):
        cmd, params = sql.rollup(self.backend, *query, debug=False)
        if cursor is None:
            cursor = self.cursor()
        cursor.execute(cmd, params)
        return cursor

    def commit(self):
        self.ds.commit()

    def store(self, cab:int, cvs:dict[int, int], revision_comment=""):
        # Remove None values from cvs
        cvs = dict([ (name, value)
                     for (name, value) in cvs.items()
                     if value is not None ])
        if not cvs:
            return

        # Create a revision entry.
        cursor = self.execute(sql.insert.from_dict(
            "revision", { "address": cab, "comment": revision_comment, }))
        cursor.execute("SELECT CURRVAL('revision_id_seq')")
        revision_id, = cursor.fetchone()

        # Create value entries for each of the CV.
        self.execute(sql.insert.from_dict(
            "value", *[ {"revision_id": revision_id, "cv": cv, "value": value}
                        for ( cv, value ) in cvs.items() ]))
        self.commit()

    def get(self, cab:int, cv:int):
        """
        Return the latest known entry for “cv” on “cab”.
        """
        result = self.get_all(cab, cv)
        return result.get(cv, None)

    def get_all(self, cab:int, cv:int|None=None):
        """
        Return the latest known CV settings on “cab” as a dict (optinally
        limit the query to “cv”.)
        """
        query = """\
            WITH latest AS (
                SELECT cv, address, MAX(revision_id) AS revision_id
                  FROM value
                  LEFT JOIN revision ON revision_id = revision.id
                  GROUP BY cv, address
            )
            SELECT latest.cv, value
              FROM latest
              LEFT JOIN value
                     ON latest.cv = value.cv
                    AND latest.revision_id = value.revision_id
             WHERE address = %s
             ORDER BY cv"""
        params = ( cab, )

        if cv is not None:
            query += " AND cv = %s"
            params += ( cv, )

        cursor = self.cursor()
        cursor.execute(query, params)
        return dict(cursor.fetchall())

    def get_revision(self, cab:int, revision_id:int):
        """
        Retrieve the latest know CV settings for “cab” at the time of
        the identified revision.
        """
        query = """\
            WITH latest AS (
                SELECT cv, address, MAX(revision_id) AS revision_id
                  FROM value
                  LEFT JOIN revision ON revision_id = revision.id
                  WHERE revision_id <= %s
                  GROUP BY cv, address
            )
            SELECT latest.cv, value
              FROM latest
              LEFT JOIN value
                     ON latest.cv = value.cv
                    AND latest.revision_id = value.revision_id
             WHERE address = cab
             ORDER BY cv"""
        params = ( revision_id, cab, )

        cursor = self.cursor()
        cursor.execute(query, params)
        return dict(cursor.fetchall())

    def get_revisions(self, cab:int):
        cursor = self.cursor()
        cursor.execute("SELECT id, address, comment, ctime "
                       "  FROM revision"
                       " WHERE address = %s"
                       " ORDER BY id DESC", ( cab, ))
        return [ Revision(*tpl) for tpl in cursor.fetchall() ]
