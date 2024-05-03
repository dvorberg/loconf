#!/usr/bin/env python

import argparse, pathlib, re
from loconf import config, debug

cv_re = re.compile(r"(\d+)-(\d+)|(\d+)")
def main():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("-d", "--debug", action="store_true",
                        help="Output debug information to stderr.")
    parser.add_argument("-dc", "--comdebug", action="store_true",
                        help="Output communications with the station "
                        "to stderr.")
    parser.add_argument("-ds", "--sqldebug", action="store_true",
                        help="Output SQL commands and queries to stderr.")

    parser.add_argument("-c", "--cab", type=int, required=True,
                        help="To make sure you are changing the correct "
                        "locomotives’s CVs, provide the cab number of the "
                        "loco on the programming track here.")
    parser.add_argument("ranges", nargs="+",
                        help= "CV numbers may be single numbers, separated by "
                        "comma or space or ranges as in start-stop.")

    args = parser.parse_args()

    debug_conf = {}
    for d in ("debug", "sqldebug", "comdebug"):
        if getattr(args, d):
            debug_conf[d] = True
    config.update(debug_conf)


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

    cvs = sorted(list(set(ranges())))

    station = config.station

    debug("Reading cab number…", end=" ")
    found_cab = station.readcab()
    if args.cab != found_cab:
        debug()
        parser.error(f"Expected cab {args.cab} but found {found_cab}!")
    else:
        debug("verified!", color="green")

    for cv in cvs:
        debug("Reading CV", cv)
        value = station.readcv(cv)
        print(cv, ":=", value)

if __name__ == "__main__":
    main()
