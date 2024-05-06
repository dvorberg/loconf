"""
List revisions and dates from the database for a cab number.
"""

import argparse, pathlib

from loconf import config, debug
from loconf.language.parser import Parser
from . import common_args

def main():
    parser = argparse.ArgumentParser(description=__doc__)

    common_args.debug(parser, com=False)
    parser.add_argument("cab", type=int,
                        help="Address (cab number) for which to list revisions")

    args = parser.parse_args()
    common_args.set_debug_config(args)

    revisions = config.database.get_revisions(args.cab)

    for revision in revisions:
        print("{: >5} | {: >20} | {}".format(revision.id,
                                             revision.ctime.ctime(),
                                             revision.comment))

if __name__ == "__main__":
    main()
