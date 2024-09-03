from sqlclasses import sql

from . import config, sqldebug
from .model import Revision, Vehicle

class Database(object):
    """
    Abstract base class for CV databases
    """
    def store_cvs(self, vehicle:Vehicle, cvs:list[int], revision_comment=""):
        raise NotImplementedError()

    def get_cv(self, cab:int, cv:int):
        raise NotImplementedError()

    def get_cvs(self, cab:int):
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

    def query(self, *query, cursor=None):
        cursor = self.execute(*query, cursor=cursor)
        return list(cursor.fetchall())

    def query_one(self, *query, cursor=None):
        result = self.query(*query, cursor=cursor)
        if result:
            tpl = result[0]
            if len(tpl) == 1:
                return tpl[0]
            else:
                return tpl
        else:
            return None

    def commit(self):
        self.ds.commit()

    def store_cvs(self, vehicle:Vehicle,
                  cvs:dict[int, int], revision_comment=""):
        # Remove None values from cvs
        cvs = dict([ (name, value)
                     for (name, value) in cvs.items()
                     if value is not None ])
        if not cvs:
            return

        # Create a revision entry.
        cursor = self.execute(sql.insert.from_dict(
            "revision", { "address": vehicle.address,
                          "vehicle_id": vehicle.vehicle_id,
                          "comment": revision_comment, }))
        cursor.execute("SELECT CURRVAL('revision_id_seq')")
        revision_id, = cursor.fetchone()

        # Create value entries for each of the CV.
        self.execute(sql.insert.from_dict(
            "value", *[ {"revision_id": revision_id, "cv": cv, "value": value}
                        for ( cv, value ) in cvs.items() ]))
        self.commit()

    def get_cv(self, vehicle:Vehicle, cv:int):
        """
        Return the latest known entry for “cv” for “vehicle”.
        """
        result = self.get_all(vehicle, cv)
        return result.get(cv, None)

    def get_all_cvs(self, vehicle:Vehicle, cv:int|None=None):
        """
        Return the latest known CV settings on “vehicle” as a dict
        (optinally limit the query to “cv”.)
        """
        query = """\
            WITH latest AS (
                SELECT cv, address, vehicle_id, MAX(revision_id) AS revision_id
                  FROM value
                  LEFT JOIN revision ON revision_id = revision.id
                  GROUP BY cv, address, vehicle_id
            )
            SELECT latest.cv, value
              FROM latest
              LEFT JOIN value
                     ON latest.cv = value.cv
                    AND latest.revision_id = value.revision_id
             WHERE address = %s AND vehicle_id = %s
             ORDER BY cv"""
        params = ( vehicle.address, vehicle.vehicle_id, )

        if cv is not None:
            query += " AND cv = %s"
            params += ( cv, )

        cursor = self.cursor()
        cursor.execute(query, params)
        return dict(cursor.fetchall())

    def get_revision(self, vehicle:Vehicle, revision_id:int):
        """
        Retrieve the latest know CV settings for “vehicle” at the
        time of the identified revision.
        """
        query = """\
            WITH latest AS (
                SELECT cv, cab, vid
                       MAX(revision_id) AS revision_id
                  FROM value
                  LEFT JOIN revision ON revision_id = revision.id
                  WHERE revision_id <= %s
                  GROUP BY cv, address, vehicle_id
            )
            SELECT latest.cv, value
              FROM latest
              LEFT JOIN value
                     ON latest.cv = value.cv
                    AND latest.revision_id = value.revision_id
             WHERE address = cab AND vehicle_id = vid
             ORDER BY cv"""
        params = ( revision_id, cab, )

        cursor = self.cursor()
        cursor.execute(query, params)
        return dict(cursor.fetchall())

    def get_revisions(self, vehicle:Vehicle):
        cursor = self.cursor()
        cursor.execute("SELECT id, address, vehicle_id, comment, ctime "
                       "  FROM revision"
                       " WHERE address = %s AND vehicle_id = %s"
                       " ORDER BY id ASC", ( vehicle.address,
                                             vehicle.vehicle_id, ))
        return [ Revision(*tpl) for tpl in cursor.fetchall() ]

    def vehicle_by_address(self, cab:int, vehicle_id:str):
        result = self.query_vehicles(sql.where("address = %i " % cab,
                                               "AND vehicle_id = ",
                                               sql.string_literal(vehicle_id)))
        if result:
            return result[0]
        else:
            raise VehicleNotFound("Address:{cab} id:“{vehicle_id}”")

    def vehicle_by_id(self, roster_id:str):
        result = self.query_vehicles(sql.where("identifyer = ",
                                               sql.string_literal(roster_id)))
        if result:
            return result[0]
        else:
            raise VehicleNotFound("ID:{roster_id}")

    def query_vehicles(self, where, orderby="identifyer"):
        query = sql.select( ("address", "vehicle_id", "identifyer", "name",),
                            ("roster",),
                            where, sql.orderby(orderby))
        result = self.query(query)
        return [ Vehicle(*tpl) for tpl in result ]

    def create_roster_entry(self, identifyer:str,
                            cab:int, vehicle_id:str,
                            name:str):
        cursor = self.execute(sql.insert.from_dict(
            "roster", { "identifyer": identifyer,
                        "address": cab,
                        "vehicle_id": vehicle_id,
                        "name": name, }))
        self.commit()

    def update_vehicle(self, vehicle, data):
        where = sql.where("identifyer = ",
                          sql.string_literal(vehicle.identifyer))
        self.execute(sql.update("roster", where, data))
        self.commit()

    def delete_vehicle(self, vehicle):
        where = sql.where("identifyer = ",
                          sql.string_literal(vehicle.identifyer))
        self.execute(sql.delete("roster", where))
        self.commit()
