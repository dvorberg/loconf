import serial, sys, traceback, time, re, dataclasses, typing

from serial.threaded import ReaderThread, LineReader
from termcolor import colored

import icecream; icecream.install()

from loconf import responses

debug=True


class CommandStation(LineReader):
    TERMINATOR=b"\n"
    ENCODING="ascii"

    def connection_made(self, transport):
        super(PrintLines, self).connection_made(transport)
        self.lines_received = 0
        self.response_we_are_waiting_for = None

    def handle_line(self, line):
        self.lines_received += 1
        for Response in responses.response_classes:
            match = Response.regex.match(line.rstrip())
            if match is not None:
                response = Response(match.groupdict())
                if debug: self.print_debug(line, response)
                self.handle_response(response)
                if Response is self.response_we_are_waiting_for:
                    self.response_we_are_waiting_for = None

                return

        if debug:
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
        pass

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

    def wait_for(self, response_class, timeout=1):
        self.response_we_are_waiting_for = response_class

        start_time = time.time()
        while True:
            if self.response_we_are_waiting_for is None \
               or time.time() > start_time + timeout:
                return

            time.sleep(.2)

    def communicate(self, line, response_class, timeout=1):
        self.write_line(line)
        self.wait_for(response_class, timeout)

def main():
    port = serial.serial_for_url("/dev/cu.usbmodem14701",
                                 baudrate=115200, timeout=1)

    with ReaderThread(port, PrintLines) as reader_thread:
        reader_thread.wait_for_lines(2)

        reader_thread.communicate("<R 5>", responses.ReadCV, 5)

        #while True:
        #    line = input("DCC-EX# ").rstrip()
        #    if line:
        #        reader_thread.write_line(line.strip())
        #        reader_thread.wait_for_lines(start_timeout=5)

main()
