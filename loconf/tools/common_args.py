from .. import config
import argparse

from loconf.utils import VehicleIdentifyer

def add_debug(parser:argparse.ArgumentParser, debug=True, com=True, sql=True):
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

def add_identification(parser:argparse.ArgumentParser, help=None):
    parser.add_argument(
        "vehicle", type=VehicleIdentifyer.parse,
        help=help or "Vehicle identification by cap, cap:id, or "
        "roster identifyer")

def add_names_file(parser:argparse.ArgumentParser):
    parser.add_argument("-n", "--names-file", type=argparse.FileType('r'),
                        default=None, help="Read variable name definitions "
                        "from this file. These names will be used as left "
                        "hand operands as in “name” := “value”.")

def add_revision_comment(parser:argparse.ArgumentParser):
    parser.add_argument("-C", "--revision-comment", default="",
                        help="Remarks stored in the database "
                        "along with the CVs read.")

def set_debug_config(args):
    debug_conf = {}
    for d in ("debug", "sqldebug", "comdebug"):
        if getattr(args, d, False):
            debug_conf[d] = True
    config.update(debug_conf)
