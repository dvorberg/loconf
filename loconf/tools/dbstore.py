import argparse, pathlib

from loconf import config, debug
from loconf.language.parser import Parser
from . import common_args

def main():
    parser = argparse.ArgumentParser(description=__doc__)

    common_args.debug(parser, com=False)
    common_args.cab(parser, "Loco address (cab number) to associate which to "
                    "associate the CVs in the database")
    common_args.revision_comment(parser)

    parser.add_argument("infile", type=pathlib.Path,
                        help="A loconf file containing the CVs to be stored "
                        "in the database for “cab”")

    args = parser.parse_args()
    common_args.set_debug_config(args)

    parser = Parser()
    cvs = parser.parse(args.infile.open())

    config.database.store(args.cab, cvs, args.revision_comment)

if __name__ == "__main__":
    main()
