#!/usr/bin/env python

"""
Read CVs from the locomotive currently on the programming track.
"""

import sys, argparse, pathlib, re, datetime

from sqlclasses import sql
from tabulate import tabulate

from ..database import controllers as db
from ..utils import VehicleIdentifyer, print_vehicle_table
from . import common_args

def create(args):
    db.create_roster_entry(args.identifyer,
                                      args.cab,
                                      args.vehicle_id,
                                      args.name)

def update(args):
    data = { "address": args.cab,
             "vehicle_id": args.vehicle_id,
             "name": args.name,
             "identifyer": args.identifyer }

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
    cp.add_argument("identifyer", help="Text identifyer for this roster entry "
                    "to be used on the command line")
    cp.add_argument("-c", "--cab", type=int, required=True,
                    help="Decoder address (cab number).")
    cp.add_argument("-V", "--vehicle-id", type=str, default="",
                    help="Secondary vehicle identifyer if several "
                    "vehicles share one decoder (“cap”) address")
    cp.add_argument("-n", "--name", default="",
                    help="Vehicle name for pretty printing")
    cp.set_defaults(func=create)

    # Update
    cp = subparsers.add_parser("update", help="Update roster entry")
    common_args.add_identification(cp)
    cp.add_argument("-c", "--cab", type=int,
                    help="Decoder address (cab number).")
    cp.add_argument("-V", "--vehicle-id", type=str, default="",
                    help="Secondary vehicle identifyer if several "
                    "vehicles share one decoder (“cap”) address")
    cp.add_argument("-i", "--identifyer", default=None,
                    help="Roster identifyer")
    cp.add_argument("-n", "--name", default=None,
                    help="Vehicle name for pretty printing")
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
