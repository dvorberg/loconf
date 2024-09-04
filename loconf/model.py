#!/usr/bin/env python

from .database.object import dbobject

class Revision(dbobject):
    __relation__ = "revision"

class Vehicle(dbobject):
    __relation__ = "roster"

    # The primary key in the database is (address, vehicle_id). My miniorm
    # can’t do that. The identifyer column is unique, though, and may stand
    # in for the “real” primary key here.
    __primary_key_column__ = ( "identifyer", )

    def __repr__(self):
        if self.vehicle_id:
            addr = f"{self.address}:{self.vehicle_id}"
        else:
            addr = str(self.address)

        return f"<Vehicle '{self.identifyer}' ({addr})>"
