import io, serial, types

from .. import debug, comdebug
from ..station import Station, StationException
from . import responses

class StationError(StationException):
    """
    The station replied “<X>“ to a command.
    """

class StationTimeout(StationException):
    """
    Waiting for a response line from the station has timed out.
    """

class ReadFailed(StationException):
    """
    Failed to read a value from the decoder.
    """

class DCCEX_Station(Station):
    def __init__(self, port_url, boudrate=115200, default_line_timeout=1):
        self._ready = False
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

        debug(f"Command station ready on {port_url}.", color="green")
        self._ready = True

    @property
    def ready(self):
        return self._ready

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
        if response.address == -1:
            raise ReadFailed("Failed to read cab address from decoder.")
        return response.address

    def writecab(self, cab:int) -> int|None:
        """
        Write the cab (DCC address) of the loco currently on the
        programming track using “<W>”. Returns the address as an
        integer or None on error.
        """
        assert cab > 1, "Cab address must be > 1."

        response = self.communicate("<W %i>" % cab, responses.WriteAddress)

        if response.address == -1 or response.address != cab:
            raise ReadFailed(f"Failed to write cab address from decoder "
                             f"({response.address}).")
        return response.address


    def readcv(self, cv:int) -> int|None:
        """
        Read a Configuration Variable from the locomotive
        currently on the programming track.
        """
        response = self.communicate("<R %i>" % cv, responses.ReadCV)
        if response.value == -1:
            raise ReadFailed("Failed to read CV #%i value from decoder." % cv)
        return response.value

    def writecv(self, cv:int, value:int) -> responses.Response:
        response = self.communicate("<W %i %i>" % ( cv, value, ),
                                    responses.WriteCV)
        if response.value == -1:
            raise ReadFailed("Failed to write CV #%i value %i to decoder." % (
                cv, value,))
        return response

if __name__ == "__main__":
    import sys, argparse, time, threading, signal, re

    from .. import config, debug, comdebug

    config.update({"debug": True, "comdebug": True})

    class ReaderThread(threading.Thread):
        def __init__(self):
            super().__init__()
            self.user_has_canceled = False

        def run(self):
            self.last_response = self.last_cmd_response = 0

            while not self.user_has_canceled:
                line = config.station.port.readline().rstrip()
                self.last_response += 1

                if line == "": # Timeout
                    time.sleep(.02)
                else:
                    self.last_response = self.last_response
                    if line == "<X>":
                        color = "red"
                        self.last_cmd_response = self.last_response
                    elif line.startswith("<*"):
                        color = "light_grey"
                    else:
                        color = "green"
                        self.last_cmd_response = self.last_response

                    comdebug(line, color=color)

        def cancel(self):
            self.user_has_canceled = True

    cmd_re = re.compile(r"sleep (?P<sleep>[0-9]+|[0-9]*\.[0-9]+)")

    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument("infiles", type=argparse.FileType("r"),
                            nargs="*")
        args = parser.parse_args()

        config.station.line_timeout = .03

        reader_thread = ReaderThread()
        reader_thread.start()

        def terminate():
            config.station.print("<!>") # Emergency stop.
            config.station.print("<0>") # Cut power to all tracks.

            reader_thread.cancel()
            reader_thread.join()
            sys.exit(0)

        def SIGINT_handler(sig, frame):
            terminate()
        signal.signal(signal.SIGINT, SIGINT_handler)

        # Wait for the station’s chatter before work.
        while not config.station.ready:
            time.sleep(.1)

        def process_line(line):
            if line.strip() == "":
                print()

            parts = line.split("#", 1)
            line = parts[0].strip()
            if len(parts) > 1:
                cmt = parts[1].strip()
                comdebug("# " + cmt, color="blue")

            if line != "":
                match = cmd_re.match(line)
                if match is None:
                    # A line to be sent to the command station.
                    cmd = f"<{line}>"
                    comdebug(cmd, color="black")

                    last_cmd_response = reader_thread.last_cmd_response
                    config.station.print(cmd)

                    counter = 0
                    while last_cmd_response == reader_thread.last_cmd_response:
                        time.sleep(.1)
                        counter += 1
                        if counter > 20:
                            break
                else:
                    # A meta command.
                    groups = match.groupdict()
                    if "sleep" in groups:
                        t = float(groups["sleep"])
                        time.sleep(t)


        for infile in args.infiles:
            for line in infile.readlines():
                process_line(line)

        while True:
            print("=>", end=" ")
            try:
                line = input()
            except EOFError:
                print()
                terminate()

            process_line(line)

    main()
