#!/usr/local/bin/python3
#
# Running:
#   ./example-async.py --help
#   ./example.py --tty /dev/tty.usbserial-A501SGSZ

import logging
import argparse as arg

import coloredlogs

from pymcintosh import create_device_controller

LOG = logging.getLogger(__name__)
coloredlogs.install(level="DEBUG")

p = arg.ArgumentParser(description="RS232 client example (synchronous)")
p.add_argument(
    "--url",
    help="pyserial supported url for communication (e.g. /dev/tty.usbserial-A501SGSZ or socket://server:4999/)",
    required=True,
)
p.add_argument("--type", default="mcintosh", help="device type (e.g. mcintosh)")
p.add_argument(
    "--baud",
    type=int,
    default=115200,
    help="baud rate if local tty used (default=115200)",
)
args = p.parse_args()

config = {"baudrate": args.baud}


def main():
    device = create_device_controller(
        args.type, args.url, serial_config_overrides=config
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
