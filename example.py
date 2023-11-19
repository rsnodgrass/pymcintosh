#!/usr/local/bin/python3
#
# Running:
#   ./example-async.py --help
#   ./example.py --tty /dev/tty.usbserial-A501SGSZ

import logging
import coloredlogs
import argparse as arg
from pymcintosh import create_equipment_api
from pymcintosh.const import BAUD_RATES

LOG = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG')

p = arg.ArgumentParser(description="RS232 client example (synchronous)")
p.add_argument(
    "--address", help="address of communication interface (e.g. /dev/tty.usbserial-A501SGSZ or socket://server:4999/)", required=True
)
p.add_argument(
    "--equipment", default="mcintosh", help="equipment type (e.g. mcintosh)"
)
p.add_argument(
    "--baud",
    type=int, default=115200, help=f"baud rate if local tty used ({BAUD_RATES})",
)
args = p.parse_args()

config = {
    "baudrate": args.baud
}

def main():
  zone = 1
  
  equipment = create_equipment_controller(
        args.equipment,
        args.url,
        serial_config_overrides=config)

  # save the status for all zones before modifying
  zone_status = {}
  for zone in range(1, 9):
      zone_status[zone] = equipment.zone_status(zone)  # save current status for all zones
      print(f"Zone {zone} status: {zone_status[zone]}")

  equipment.all_off()
  exit

main()