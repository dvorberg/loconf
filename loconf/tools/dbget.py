"""
List revisions and dates from the database for a cab number.
"""

import sys, argparse, pathlib

from loconf import config, debug
from loconf.language.parser import Parser
from . import common_args

def main():
    parser = argparse.ArgumentParser(description=__doc__)

    common_args.debug(parser, com=False)
    parser.add_argument("-r", "--revision-id", type=int, default=None,
                        help="Specify a particular revision. "
                        "Use “lsdbrevisions” to list available ids.")

    common_args.names_file(parser)
    parser.add_argument("-o", "--outfile", type=argparse.FileType('w'),
                        default=sys.stdout, help="Output file. "
                        "Defaults to stdout.")


    parser.add_argument("cab", type=int,
                        help="Address (cab number) for which to retrieve CVs")

    args = parser.parse_args()
    common_args.set_debug_config(args)

    if args.revision_id is None:
        cvs = config.database.get_all(args.cab)
    else:
        cvs = config.database.get_revision(args.revision_id)

    if not cvs:
        print("No such cab/revsion combination. Check lsdbrevisions.")
        sys.exit(1)

    print(cvs)

if __name__ == "__main__":
    main()
