#!/usr/bin/env python

from .database.object import dbobject

class Revision(dbobject):
    __relation__ = "revision"

class Vehicle(dbobject):
    __relation__ = "roster"
    __primary_key__ = ( "address", "vehicle_id", )

    def __repr__(self):
        if self.vehicle_id:
            addr = f"{self.address}:{self.vehicle_id}"
        else:
            addr = str(self.address)

        return f"<Vehicle '{self.identifyer}' ({addr})>"
