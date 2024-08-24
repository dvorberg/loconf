#!/usr/bin/env python

"""
Write CVs from the locomotive currently on the programming track.
"""

import sys, argparse, pathlib, re, datetime

from loconf import config, debug
from loconf.station import StationException
from loconf.language import parse_file as parse_loconf_file

from . import common_args
from .utils import read_names_file

cv_re = re.compile(r"(\d+)[-–](\d+)|(\d+)")
def main():
    parser = argparse.ArgumentParser(description=__doc__)

    common_args.debug(parser)
    common_args.cab(parser, "To make sure you are changing the "
                    "correct locomotives’s CVs, provide the cab number  "
                    "of the loco on the programming track here."),
    common_args.revision_comment(parser)
    parser.add_argument("infile",
                        type=argparse.FileType("r"),
                        help=".loconf file to read CVs from.")

    args = parser.parse_args()
    common_args.set_debug_config(args)

    # Get the CV revision to be written from the input file.
    file_cvs = parse_loconf_file(args.infile)

    # Retrieve the current set of CVs from the database.
    db_cvs = config.database.get_all(args.cab)

    # Compile a list of CVs that need to be written.
    write_cvs = {}
    for cv, new_value in file_cvs.items():
        current_value = db_cvs.get(cv, None)
        if current_value is None or current_value != new_value:
            write_cvs[cv] = new_value

    # Weed out None values
    write_cvs = dict([ (cv, value)
                       for cv, value in write_cvs.items()
                       if value is not None ])

    if len(write_cvs) == 0:
        print("No changed CVs found. Input file is identical to latest "
              "database revision.", file=sys.stderr)
    else:
        # Now go ahead and write the CVs to the decoder.
        # First off: Verify CAB number.
        debug("Reading cab number…", end=" ")
        found_cab = config.station.readcab()
        if args.cab != found_cab:
            debug()
            parser.error(f"Expected cab {args.cab} but found {found_cab}!")
        else:
            debug("verified!", color="green")

        # Write phase.
        to_be_stored = {}
        try:
            for cv, value in write_cvs.items():
                debug(cv, ":=", value, color="grey")
                config.station.writecv(cv, value)
                to_be_stored[cv] = value
        except StationException:
            raise
        finally:
            config.database.store(args.cab, to_be_stored,
                                  args.revision_comment)


if __name__ == "__main__":
    main()
