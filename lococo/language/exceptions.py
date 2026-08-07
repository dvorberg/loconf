import dataclasses, io, pathlib
import ply.lex

@dataclasses.dataclass
class Location:
    lineno: int
    looking_at: str
    filepath: pathlib.Path = None

    @classmethod
    def from_lexdatapos(Location, lexdata, lexpos, filepath=None):
        lineno = lexdata[:lexpos].count("\n") + 1
        remainder = lexdata[lexpos:]
        return Location( lineno, remainder[:40], filepath )


    @classmethod
    def from_lextoken(Location, lextoken:ply.lex.LexToken, filepath=None):
        return Location.from_lexdatapos(lextoken.lexer.lexdata,
                                        lextoken.lexpos,
                                        filepath)

    @classmethod
    def from_baselexer(Location, lexer, filepath=None):
        return Location.from_lexdatapos(lexer.lexdata, lexer.lexpos, filepath)

class LoconfError(Exception):
    """
	General-purpose exception raised when errors occur during lexing and
    parsing.

	'message' is brief error message (no HTML)
	'looking_at' is text near/after error location
	'trace' is exception trace (raw text) , or '' if no exception occurred.
	'location' is buffer after point of error.
	"""
    def __init__(self, message:str, location:Location=None, trace=None):
        Exception.__init__(self, message)

        self.message = message
        self.trace = trace
        self.location = location

    @property
    def lineno(self):
        if self.location:
            return self.location.lineno
        else:
            return None

    @property
    def looking_at(self):
        if self.location:
            return self.location.looking_at
        else:
            return None

    def __str__(self):
        ret = io.StringIO()

        def say(*args):
            print(*args, end=" ", file=ret)

        say(f"{self.message}")
        if self.location:
            if self.location.filepath is not None:
                fname = self.location.filepath.name
                if " " in fname: fname = repr(fname)
                fname = "In " + fname
            else:
                fname = "Line"

            say(f"{fname}:{self.lineno}")
            say(f"Looking at: {repr(self.looking_at)}")

        if self.trace:
            say(f"Traceback: {self.trace}")

        return ret.getvalue()

class LexerSetupError(LoconfError):
    pass

class SyntaxError(LoconfError):
    pass

class ParseError(LoconfError):
    pass
