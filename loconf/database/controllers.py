from sqlclasses import sql

from .. import config
from ..model import Vehicle, Revision

def store_cvs(vehicle:Vehicle,
              cvs:dict[int, int], revision_comment=""):
    # Remove None values from cvs
    cvs = dict([ (name, value)
                 for (name, value) in cvs.items()
                 if value is not None ])
    if not cvs:
        return

    # Create a revision entry.
    revision = Revision.insert_from_dict( {"address": vehicle.address,
                                           "vehicle_id": vehicle.vehicle_id,
                                           "comment": revision_comment, })
    # Create value entries for each of the CVs.
    config.dbconn.execute(sql.insert.from_dict(
        "value", *[ {"revision_id": revision.id, "cv": cv, "value": value}
                    for ( cv, value ) in cvs.items() ]))
    config.dbconn.commit()

def get_cv(vehicle:Vehicle, cv:int):
    """
        Return the latest known entry for “cv” for “vehicle”.
        """
    result = get_all_cvs(vehicle, cv)
    return result.get(cv, None)

def get_all_cvs(vehicle:Vehicle, cv:int|None=None):
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

    cursor = cursor.execute(query, params)
    return dict(cursor.fetchall())

def get_revision(vehicle:Vehicle, revision_id:int):
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

    cursor = config.dbconn.execute(query, params)
    return dict(cursor.fetchall())

def get_revisions(vehicle:Vehicle):
    cursor = config.dbconn.cursor()
    cursor.execute("SELECT id, address, vehicle_id, comment, ctime "
                   "  FROM revision"
                   " WHERE address = %s AND vehicle_id = %s"
                   " ORDER BY id ASC", ( vehicle.address,
                                         vehicle.vehicle_id, ))
    return [ Revision(*tpl) for tpl in cursor.fetchall() ]

def vehicle_by_address(cab:int, vehicle_id:str):
    result = query_vehicles(sql.where("address = %i " % cab,
                                      "AND vehicle_id = ",
                                      sql.string_literal(vehicle_id)))
    if result:
        return result[0]
    else:
        raise VehicleNotFound("Address:{cab} id:“{vehicle_id}”")

def vehicle_by_id(roster_id:str):
    result = query_vehicles(sql.where("nickname = ",
                                      sql.string_literal(roster_id)))
    if result:
        return result[0]
    else:
        raise VehicleNotFound("ID:{roster_id}")

def query_vehicles(where, orderby="nickname"):
    return Vehicle.select(where, sql.orderby(orderby))

def create_roster_entry(nickname:str,
                        cab:int, vehicle_id:str,
                        designation:str):
    Vehicle.insert_from_dict({ "nickname": nickname,
                               "address": cab,
                               "vehicle_id": vehicle_id,
                               "designation": designation, },
                             retrieve_id=False)
    config.dbconn.commit()

def update_vehicle(vehicle:Vehicle, data:dict):
    where = sql.where("nickname = ",
                      sql.string_literal(vehicle.nickname))
    config.dbconn.execute(sql.update("roster", where, data))
    config.dbconn.commit()

def delete_vehicle(vehicle:Vehicle):
    where = sql.where("nickname = ",
                      sql.string_literal(vehicle.nickname))
    config.dbconn.execute(sql.delete("roster", where))
    config.dbconn.commit()

def vehicle_count_by_address(address:int):
    return config.dbconn.query_one(f"SELECT COUNT(address) FROM roster "
                                   f" WHERE address = {address} "
                                   f" GROUP BY address ")
