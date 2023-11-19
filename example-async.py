#! /usr/local/bin/python3
#
# Running:
#   ./example-async.py --help
#   ./example-async.py --tty /dev/tty.usbserial-A501SGSZ
#   ./example-async.py --tty socket:/remote-server:4999/

import logging
import argparse as arg
import asyncio
import sys

from pymcintosh import async_get_amp_controller

####----------------------------------------
LOG = logging.getLogger()
LOG.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
LOG.addHandler(handler)
####----------------------------------------

p = arg.ArgumentParser(description="RS232 client example (asynchronous)")
p.add_argument(
    "--address", help="address of communication mechanism to use (e.g. /dev/tty.usbserial-A501SGSZ or socket://server:4999/)", required=True
)
p.add_argument(
    "--equipment", default="mcintosh", help="model (e.g. mcintosh)"
)
p.add_argument( # FIXME: this is not required for IP based right?
    "--baud",
    type=int,
    default=115200,
    help="baud rate (9600, 14400, 19200, 38400, 57600, 115200)",
)
args = p.parse_args()

config = {
    "baudrate": args.baud
}

async def main():
    equipment = await async_get_equipment_controller(
        args.equipment,
        args.address,
        asyncio.get_event_loop(),
        config_overrides=config,
    )
    
    print equipment.commands()
    
    
    await equipment.power.off()
    
    
    
    
    #    print(f"Xantech amp version = {await amp.sendCommand('version')}")

    for zone in range(1, 8):

        await asyncio.sleep(0.5)
        await amp.set_power(zone, True)

        await asyncio.sleep(0.5)
        await amp.set_source(zone, 1)
        await amp.set_mute(zone, False)

        status = await amp.zone_status(zone)
        print(f"Zone {zone} status: {status}")

    exit()


asyncio.run(main())
