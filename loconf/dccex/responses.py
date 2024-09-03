import re, typing, types

class Response(object):
    def __init__(self, groupdict):
        annotations = typing.get_type_hints(self.__class__)
        for name, value in groupdict.items():
            target_type = annotations[name]

            if isinstance(target_type, types.UnionType):
                for t in typing.get_args(target_type):
                    if t is type(None):
                        value = None
                        break

                    try:
                        value = t(value)
                    except (ValueError, TypeError):
                        pass
                    else:
                        break
            else:
                value = target_type(value)

            setattr(self, name, value)

    def __repr__(self):
        info = [ "%s=%s" % ( name, repr(getattr(self, name),) )
                 for name in typing.get_type_hints(self.__class__).keys() ]
        return f"<{self.__class__.__name__} {' '.join(info)}>"

    @classmethod
    def from_line(cls, line:str):
        for Response in response_classes:
            match = Response.regex.match(line.rstrip())
            if match is not None:
                return Response(match.groupdict())

        raise ValueError("Don’t know how to handle station "
                         "response " + repr(line))

class Comment(Response):
    regex = re.compile(r"<\* (?P<comment>.*?) \*>")
    comment: str

class Error(Response):
    """
    <X>: Whenever the DCC-EX is unhappy with what I say, it
    passiv-agressively says “<X>“. Whatever.
    """
    regex = re.compile(r"<X>")

class TrackManagement(Response):
    """
    <= trackletter state cab>

    • trackletter: A-H
    • state: PROG, MAIN DC, DCX
    • cab: cab(loco) equivalent to a fake DCC Address
    """
    regex = re.compile(r"<= "
                       r"(?P<trackletter>[A-H]) "
                       r"(?P<state>PROG|MAIN|DC|DCX)"
                       r"( (?P<cab>\d+))?")
    trackletter: str
    state: str
    cab: int|None

class TrackPower(Response):
    """
    <p0|1 track_letter>
    """
    regex = re.compile(r"<p(?P<state>0|1)( (?P<trackletter>[A-H]))?>")
    state: int
    trackletter: str

    @property
    def on(self):
        return bool(self.state)

class At(Response):
    """
    I don’t know what these to.
    """
    regex = re.compile(r'<@ .*?(\"[^"]+\")?>')

class Version(Response):
    regex = re.compile(r"<iDCC-EX.*?>")

class ReadCV(Response):
    """
    <P cv>: Request value of “CV”.
    """
    regex = re.compile(r"<v (?P<cv>\d+) (?P<value>-?\d+)>")
    cv: int
    value: int

class WriteCV(Response):
    regex = re.compile(r"<r (?P<cv>\d+) (?P<value>-?\d+)>")
    cv: int
    value: int

class ReadAddress(Response):
    """
    <r>: Request the address of the engine on the programming track.
    """
    regex = re.compile(r"<r (?P<address>-?\d+)>")
    address: int

class WriteAddress(Response):
    """
    <w>: Request the address of the engine on the programming track.
    """
    regex = re.compile(r"<w (?P<address>-?\d+)>")
    address: int

class ReadCVplus(Response):
    """
    <R cv callbacknum callbacksum>: Request value of “CV” echoing arbitrary
    “callbacknum” and “callbacksum” integers back to the caller.
    """
    regex = re.compile(r"<r "
                       r"(?P<callbacknum>\d+)\|"
                       r"(?P<callbacksub>\d+)\|"
                       r"(?P<cv>\d+) "
                       r"(?P<value>-?\d+)>")
    cv: int
    value: int
    callbacknum: int
    callbacksum: int


response_classes = [ cls
                     for cls in globals().values()
                     if isinstance(cls, type) \
                         and issubclass(cls, Response) \
                         and cls is not Response ]
