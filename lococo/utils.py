import re
from tabulate import tabulate

from . import config, debug
from .language.parser import Parser

def read_names_file(fp):
    parser = Parser()
    parser.parse(fp)
    return dict( [(value, name,)
                  for (name, value) in parser.variables.items()] )

class VehicleIdentifyerParseError(Exception):
    pass

class UnknownVehicle(Exception):
    pass

class AmbiguousAddress(Exception):
    pass


class VehicleIdentifyer(object):
    def __init__(self, cab:int, vehicle_id:str|None):
        self.cab = cab
        self.vehicle_id = vehicle_id

    vehicle_identifyer_re = re.compile(r"^(\d+)(?::(\w*))?$|^(\w+)$")
    @classmethod
    def parse(cls, s:str):
        """
        There are three ways to specify a vehicle:
        - <int>        Decoder (“cab”) address (with vehicle_id = None).
                       Most likely a locomotive.
        - <int>:<str>  Decoder (“cab”) address with a vehicle_id set.
                       Part of a set of vehicles with the same address.
        - <str>        A roster identifyer. cab and vehicle_id need to be loaded
                       from the database.
        Vehicle and roster IDs must not contain space characters.
        """
        from .database.controllers import (vehicle_by_id, vehicle_by_address,
                                           vehicle_count_by_address)

        match = cls.vehicle_identifyer_re.match(s)
        if match is None:
            raise VehicleIdentifyerParseError(s)
        else:
            cab, vehicle_id, roster_id = match.groups()

            if cab is not None:
                cab = int(cab)
                count_on_cab = vehicle_count_by_address(cab)
                if count_on_cab is None or count_on_cab == 0:
                    raise UnknownVehicle(s)
                else:
                    if vehicle_id is None:
                        if count_on_cab != 1:
                            raise AmbiguousAddress(
                                f"More than one vehicle with "
                                f"decoder address {cab}. "
                                f"For empty vehicle id use "
                                f"“<cab>:” syntax.")
                        else:
                            vehicle_id = ""
                    return vehicle_by_address(cab, vehicle_id)
            else:
                return vehicle_by_id(roster_id)

    def __repr__(self):
        return f"{self.cab}:{self.vehicle_id}"

def print_vehicle_table(vehicles):
    print(tabulate([ (v.nickname, v.id, v.designation,) for v in vehicles ],
                   headers=["Nickname", "Cab:id", "Designation"],
                   tablefmt='orgtbl'))

class CabAddressMismatch(Exception):
    pass

def verify_vehicle(vehicle):
    """
    Make sure the vehicle on the programming track is the one the user
    wants, i.e. stated on the command line. Raises CabAddressMismatch.
    """
    # Now go ahead and write the CVs to the decoder.
    # First off: Verify CAB number.
    debug("Reading decoder address …", end=" ")
    found_cab = config.station.readcab()
    if vehicle.address != found_cab:
        debug()
        raise CabAddressMismatch(f"Expected {vehicle} but found "
                                 f"address {found_cab}!")
    else:
        debug("verified!", color="green")
