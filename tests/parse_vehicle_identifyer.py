import argparse
from loconf.utils import VehicleIdentifyer

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vehicle", type=VehicleIdentifyer.parse)
    args = parser.parse_args()

    ic(args.vehicle)


main()
