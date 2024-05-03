import serial, time

def main():
    port = serial.Serial("/dev/cu.usbmodem14101", 115200)

    # On opening the port, the Command Station will provide
    # copyright and version information. We need to read all that.
    port.timeout = 1
    info = port.read(1024)
    print(info.decode("utf-8"))

    port.write(b"<R 1 0 0>") # Request the current Track Manager configuration
    print(port.readline().decode("utf-8").rstrip())
    print(port.readline().decode("utf-8").rstrip())
    print(port.readline().decode("utf-8").rstrip())

main()
