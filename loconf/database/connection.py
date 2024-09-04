from termcolor import colored
from sqlclasses import sql

from .. import config, sqldebug
from .object import dbobject

class DatabaseConnection(object):
    """
    Abstract base class for CV databases
    """
    pass

class CursorDebugWrapper(object):
    def __init__(self, cursor):
        self._cursor = cursor

    def __getattr__(self, name):
        return getattr(self._cursor, name)

    def execute(self, query, vars=None):
        sql = self._cursor.mogrify(query, vars)
        print(colored(sql.decode("utf-8", errors="replace"), "cyan"))
        return self._cursor.execute(sql)

    def __enter__(self):
        return CursorDebugWrapper(self._cursor.__enter__())

    def __exit__(self, type, value, traceback):
        return self._cursor.__exit__(type, value, traceback)

    def __iter__(self):
        return self._cursor.__iter__()


class PostgresConnection(DatabaseConnection):
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
        cursor = self.ds.cursor()

        if config.sqldebug:
            return CursorDebugWrapper(cursor)
        else:
            return cursor

    def execute(self, command, parameters=()):
        if isinstance(command, sql.Part):
            if parameters:
                raise ValueError("Can’t provide parameters with  "
                                 "sqlclasses.sql statement.")
            command, parameters = self.backend.rollup(command)

        cc = self.cursor()
        cc.execute(command, parameters)
        return cc

    def query(self, command, parameters=(), dbobject_class=dbobject):
        if isinstance(command, sql.Part):
            if parameters:
                raise ValueError("Can’t provide parameters with "
                                 "sqlclasses.sql statement.")
            command, parameters = self.backend.rollup(command)

        with self.cursor() as cc:
            cc.execute(command, parameters)
            return dbobject_class.__result_class__(cc, dbobject_class)

    def select_one(self, command, parameters=(), dbobject_class=dbobject):
        if isinstance(command, sql.Part):
            if parameters:
                raise ValueError("Can’t provide parameters with "
                                 "sqlclasses.sql statement.")
            command, parameters = self.backend.rollup(command)

        with self.cursor() as cc:
            cc.execute(command, parameters)
            tpl = cc.fetchone()
            if tpl is None:
                return None
            else:
                return dbobject_class(cc.description, tpl)

    def query_one(self, command, parameters=()):
        if isinstance(command, sql.Part):
            if parameters:
                raise ValueError("Can’t provide parameters with "
                                 "sqlclasses.sql statement.")
            command, parameters = self.backend.rollup(command)

        with self.cursor() as cc:
            cc.execute(command, parameters)
            return cc.fetchone()

    def commit(self):
        self.ds.commit()

    def rollback(self):
        self.ds.rollback()

    def insert_from_dict(self, relation, d, retrieve_id=True,
                         sequence_name=None):
        if sequence_name is not None:
            retrieve_id = True

        command = sql.insert(relation, list(d.keys()), [ d, ])

        with self.cursor() as cc:
            command, params = self.backend.rollup(command)
            cc.execute(command, params)

            if not "id" in d and retrieve_id:
                if sequence_name is None:
                    if isinstance(relation, sql.relation):
                        name = relation.name.name
                    else:
                        name = str(relation)
                    sequence_name = '%s_id_seq' % name

                cc.execute("SELECT CURRVAL('%s')" % sequence_name)
                id, = cc.fetchone()
                return id
            else:
                return None
