#!/usr/bin/env python

"""
Read CVs from the locomotive currently on the programming track.
"""

import sys, argparse, pathlib, re, datetime

from sqlclasses import sql
from tabulate import tabulate

from ..database import controllers as db
from ..utils import (VehicleIdentifyer, VehicleIdentifyerParseError,
                     print_vehicle_table)
from . import common_args

vehicle_re = re.compile(r"(\d+)(?::(\w*))")
def create(args):
    match = vehicle_re.match(args.vehicle)
    if match is None:
        raise VehicleIdentifyerParseError(args.vehicle)
    else:
        cab, vehicle_id = match.groups()

    db.create_roster_entry(args.nickname,
                           cab,
                           vehicle_id,
                           args.designation)

def update(args):
    data = { "address": args.cab,
             "vehicle_id": args.vehicle_id,
             "designation": args.designation,
             "nickname": args.nickname }

    # Filter out None and empty values.
    data = dict([ (n, v) for (n, v) in data.items() if v])

    if len(data) == 0:
        raise ValueError("No values are to be changed.")
    else:
        db.update_vehicle(args.vehicle, data)

def delete(args):
    db.delete_vehicle(args.vehicle)

def list_entries(args):
    vehicles = db.query_vehicles(None)
    print_vehicle_table(vehicles)
    print()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    common_args.add_debug(parser)
    parser.set_defaults(func=None)

    subparsers = parser.add_subparsers(help="Command Help")

    # Create
    cp = subparsers.add_parser("create", help="Create roster entry")
    cp.add_argument("-d", "--designation", default="",
                    help="Vehicle designation for pretty printing")
    cp.add_argument("vehicle",
                    help="Vehicle identification by decoder (“cab”) address "
                    "or cab:id")
    cp.add_argument("nickname", help="Text nickname for this roster entry "
                    "to be used on the command line")
    cp.set_defaults(func=create)

    # Update
    cp = subparsers.add_parser("update", help="Update roster entry")
    common_args.add_identification(cp)
    cp.add_argument("-c", "--cab", type=int,
                    help="Decoder address (cab number).")
    cp.add_argument("-V", "--vehicle-id", type=str, default="",
                    help="Secondary vehicle identifyer if several "
                    "vehicles share one decoder (“cap”) address")
    cp.add_argument("-n", "--nickname", default=None,
                    help="Roster identifyer")
    cp.add_argument("-d", "--designation", default=None,
                    help="Vehicle designation for pretty printing")
    cp.set_defaults(func=update)

    # Delete
    cp = subparsers.add_parser("delete", help="Delete an entry from the roster")
    common_args.add_identification(cp)
    cp.set_defaults(func=delete)

    # List
    cp = subparsers.add_parser("list", help="List roster entries to console")
    cp.set_defaults(func=list_entries)

    args = parser.parse_args()
    common_args.set_debug_config(args)

    if args.func is None:
        parser.error("Please specify a command.")
    else:
        args.func(args)

if __name__ == "__main__":
    main()
