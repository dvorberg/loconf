#!/usr/bin/env python

"""
Read CVs from the locomotive currently on the programming track.
"""

import sys, argparse, pathlib, re, datetime

from loconf import config, debug

from . import common_args
from .utils import read_names_file

cv_re = re.compile(r"(\d+)-(\d+)|(\d+)")
def main():
    parser = argparse.ArgumentParser(description=__doc__)

    common_args.debug(parser)
    common_args.cab(parser, "To make sure you are changing the "
                    "correct locomotives’s CVs, provide the cab number  "
                    "of the loco on the programming track here."),
    common_args.names_file(parser)
    common_args.revision_comment(parser)

    parser.add_argument("-o", "--outfile", type=argparse.FileType('w'),
                        default=sys.stdout, help="Output file. "
                        "Defaults to stdout.")

    parser.add_argument("ranges", nargs="+",
                        help= "CV numbers may be single numbers, separated by "
                        "comma or space or ranges as in start-stop.")

    args = parser.parse_args()

    common_args.set_debug_config(args)

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
    print(f"# CVs read from address {args.cab} on {now.ctime()}",
          file=args.outfile)
    print(file=args.outfile)


    if args.names_file is None:
        names = {}
    else:
        names = read_names_file(args.names_file)

        print(f'include "{args.names_file.name}"', file=args.outfile)
        print("", file=args.outfile)

    cvs = sorted(list(set(ranges())))

    station = config.station

    debug("Reading cab number…", end=" ")
    found_cab = station.readcab()
    if args.cab != found_cab:
        debug()
        parser.error(f"Expected cab {args.cab} but found {found_cab}!")
    else:
        debug("verified!", color="green")

    to_be_stored = {}
    try:
        for cv in cvs:
            debug("Reading CV", cv, end=" ")
            value = station.readcv(cv)

            if cv in names:
                left_hand = names[cv]
            else:
                left_hand = cv

            debug(left_hand, ":=", value, color="grey")

            print(left_hand, ":=", value, file=args.outfile)
    except StationException:
        raise
    finally:
        # Store the read cvs in the database.
        config.database.store(cab, to_be_stored, args.revision_comment)


if __name__ == "__main__":
    main()
