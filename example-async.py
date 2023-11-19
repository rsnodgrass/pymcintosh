#! /usr/local/bin/python3
#
# Running:
#   ./example-async.py --help
#   ./example-async.py --tty /dev/tty.usbserial-A501SGSZ
#   ./example-async.py --tty socket:/remote-server:4999/

import logging
import argparse as arg
import asyncio

import coloredlogs

from pymcintosh import create_equipment_controller

LOG = logging.getLogger(__name__)
coloredlogs.install(level="DEBUG")

p = arg.ArgumentParser(description="RS232 client example (asynchronous)")
p.add_argument(
    "--url",
    help="pyserial supported url for communication (e.g. /dev/tty.usbserial-A501SGSZ or socket://server:4999/)",
    required=True,
)
p.add_argument("--type", default="mcintosh", help="equipment type (e.g. mcintosh)")
p.add_argument(
    "--baud",
    type=int,
    default=115200,
    help="baud rate if local tty used (default=115200)",
)
args = p.parse_args()

config = {"baudrate": args.baud}


async def main():
    equipment = create_equipment_controller(
        args.type,
        args.url,
        serial_config_overrides=config,
        event_loop=asyncio.get_event_loop(),
    )

    print(equipment.commands())

    await equipment.power.off()

    # exit()


asyncio.run(main())
