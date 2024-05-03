from sqlclasses import sql

class Database(object):
    """
    Abstract base class for CV databases
    """
    def store(self, address:int, cvs:list[int], revision_comment=""):
        raise NotImplementedError()

    def get(self, address:int, cv:int):
        raise NotImplementedError()

    def get_all(self, address:int):
        raise NotImplementedError()

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

    def execute(self, *query, cursor=None):
        cmd, params = sql.rollup(self.backend, *query, debug=False)
        if cursor is None:
            cursor = self.ds.cursor()
        cursor.execute(cmd, params)
        return cursor

    def commit(self):
        self.ds.commit()

    def store(self, address:int, cvs:dict[int, int], revision_comment=""):
        # Create a revision entry.
        cursor = self.execute(sql.insert.from_dict(
            "revision", { "address": address, "comment": revision_comment, }))
        cursor.execute("SELECT CURRVAL('revision_id_seq')")
        revision_id, = cursor.fetchone()

        # Create value entries for each of the CV.
        self.execute(sql.insert.from_dict(
            "value", *[ {"revision_id": revision_id, "cv": cv, value: value}
                        for ( cv, value ) in cvs.items() ]))
        self.commit()



    def get(self, address:int, cv:int):
        cursor = self.execute(
            "SELECT value "
            "  FROM value "
            "  LEFT JOIN revision ON revision_id = revision.id "
            " WHERE ")

    def get_all(self, address:int):
        raise NotImplementedError()
