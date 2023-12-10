#!/usr/local/bin/python3
#
# Running:
#   ./example-async.py --help
#   ./example.py --tty /dev/tty.usbserial-A501SGSZ

import logging
import argparse as arg

import coloredlogs

from pymcintosh import DeviceController

LOG = logging.getLogger(__name__)
coloredlogs.install(level="DEBUG")

p = arg.ArgumentParser(description="RS232 client example (synchronous)")
p.add_argument(
    "--url",
    help="pyserial supported url for communication (e.g. /dev/tty.usbserial-A501SGSZ or socket://server:4999/)",
    required=True,
)
p.add_argument("--model", default="mx160", help="device model (e.g. mx160)")
p.add_argument(
    "--baud",
    type=int,
    default=115200,
    help="baud rate if local tty used (default=115200)",
)
p.add_argument("-d", "--debug", action="store_true", help="verbose logging")
args = p.parse_args()

if args.debug:
    logging.getLogger().setLevel(level=logging.DEBUG)

config = {"baudrate": args.baud}


def main():
    device = DeviceController.create(
        args.model, args.url, serial_config_overrides=config
    )

    # save the status for all zones before modifying
    zone_status = {}
    for zone in range(1, 9):
        zone_status[zone] = device.zone_status(
            zone
        )  # save current status for all zones
        print(f"Zone {zone} status: {zone_status[zone]}")

    device.all_off()
    exit


main()
