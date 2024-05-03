import sys, os, pathlib, functools, tomllib, copy, termcolor, io


import icecream
icecream.install()
ic.disable()


def read_config_file(fp):
    return tomllib.load(fp)


class Configuration(object):
    def __init__(self, confdata):
        self.confdata = confdata

    @property
    def confdata(self):
        return dict(self._confdata.items())

    @confdata.setter
    def confdata(self, confdata:dict):
        self._confdata = confdata

        # Remove cached property values.
        for name, f in self.__class__.__dict__.items():
            if isinstance(f, functools.cached_property) \
               and name in self.__dict__:
                delattr(self, name)

        if self.debug:
            ic.enable()
        else:
            ic.disable()

    def update(self, data:dict):
        d = self.confdata
        d.update(data)
        self.confdata = d

    @property
    def debug(self):
        return bool(self._confdata.get("debug", False))

    @property
    def sqldebug(self):
        return bool(self._confdata.get("sqldebug", False))

    @property
    def comdebug(self):
        return bool(self._confdata.get("comdebug", False))

    @functools.cached_property
    def database(self):
        entry = self._confdata["database"]
        if type(entry) is str:
            # The the string as a path and open it as some database
            # format.
            pass
        else:
            typ = entry.get("type", "none")
            from . import database
            if typ == "psycopg2":
                return database.PostgresDatabase(entry.get("params"))
            else:
                raise ValueError(f"Unknown database type “{typ}”")

    @functools.cached_property
    def station(self):
        entry = self._confdata["station"]
        type = entry.get("type", None)
        if type == "dccex":
            params = copy.copy(entry)
            del params["type"]

            from .dccex.station import DCCEX_Station
            return DCCEX_Station(**params)
        else:
            raise ValueError(f"Unknown station type “{type}”")


config_file_path = pathlib.Path(pathlib.Path.home(), ".loconfrc.toml")

if config_file_path.exists():
    confdata = tomllib.load(config_file_path.open("rb"))
else:
    confdata = {}

config = Configuration(confdata)

def _debug(doit:bool, *args, color="black", **kw):
    if doit:
        if len(args) == 0:
            sys.stderr.write("\n")
        else:
            out = io.StringIO()
            print(*args, **kw, file=out)
            s = out.getvalue()

            termcolor.cprint(s, color, end="")
        sys.stderr.flush()


def debug(*args, color="grey", **kw):
    _debug(config.debug, *args, color=color, **kw)

def comdebug(*args, color="light_grey", **kw):
    _debug(config.comdebug, *args, color=color, **kw)
