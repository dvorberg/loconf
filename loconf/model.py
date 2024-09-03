import dataclasses, datetime

@dataclasses.dataclass
class Revision(object):
    id: int
    address: int
    comment: str
    ctime: datetime.datetime

@dataclasses.dataclass
class Vehicle(object):
    address: int
    vehicle_id: str
    identifyer: str
    name: str

    def __repr__(self):
        if self.vehicle_id:
            addr = f"{self.address}:{self.vehicle_id}"
        else:
            addr = str(self.address)

        return f"<Vehicle '{self.identifyer}' ({addr})>"
