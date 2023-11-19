import logging
import asyncio
import time
from functools import wraps
from threading import RLock

import serial

from .config import (
    DEVICE_CONFIG,
    PROTOCOL_CONFIG,
    get_with_log,
)
from .protocol import (
    CONF_COMMAND_EOL,
    CONF_COMMAND_SEPARATOR,
    CONF_RESPONSE_EOL,
    async_get_rs232_protocol,
)

LOG = logging.getLogger(__name__)

SUPPORTED_EQUIPMENT = DEVICE_CONFIG.keys()

CONF_SERIAL_CONFIG = "rs232"

def get_device_config(equipment_type, key, log_missing=True):
    return get_with_log(equipment_type, DEVICE_CONFIG[equipment_type], key, log_missing=log_missing)


def get_protocol_config(equipment_type, key):
    protocol = get_device_config(equipment_type, "protocol")
    return PROTOCOL_CONFIG[protocol].get(key)



class EquipmentControl:
    """
    Creates an eequipment controller object. If an event_loop argument is passed in
    this will return the asynchronous implementation. By default this returns the
    synchronous interface.

    :param equipment_type: identifier for type of equipment (e.g. mcintosh)
    :param url: pyserial supported url for communication (e.g. '/dev/ttyUSB0' or 'socket://remote-host:7000/')
    :param config_overrides: dictionary of serial port configuration overrides (e.g. baudrate)

    :param event_loop: to get an interface that can be used asynchronously, pass in an event loop

    :return an instance of EquipmentControlBase
    """
    @classmethod
    def get_equipment_controller(self, equipment_type: str, url: str, serial_config_overrides={}, event_loop=None) -> EquipmentController:
        if equipment_type not in SUPPORTED_EQUIPMENT:
            LOG.error("Unsupported equipment type '%s'", equipment_type)
            return None

        if event_loop:
            return EquipmentControllerSync(equipment_type, url, serial_config_overrides)
        else:            
            return EquipmentControllerAsync(equipment_type, url, serial_config_overrides)


class EquipmentController:
    """
    EquipmentControl interface
    """

    def interface(self):
        """
        Return details on the interface (JSON)
        """
        # FIXME: convert for this equipment the protocol
        # definition into a lightweight return of details 
        # (e.g. lots of stuff should be filtered out that 
        # is unnecessary). This does not need to be async/sync
        # specific so can be implemented here.
        return []

    def set_power(self, zone: int, power: bool):
        """
        Turn zone on or off
        :param zone: zone 11..16, 21..26, 31..36
        :param power: True to turn on, False to turn off
        """
        raise NotImplementedError()

def _command(equipment_type: str, format_code: str, args={}):
    cmd_eol = get_protocol_config(equipment_type, CONF_COMMAND_EOL)
    cmd_separator = get_protocol_config(equipment_type, CONF_COMMAND_SEPARATOR)

    rs232_commands = get_protocol_config(equipment_type, "commands")
    command = rs232_commands.get(format_code) + cmd_separator + cmd_eol

    return command.format(**args).encode("ascii")



def get_equipment_controller(equipment_type: str, url, config_overrides={}):
    """
    Return synchronous version of amplifier control interface
    :param equipment_type identifier for type of equipment (e.g. mcintosh)
    :param url: pyserial supported url for communication (e.g. '/dev/ttyUSB0' or 'socket://remote-host:7000/')
    :param config_overrides: dictionary of serial port configuration overrides (e.g. baudrate)
    :return: synchronous implementation of equipment control interface
    """

    # sanity check the provided equipment type
    if equipment_type not in SUPPORTED_EQUIPMENT:
        LOG.error("Unsupported equipment type '%s'", equipment_type)
        return None

    lock = RLock()

    def synchronized(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                return func(*args, **kwargs)
        return wrapper

    class EquipmentControllerSync(EquipmentController):
        def __init__(self, equipment_type, url, serial_config_overrides):
            self._equipment_type = equipment_type

            # allow overriding the default serial port configuration, in case the user has changed
            # settings on their amplifier (e.g. increased the default baudrate)
            serial_config = get_device_config(equipment_type, CONF_SERIAL_CONFIG)
            if serial_config_overrides:
                LOG.debug(
                    f"Overiding config for {url}: {serial_config_overrides}"
                )
                serial_config.update(serial_config_overrides)

            self._port = serial.serial_for_url(url, **serial_config)

        def _send_request(self, request: bytes, skip=0):
            """
            :param request: request that is sent to the mcintosh
            :param skip: number of bytes to skip for end of transmission decoding
            :return: ascii string returned by mcintosh
            """
            # clear
            self._port.reset_output_buffer()
            self._port.reset_input_buffer()

            # print(f"Sending:  {request}")
            LOG.debug(f"Sending:  {request}")

            # send
            self._port.write(request)
            self._port.flush()

            response_eol = get_protocol_config(amp_type, CONF_RESPONSE_EOL)
            len_eol = len(response_eol)

            # receive
            result = bytearray()
            while True:
                c = self._port.read(1)
                # print(c)
                if not c:
                    ret = bytes(result)
                    LOG.info(result)
                    raise serial.SerialTimeoutException(
                        "Connection timed out! Last received bytes {}".format(
                            [hex(a) for a in result]
                        )
                    )
                result += c
                if len(result) > skip and result[-len_eol:] == response_eol.encode(
                    "ascii"
                ):
                    break

            ret = bytes(result)
            LOG.debug('Received "%s"', ret)
            #            print(f"Received: {ret}")
            return ret.decode("ascii")


        @synchronized
        def set_volume(self, zone: int, volume: int):
            self._send_request(_set_volume_cmd(self._amp_type, zone, volume))

    return EquipmentControlSync(equipment_type, address, config_overrides)


async def async_get_amp_controller(
    loop, equipment_type: str, url: str, serial_config_overrides={})
    """
    Return asynchronous version of equipment control interface
    :param loop reference to the event loop
    :param equipment identifier for what equipment (e.g. mcintosh)
    :param url: url for the communication mechanism (e.g. '/dev/ttyUSB0' or 'socket://remote-host:7000/')
    :param serial_config_overrides: dictionary of serial port configuration overrides (e.g. baudrate)
    :return: synchronous implementation of equipment control interface
    """

    # sanity check the provided amplifier type
    if equipment_type not in SUPPORTED_EQUIPMENT:
        LOG.error("Unsupported amplifier type '%s'", equipment_type)
        return None

    lock = asyncio.Lock()

    def locked_coro(coro):
        @wraps(coro)
        async def wrapper(*args, **kwargs):
            async with lock:
                return await coro(*args, **kwargs)
        return wrapper

    class EquipmentControllerAsync(EquipmentController):
        def __init__(self, equipment_type, serial_config_overrides, protocol):
            self._equipment_type = equipment_type
            self._serial_config = serial_config
            self._protocol = protocol

        @locked_coro
        async def zone_status(self, zone: int):
            # FIXME: this has nothing to do with amp_type?  protocol!

            # if there is a list of zone status commands, execute that (some don't have a single command for status)
            # if get_protocol_config(amp_type, 'zone_status_commands'):
            #    return await self._zone_status_manual(zone)

            cmd = _zone_status_cmd(self._amp_type, zone)
            skip = get_device_config(amp_type, "zone_status_skip") or 0
            status_string = await self._protocol.send(cmd, skip=skip)

            status = ZoneStatus.from_string(self._amp_type, status_string)
            LOG.debug("Status: %s (string: %s)", status, status_string)
            if status:
                return status.dict
            return None


    protocol = get_device_config(equipment_type, "protocol")
    protocol_config = PROTOCOL_CONFIG[protocol]

    # allow overriding the default serial port configuration, in case the user has changed
    # settings on their amplifier (e.g. increased the default baudrate)
    serial_config = get_device_config(equipment_type, CONF_SERIAL_CONFIG)
    if serial_config_overrides:
        LOG.debug(
            f"Overiding serial port config for {url}: {serial_config_overrides}"
        )
        serial_config.update(serial_config_overrides)

    LOG.debug(f"Loading {equipment_type}/{protocol}: {serial_config}, {protocol_config}")
    
    # FIXME: this is async why??? can it be a factory?
    protocol = await async_get_rs232_protocol(
        url, DEVICE_CONFIG[equipment_type], serial_config, protocol_config, loop
    )
    return EquipmentControllerAsync(equipment_type, serial_config, protocol)
