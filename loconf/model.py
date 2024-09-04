#!/usr/bin/env python

from .database.object import dbobject
from .utils import VehicleIdentifyer

class Revision(dbobject):
    __relation__ = "revision"

class Vehicle(dbobject):
    __relation__ = "roster"

    # The primary key in the database is (address, vehicle_id). My miniorm
    # can’t do that. The nickname column is unique, though, and may stand
    # in for the “real” primary key here.
    __primary_key_column__ = ( "nickname", )

    @property
    def id(self):
        return VehicleIdentifyer(self.address, self.vehicle_id)

    def __repr__(self):
        if self.vehicle_id:
            addr = f"{self.address}:{self.vehicle_id}"
        else:
            addr = str(self.address)

        return f"<Vehicle '{self.nickname}' ({addr})>"

    def __str__(self):
        return f"{self.designation or self.nickname} ({self.id})"
