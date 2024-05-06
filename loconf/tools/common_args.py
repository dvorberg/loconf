from .. import config
import argparse

def debug(parser:argparse.ArgumentParser, debug=True, com=True, sql=True):
    if debug:
        parser.add_argument("-d", "--debug", action="store_true",
                            help="Output debug information to stderr.")

    if com:
        parser.add_argument("-dc", "--comdebug", action="store_true",
                            help="Output communications with the station "
                            "to stderr.")
    if sql:
        parser.add_argument("-ds", "--sqldebug", action="store_true",
                            help="Output SQL commands and queries to stderr.")

def cab(parser:argparse.ArgumentParser, help=None):
    parser.add_argument("-c", "--cab", type=int, required=True,
                        help=help or "Loco address (cab number).")

def names_file(parser:argparse.ArgumentParser):
    parser.add_argument("-n", "--names-file", type=argparse.FileType('r'),
                        default=None, help="Read variable name definitions "
                        "from this file. These names will be used as left "
                        "hand operands as in “name” := “value”.")

def revision_comment(parser:argparse.ArgumentParser):
    parser.add_argument("-C", "--revision-comment", default="",
                        help="Remarks stored in the database "
                        "along with the CVs read.")

def set_debug_config(args):
    debug_conf = {}
    for d in ("debug", "sqldebug", "comdebug"):
        if getattr(args, d, False):
            debug_conf[d] = True
    config.update(debug_conf)
