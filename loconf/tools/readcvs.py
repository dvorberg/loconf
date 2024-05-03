#!/usr/bin/env python

import sys, argparse, pathlib, re, datetime
from loconf import config, debug

from loconf.language.parser import Parser

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
    parser.add_argument("-o", "--outfile", type=argparse.FileType('w'),
                        default=sys.stdout, help="Output file. "
                        "Defaults to stdout.")
    parser.add_argument("-n", "--names-file", type=argparse.FileType('r'),
                        default=None, help="Read variable name definitions "
                        "from this file. These names will be used as left "
                        "hand operands as in “name” := “value”.")
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

    now = datetime.datetime.now()
    print(f"CVs read from address {args.cab} on {now.ctime()}",
          file=args.outfile)
    print(file=args.outfile)

    if args.names_file is None:
        names = {}
    else:
        parser = Parser()
        parser.parse(args.names_file)
        names = dict( [(value, name,)
                       for (name, value) in parser.variables.items()] )

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

    for cv in cvs:
        debug("Reading CV", cv, end=" ")
        value = station.readcv(cv)

        if cv in names:
            left_hand = names[cv]
        else:
            left_hand = cv

        debug(left_hand, ":=", value, color="grey")

        print(left_hand, ":=", value, file=args.outfile)

if __name__ == "__main__":
    main()
