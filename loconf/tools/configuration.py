#!/usr/bin/env python

"""
Read CVs from the locomotive currently on the programming track.
"""

import sys, argparse, datetime, re

from sqlclasses import sql
from tabulate import tabulate

from .. import config, debug
from ..utils import ( VehicleIdentifyer, print_vehicle_table,
                      verify_vehicle, CabAddressMismatch, )
from ..language import parse_file as parse_loconf_file
from ..station import StationException
from ..database.controllers import store_cvs, get_all_cvs, query_vehicles
from ..model import Vehicle
from . import common_args

def readcvs(args):
    cv_re = re.compile(r"(\d+)[-–](\d+)|(\d+)")
    def find_cvs(s):
        match = cv_re.match(s)
        if match is None:
            raise ValueError(f"Can’t parse CV number(s): “{s}”.")
        start, stop, single = match.groups()
        if single is not None:
            yield int(single)
        else:
            for a in range(int(start), int(stop)+1):
                yield a

    def ranges():
        for r in args.ranges:
            parts = r.split(",")
            for s in parts:
                for cv in find_cvs(s):
                    yield cv


    now = datetime.datetime.now()
    print(f"# CVs read from {args.vehicle} on {now.ctime()}",
          file=args.outfile)
    print(file=args.outfile)

    if args.names_file is None:
        names = {}
    else:
        names = read_names_file(args.names_file)

        print(f'include "{args.names_file.name}"', file=args.outfile)
        print("", file=args.outfile)

    cvs = sorted(list(set(ranges())))

    verify_vehicle(args.Vehicle)

    to_be_stored = {}
    try:
        for cv in cvs:
            debug("Reading CV", cv, end=" ")
            value = config.station.readcv(cv)

            if cv in names:
                left_hand = names[cv]
            else:
                left_hand = cv

            debug(left_hand, ":=", value, color="light_grey")

            print(left_hand, ":=", value, file=args.outfile)

            to_be_stored[cv] = value
    except StationException:
        raise
    finally:
        # Store the read cvs in the database.
        if not args.dont_update:
            store_cvs(args.vehicle, to_be_stored,
                      args.revision_comment)

def writecvs(args):
    # Get the CV revision to be written from the input file.
    file_cvs = parse_loconf_file(args.infile)

    # Retrieve the current set of CVs from the database.
    if args.all:
        db_cvs = {}
    else:
        db_cvs = get_all_cvs(args.vehicle)

    # Compile a list of CVs that need to be written.
    write_cvs = {}
    for cv, new_value in file_cvs.items():
        current_value = db_cvs.get(cv, None)
        if current_value is None or current_value != new_value:
            write_cvs[cv] = new_value

    # Weed out None values.
    write_cvs = dict([ (cv, value)
                       for cv, value in write_cvs.items()
                       if value is not None ])

    if len(write_cvs) == 0:
        print("No changed CVs found. Input file is identical to latest "
              "database revision.", file=sys.stderr)
    else:
        verify_vehicle(args.vehicle)

        # Write phase.
        to_be_stored = {}
        try:
            for cv, value in write_cvs.items():
                debug(cv, ":=", value, color="light_grey")
                config.station.writecv(cv, value)
                to_be_stored[cv] = value
        except StationException:
            raise
        finally:
            if not args.dont_update:
                store_cvs(args.vehicle, to_be_stored,
                          args.revision_comment)


def listrevs(args):
    pass

def showrev(args):
    pass

def readcab(args):
    cab = config.station.readcab()
    print("Found:", cab)

    vehicles = query_vehicles(sql.where("address = %i" % cab))
    if len(vehicles) == 0:
        print("No vehicles with on the roster with address %i." % cab)
    else:
        print()
        print_vehicle_table(vehicles)


def writecab(args):
    if args.new < 1:
        raise ValueError("Decoder (“cab”) addresses must be > 1.")

    if args.old >= 1:
        found_cab = config.station.readcab()
        if found_cab != args.old:
            raise CabAddressMismatch(f"Vehicle on the programming track has "
                                     f"address {found_cab} not {args.old} as "
                                     f"required.")

    config.station.writecab(args.new)

def reset(args):
    verify_vehicle(args.vehicle)
    config.station.writecv(8, args.value)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    common_args.add_debug(parser)
    parser.set_defaults(func=None)

    subparsers = parser.add_subparsers(help="Command Help")

    # Read CVs
    cp = subparsers.add_parser("readcvs",
                               help="Read CVs from a decoder and print them"
                               "save them to a .loconf file.")
    cp.set_defaults(func=readcvs)
    common_args.add_identification(cp, help="To make sure you are reading the "
                                   "correct locomotives’s CVs, provide the "
                                   "roster identification (cab:vehicle_id "
                                   "or roster id) of the loco on the "
                                   "programming track here.")
    common_args.add_names_file(cp)
    common_args.add_revision_comment(cp)
    cp.add_argument("-o", "--outfile", type=argparse.FileType('w'),
                    default=sys.stdout, help="Output file. "
                    "Defaults to stdout.")
    cp.add_argument("ranges", nargs="+",
                    help= "CV numbers may be single numbers, separated by "
                    "comma or space or ranges as in start-stop.")
    cp.add_argument("-U", "--dont-update", default=False,
                    action="store_true",
                    help="Don’t update the database with the CVs read.")


    # Write CVs
    cp = subparsers.add_parser("writecvs",
                               help="Write CVs from a decoder from a loconf "
                               "file.")
    cp.set_defaults(func=writecvs)
    common_args.add_identification(cp)

    cp.add_argument("infile",
                    type=argparse.FileType("r"),
                    help=".loconf file to read CVs from.")

    common_args.add_revision_comment(cp)

    cp.add_argument("-U", "--dont-update", default=False, action="store_true",
                    help="Don’t update the database with the CVs written.")
    cp.add_argument("-a", "--all", default=False, action="store_true",
                    help="Write all values from the loconf file to the "
                    "decoder even if they are identical to the ones in the "
                    "database.")

    cp = subparsers.add_parser("readcab",
                               help="Read the decoder (“cab”) address or the "
                               "vehicle currently on the programming track.")
    cp.set_defaults(func=readcab)

    cp = subparsers.add_parser("writecab",
                               help="Write the decoder (“cab”) address or the "
                               "vehicle currently on the programming track.")
    cp.set_defaults(func=writecab)
    cp.add_argument("old", type=int, help="Provide the "
                    "old decoder (“cab”) address. Use any value < 1 to "
                    "disable this safety check at you own risk.")
    cp.add_argument("new", type=int, help="New decoder (“cab”) address for the "
                    "vehicle on the programming track.")

    cp = subparsers.add_parser("reset",
                               help="Write to CV 8 which resets the decoder. "
                               "This will likely reset the address (“cab”) on the "
                               "decoder to the default value (3?) but not affect "
                               "loconf’s database or configuration revisions "
                               "associated with the current address.")
    cp.set_defaults(func=reset)
    common_args.add_identification(cp)
    cp.add_argument("-V", "--value", type=int, default=8,
                    help="Value to write to CV 8. Defaults to 8.")

    args = parser.parse_args()
    common_args.set_debug_config(args)

    if args.func is None:
        parser.error("Please specify a command.")
    else:
        args.func(args)

if __name__ == "__main__":
    main()
