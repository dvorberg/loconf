import io, serial, time, types

from .. import debug, comdebug
from ..station import Station
from . import responses

class StationException(Exception):
    def __init__(self, command=None):
        self.command = command

class StationError(StationException):
    """
    The station replied “<X>“ to a command.
    """

class StationTimeout(StationException):
    """
    Waiting for a response line from the station has timed out.
    """

class DCCEX_Station(Station):
    def __init__(self, port_url, boudrate=115200, default_line_timeout=8):
        debug(f"Connecting to station on {port_url}…", end=" ")
        self.serial_port = serial.serial_for_url(port_url, boudrate)
        self.port = io.TextIOWrapper(io.BufferedRWPair(self.serial_port,
                                                       self.serial_port))

        self.default_line_timeout = default_line_timeout
        self.line_timeout = default_line_timeout

        # Read the station’s state info and copyright.
        try:
            self.communicate(None, [], line_timeout=1)
        except StationTimeout:
            pass

        debug("success.", color="green")

    @property
    def line_timeout(self):
        return self.serial_port.timeout

    @line_timeout.setter
    def line_timeout(self, line_timeout):
        if line_timeout is None:
            self.serial_port.timeout = self.default_line_timeout
        else:
            self.serial_port.timeout = line_timeout

    def print(self, *args, **kw):
        """
        Like print() but communicate the output to the command station.
        """
        print(*args, **kw, file=self.port)
        self.port.flush()

    def communicate(self, command:str,
                    wanted_responses:tuple[type(responses.Response)],
                    line_timeout=None):
        """
        Print “command” to the Command Station and read lines until
        the first of the “expected_responses” is found. Return it.
        Ignore all other lines.

        • Will raise StationError if the station replies “<X>” unless
          responses.Error is a “wanted_response”.
        • Will raise StationTimeout when waiting for the next line.
        """
        if type(wanted_responses) is type(type):
            wanted_responses = ( wanted_responses, )
        else:
            wanted_responses = tuple(wanted_responses)

        self.line_timeout = line_timeout

        if command:
            comdebug(command)
            self.print(command)

        while True:
            line = self.port.readline().rstrip()

            if line == "": # Timeout
                raise StationTimeout(command)

            response = responses.Response.from_line(line)
            if isinstance(response, wanted_responses):
                comdebug(line, color="green")
                return response
            elif isinstance(response, responses.Error):
                comdebug(line, color="cyan")
                raise StationError(command)
            else:
                comdebug(line)

    def readcab(self) -> int|None:
        """
        Read the cab (DCC address) of the loco currently on the
        programming track using “<R>”. Returns the address as an
        integer or None on error.
        """
        response = self.communicate("<R>", responses.ReadAddress)
        return response.address


    def readcv(self, cv:int) -> int|None:
        """
        Read a Configuration Variable from the locomotive
        currently on the programming track.
        """
        response = self.communicate("<R %i>" % cv, responses.ReadCV)
        return response.value
