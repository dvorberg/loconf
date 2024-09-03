import os.path as op, datetime
import datetime, types

from termcolor import colored
from sqlclasses import sql

from .. import config

class DbUsageException(Exception): pass

class Result(list):
    def __init__(self, cursor, dbobject_class, clauses=[]):
        self.dbobject_class = dbobject_class

        self.where = None
        self._count = None
        if clauses:
            for clause in clauses:
                if isinstance(clause, sql.where):
                    self.where = clause
                    break

        def generator():
            for tpl in cursor:
                yield dbobject_class(cursor.description, tpl)
        list.__init__(self, generator())

    def __getitem__(self, key):
        if isinstance(key, slice):
            ret = self.__class__([], self.dbobject_class, [self.where])
            for a in super().__getitem__(key):
                ret.append(a)
            return ret
        else:
            return super().__getitem__(key)

    def count(self):
        """
        Issue a SELECT COUNT(*) SQL query for this dbclass and where
        clause.  Raises ValueError if not sql.where() clause was used
        when selecting this result.
        """
        if self.where:
            if self._count is None:
                self._count =  self.dbobject_class.count(self.where)

            return self._count
        else:
            raise DbUsageException(
                "No WHERE clause provided with this result.")

class SQLRepresentation(type):
    def __new__(cls, name, bases, dct):
        ret = super().__new__(cls, name, bases, dct)

        schema = None
        if ret.__schema__ is None:
            for base in bases:
                if getattr(base, "__schema__", None) is not None:
                    schema = base.__schema__
                    break
        else:
            schema = ret.__schema__

        if bases != ( object, ):
            if ret.__relation__ is None:
                ret.__relation__ = sql.relation(name, schema)
            elif type(ret.__relation__) is str:
                ret.__relation__ = sql.relation(ret.__relation__, schema)
            else:
                if not isinstance(ret.__relation__, sql.relation):
                    raise TypeError(
                        "__relation__ must be string or sql.relation instance.")

            if ret.__view__ is None:
                ret.__view__ = ret.__relation__
            elif type(ret.__view__) is str:
                ret.__view__ = sql.relation(ret.__view__, schema)
            else:
                if not isinstance(ret.__relation__, sql.relation):
                    raise TypeError(
                        "__view__ must be string or sql.relation instance.")

        return ret

class dbobject(object, metaclass=SQLRepresentation):
    __schema__ = None
    __relation__ = None
    __view__ = None
    __result_class__ = Result
    __primary_key_column__ = "id"

    def __init__(self, description, values):
        if values is None:
            raise ValueError("Can’t construct dbobject form None.")

        self._column_names = []
        for column, value in zip(description, values):
            try:
                setattr(self, column.name, value)
            except AttributeError:
                #raise AttributeError("Can’t set " + column.name)
                setattr(self, "_" + column.name, value)

            self._column_names.append(column.name)

        self.update_db = self.update_db_instance

    @classmethod
    def from_dict(cls, data):
        self = cls( (), () )
        for key, value in data.items():
            try:
                setattr(self, key, value)
            except AttributeError:
                #raise AttributeError("Can't set attribute %s to %s" % (
                #    key, repr(value)))
                setattr(self, "_" + key, value)
        return self

    def as_dict(self):
        ret = {}
        for name, value in self.__dict__.items():
            if not name.startswith("__") and \
               not type(value) is types.MethodType:
                ret[name] = value
        return ret

    @classmethod
    def primary_key_literal(cls, value):
        return sql.find_literal_maybe(value)

    @classmethod
    def primary_key_where(cls, value):
        # Return an sql.where() instance identifying this dbobject to the db.
        literal = cls.primary_key_literal(value)
        return sql.where(cls.__primary_key_column__, " = ", literal)

    @classmethod
    def update_db(cls, primary_key, **data):
        command = sql.update(cls.__relation__ or cls.__view__,
                             cls.primary_key_where(primary_key), data)
        execute(command)

    def update_db_instance(self, **data):
        self.__class__.update_db(getattr(self, self.__primary_key_column__),
                                         **data)

    @classmethod
    def select_query(cls, *clauses):
        return sql.select("*", [cls.__view__,], *clauses)

    @classmethod
    def delete(cls, where):
        execute(sql.delete(cls.__view__, where))

    @classmethod
    def empty(cls):
        query = cls.select_query(sql.where("false"))
        with config.dbconn.cursor() as c:
            query, params = rollup_sql(query)
            c.execute(query, params)
            values = []
            for a in c.description:
                values.append(None)
            return cls(c.description, values)

    @classmethod
    def count(cls, *clauses):
        query = sql.select("COUNT(*)", [cls.__view__,], *clauses)
        query, params = rollup_sql(query)
        with config.dbconn.cursor() as cc:
            cc.execute(query, params)
            count, = cc.fetchone()
        return count

    @classmethod
    def select(cls, *clauses):
        with config.dbconn.cursor() as c:
            query = cls.select_query(*clauses)
            query, params = rollup_sql(query)
            c.execute(query, params)
            return cls.__result_class__(c, cls, clauses)

    @classmethod
    def select_by_primary_key(cls, value):
        return cls.select_one(cls.primary_key_where(value))

    @classmethod
    def select_one(cls, *clauses):
        for clause in clauses:
            if isinstance(clause, sql.limit):
                break
        else:
            clauses = list(clauses)
            clauses.append(sql.limit(1))

        result = cls.select(*clauses)
        if len(result) == 0:
            return None
        else:
            return result[0]
