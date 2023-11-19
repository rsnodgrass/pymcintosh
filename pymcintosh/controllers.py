import logging

import serial

from .asynchronous import async_get_rs232_protocol, locked_coro
from .config import DEVICE_CONFIG, PROTOCOL_CONFIG, get_with_log
from .const import *  # noqa: F403
from .sync import synchronized

LOG = logging.getLogger(__name__)


def get_device_config(equipment_type, key, log_missing=True):
    return get_with_log(
        equipment_type, DEVICE_CONFIG[equipment_type], key, log_missing=log_missing
    )


class EquipmentControllerBase:
    """
    EquipmentControllerBase base class that defines operations allowed
    to control equipment.
    """

    def __init__(self, equipment_type, url, serial_config, protocol_name):
        self._equipment_type = equipment_type
        self._url = url
        self._serial_config = serial_config
        self._protocol_name = protocol_name
        self._protocol_config = PROTOCOL_CONFIG[protocol_name]

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

    def _command(self, equipment_type: str, format_code: str, args={}):
        cmd_eol = self._protocol_config.get(CONF_COMMAND_EOL)
        cmd_separator = self._protocol_config.get(CONF_COMMAND_SEPARATOR)

        rs232_commands = self._protocol_config.get("commands")
        command = rs232_commands.get(format_code) + cmd_separator + cmd_eol

        return command.format(**args).encode("ascii")


class EquipmentControllerSync(EquipmentControllerBase):
    def __init__(self, equipment_type, url, serial_config, protocol_name):
        EquipmentControllerBase.__init__(
            equipment_type, url, serial_config, protocol_name
        )
        self._connection = serial.serial_for_url(url, **serial_config)

    def _send_request(self, request: bytes, skip=0):
        """
        :param request: request that is sent to the equipment
        :param skip: number of bytes to skip for end of transmission decoding
        :return: ascii string returned by equipment
        """
        # clear
        self._connection.reset_output_buffer()
        self._connection.reset_input_buffer()

        LOG.debug(f"Sending {self._equipment_type} @ {self._url}: {request}")

        # send
        self._connection.write(request)
        self._connection.flush()

        response_eol = self._protocol_config.get(CONF_RESPONSE_EOL)
        len_eol = len(response_eol)

        # receive
        result = bytearray()
        while True:
            c = self._connection.read(1)
            if not c:
                ret = bytes(result)
                LOG.info(result)
                raise serial.SerialTimeoutException(
                    "Connection timed out! Last received bytes {}".format(
                        [hex(a) for a in result]
                    )
                )

            result += c
            if len(result) > skip and response_eol.encode("ascii") == result[-len_eol:]:
                break

        ret = bytes(result)
        LOG.debug("Received {self._equipment_type} @ {self._url}: %s", ret)
        return ret.decode("ascii")

    @synchronized
    def set_volume(self, zone: int, volume: int):
        self._send_request(_set_volume_cmd(self._amp_type, zone, volume))


# -----------------------------------------------------------------------------
z


class EquipmentControllerAsync(EquipmentControllerBase):
    def __init__(self, loop, equipment_type, url, serial_config, protocol_name):
        EquipmentControllerBase.__init__(
            equipment_type, url, serial_config, protocol_name
        )
        self._loop = loop
        self._connection_ref = None

    """
    @return the connection to the RS232 device (lazy connect if none)
    """

    async def _connection(self):
        if not self._connection_ref:
            LOG.debug(
                f"Connecting to {self._equipment_type}/{self._protocol_name} @ {self._url}: %s %s",
                self._serial_config,
                self._protocol_config,
            )
            self._connection_ref = await async_get_rs232_protocol(
                self._url,
                DEVICE_CONFIG[self._equipment_type],
                self._serial_config,
                self._protocol_config,
                self._loop,
            )
        return self._connection_ref

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


# -----------------------------------------------------------------------------


class EquipmentController:
    """
    Create an instance of an EquipmentControllerBase object given
    details about the given equipment.

    If an event_loop argument is passed in this will return the
    asynchronous implementation. By default the synchronous interface
    is returned.

    :param equipment_type: identifier for type of equipment (e.g. mcintosh)
    :param url: pyserial supported url for communication (e.g. '/dev/ttyUSB0' or 'socket://remote-host:7000/')
    :param config_overrides: dictionary of serial port configuration overrides (e.g. baudrate)

    :param event_loop: to get an interface that can be used asynchronously, pass in an event loop

    :return an instance of EquipmentControlBase
    """

    @classmethod
    def create_equipment_controller(
        self, equipment_type: str, url: str, serial_config_overrides={}, event_loop=None
    ) -> EquipmentControllerBase:
        # ensure caller has specified a valid equipment_type
        config = DEVICE_CONFIG.get(equipment_type)
        if not config:
            LOG.error(f"Unsupported equipment type '{equipment_type}'")
            return None

        # caller can override the default serial port config for a given type
        # of equipment since the user could have changed settings on their
        # physical equipment (e.g. increasing the baudrate)
        serial_config = get_device_config(equipment_type, CONF_SERIAL_CONFIG)
        if serial_config_overrides:
            LOG.debug(f"Overriding serial config for {url}: {serial_config_overrides}")
            serial_config.update(serial_config_overrides)

        # ensure the equipment has a protocol defined
        protocol_name = get_device_config(equipment_type, CONF_PROTOCOL_NAME)
        if not protocol_name:
            LOG.error(
                f"Equipment type {equipment_type} is missing "
                + f"'{CONF_PROTOCOL_NAME}' config key"
            )
            return

        if event_loop:
            return EquipmentControllerAsync(
                event_loop, equipment_type, url, serial_config, protocol_name
            )

        return EquipmentControllerSync(
            equipment_type, url, serial_config, protocol_name
        )
