import serial, sys, traceback, time, re, dataclasses, typing

from serial.threaded import ReaderThread, LineReader
from termcolor import colored

from .. import config
from . import responses

@dataclasses.dataclass
class Callback(object):
    response_type: responses.Response
    callback: callable

    def match(self, response):
        if isinstance(response, self.response_type):
            self.callback(response)
            return True
        else:
            return False

class SerialInterface(LineReader):
    TERMINATOR=b"\n"
    ENCODING="ascii"

    def connection_made(self, transport):
        super().connection_made(transport)
        self.lines_received = 0
        self.callbacks = []

    def handle_line(self, line):
        self.lines_received += 1
        for Response in responses.response_classes:
            match = Response.regex.match(line.rstrip())
            if match is not None:
                response = Response(match.groupdict())
                self.handle_response(response)

        if config.comdebug:
            self.print_debug(line, None)

    def print_debug(self, line, response):
        if response is None:
            print(colored(line, "red"))
        elif isinstance(response, responses.Comment):
            print(colored(line, "grey"))
        else:
            print(colored(line, "green"))
            print(repr(response))

    def handle_response(self, response):
        for index, callback in enumerate(self.callbacks):
            if callback.match(response):
                if config.comdebug:
                    print(colored(callback.callback, "green"))
                del self.callbacks[index]
                return

    def connection_lost(self, exc):
        if exc is not None:
            raise exc
        #if exc:
        #    traceback.print_exc(exc)
        #sys.stdout.write("port closed\n")

    def wait_for_line(self, timeout=1):
        here = self.lines_received
        start_time = time.time()

        while here == self.lines_received:
            time.sleep(.05)
            if time.time() > start_time+timeout:
                return

    def wait_for_lines(self, start_timeout=1, more_timeout=.2):
        self.wait_for_line(start_timeout)

        while True:
            here = self.lines_received
            time.sleep(more_timeout)
            if self.lines_received == here:
                return

    def communicate(self, line, callback:Callback):
        self.callbacks.append(callback)
        ic(line)
        self.write_line(line)
