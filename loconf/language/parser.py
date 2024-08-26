import copy, dataclasses, pathlib, itertools
import ply.lex

from . import lextokens
from .exceptions import Location, SyntaxError, ParseError

class LexerWrapper(object):
    """
    Prettify some of ply.lex.lex()’s functionality.
    """
    def __init__(self, lexer:ply.lex.Lexer, infile):
        self.base = copy.copy(lexer)
        self.infile = infile
        self._current_token = None

    def tokenize(self):
        source = self.infile.read()
        self.base.input(source.lstrip())

        while True:
            try:
                token = self.base.token()
            except ply.lex.LexError as e:
                raise SyntaxError(
                    str(e), location=Location.from_baselexer(
                        self.base, self.infilepath))

            if not token:
                break
            else:
                self._current_token = token
                token.get_location = self.get_location
                yield token

    @property
    def infilepath(self):
        if hasattr(self.infile, "name"):
            return pathlib.Path(self.infile.name)
        else:
            return None

    def get_location(self):
        if (self._current_token is not None
            and hasattr(self._current_token, "lexer")):
            return Location.from_lextoken(self._current_token, self.infilepath)
        else:
            return Location.from_baselexer(self.base, self.infilepath)

    @property
    def remainder(self) -> str:
        return get_remainder(self.base)

    @property
    def lexpos(self) -> int:
        return self.base.lexpos

    @lexpos.setter
    def lexpos(self, lexpos:int):
        self.base.lexpos = lexpos

    @remainder.setter
    def remainder(self, remainder:str):
        set_remainder(self.base, remainder)

    @property
    def lexmatch(self):
        return self.base.lexmatch


@dataclasses.dataclass
class Setting:
    value: int
    location: Location

class Parser(object):
    def __init__(self, include_paths=[]):
        self.include_paths = include_paths
        self.variables = {}

    def parse(self, infile):
        include_paths = copy.copy(self.include_paths)
        include_paths.append(pathlib.Path(".").absolute())

        filepath = getattr(infile, "name", None)
        if filepath is not None:
            include_paths.insert(0, pathlib.Path(filepath).absolute().parent)

        cvs = {} # Maps number:int to Setting

        infilepaths = set()
        def tokens_from(infile):
            infilepath = getattr(infile, "name", None)
            if infilepath is None:
                infilepath = "<no filename>"
            else:
                infilepath = pathlib.Path(infilepath).absolute()

            if infilepath in infilepaths:
                raise ParseError("Multiple inclusions of {infilepath}.")
            else:
                infilepaths.add(infilepath)

            lexer = LexerWrapper(ply.lex.lex(module=lextokens,
                                             reflags=0,
                                             optimize=False,
                                             lextab=None), infile)

            return lexer.tokenize()

        tokens = tokens_from(infile)


        def expect(*types):
            token = next(tokens)
            if token.type not in types:
                if len(types) == 1:
                    type = types[0]
                else:
                    types = ",".join(types)
                    type = f"one of {types}"
                raise ParseError(f"Expected {type}, found {token.type}.",
                                 location=token.get_location())
            return token

        def expect_number():
            return parse_number(next(tokens))

        def parse_number(token):
            # A number could either be:
            # - a number literal (int value already present)
            # - an identifyer (that needs to be dereferenced)
            # - an expression (enclosed in () that needs to be processed)
            match token.type:
                case "number_literal":
                    return token.value
                case "identifyer":
                    identifyer = token.value
                    if identifyer not in self.variables:
                        raise ParseError(f"Unknown identifyer: “{identifyer}”.",
                                         token.get_location())
                    else:
                        return self.variables[identifyer]
                case "open_paren":
                    return parse_sum()
                case "open_bracket":
                    return parse_bits()
                case _:
                    raise ParseError(f"Expected number, identifyer or "
                                     f"expression, found {token.type}.")


        def parse_sum():
            # The open paren has been consumed.
            ret = 0
            while True:
                n = expect_number()
                if n not in { 0, 1, 2, 4, 8, 16, 32, 64, 128, }:
                    raise SyntaxError("Components in a sum must be powers "
                                      "of two.")
                ret += n
                token = expect("plus", "close_paren")
                if token.type == "close_paren":
                    break

            return ret

        def parse_bits():
            # The open bracket has been consumed.
            ret = 0
            while True:
                n = expect_number()
                if n < 0 or n > 7:
                    raise SyntaxError("Bit number must be 0 <= n <= 7.")
                ret += 2 ** n
                token = expect("comma", "close_bracket")
                if token.type == "close_bracket":
                    break

            return ret

        while True:
            try:
                token = next(tokens)
            except StopIteration:
                break

            match token.type:
                # case "line_comment" | "inline_comment" | "whitespace":
                # These are handled by returning None in lextokens functions.

                case "name_keyword":
                    number = expect_number()
                    identifyer = expect("identifyer").value

                    if identifyer in self.variables:
                        raise ParseError(
                            f"Identifyer already defined: {identifyer}")
                    else:
                        self.variables[identifyer] = number

                case "include_keyword":
                    path = pathlib.Path(expect("string_literal").value)

                    if path.is_absolute():
                        inpath = path
                    else: # Check for path relative to the current input file.
                        location = token.get_location()
                        inpath = pathlib.Path(location.filepath.parent, path)
                        if not inpath.exists():
                            # Try to find the file to be included along the
                            # input path.
                            for ip in include_paths:
                                inpath = pathlib.Path(ip, path)
                                if inpath.exists:
                                    break

                    tokens = itertools.chain(tokens_from(inpath.open()), tokens)

                case "identifyer" | "number_literal":
                    cv = parse_number(token)
                    expect("walrus")
                    value = expect_number()

                    if cv in cvs:
                        setting = cvs[cv]
                        raise ParseError(f"CV {cv} already set to "
                                         f"{setting.value} at "
                                         f"{setting.location}")
                    else:
                        cvs[cv] = Setting(value, token.get_location())

                case _:
                    ic(token)

        return dict([(cv, setting.value) for cv, setting in cvs.items()])

def parse_file(fp):
    parser = Parser()
    return parser.parse(fp)

if __name__ == "__main__":
    import pathlib, argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("infilepath", type=pathlib.Path)
    args = ap.parse_args()

    cvs = parse_file(ap.infilepath.open())
    ic(cvs)
