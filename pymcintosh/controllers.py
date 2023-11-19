import logging

import serial

from .asynchronous import async_get_rs232_protocol, locked_coro
from .const import *  # noqa: F403
from .core import load_yaml_dir
from .protocol import PROTOCOL_DEFS
from .sync import synchronized

LOG = logging.getLogger(__name__)

DEVICE_CONFIG = load_yaml_dir(f"{CONFIG_DIR}/series")


class DeviceControllerBase:
    """
    DeviceControllerBase base class that defines operations allowed
    to control a device.
    """

    def __init__(self, device_type, url, serial_config, protocol_name):
        self._device_type = device_type
        self._url = url
        self._serial_config = serial_config
        self._protocol_name = protocol_name
        self._protocol_def = PROTOCOL_DEFS[protocol_name]

    def _write(self, data: bytes, skip=0):
        """
        Write the provided data to the connected device.
        """
        raise NotImplementedError()

    def _command(self, device_type: str, format_code: str, args={}):
        cmd_eol = self._protocol_def.get(CONF_COMMAND_EOL)
        cmd_separator = self._protocol_def.get(CONF_COMMAND_SEPARATOR)

        rs232_commands = self._protocol_def.get("commands")
        command = rs232_commands.get(format_code) + cmd_separator + cmd_eol

        return command.format(**args).encode("ascii")

    def command(self, group: str, action: str, **kwargs):
        """
        Call a command by the group/action and args as defined in the
        device's protocol yaml.
        """
        LOG.error(f"Should be calling {group}.{action}({kwargs})")

    def raw_command(self, command: str):
        """
        Allows sending a raw command to the device. Generally this should not
        be used except for testing, since all commands should be defined in
        the yaml protocol configuration. No response messages are supported.
        """
        self._write(command)


class DeviceControllerSync(DeviceControllerBase):
    def __init__(self, device_type, url, serial_config, protocol_name):
        DeviceControllerBase.__init__(device_type, url, serial_config, protocol_name)
        self._connection = serial.serial_for_url(url, **serial_config)

    @synchronized
    def _write(self, request: bytes, skip=0):
        """
        :param request: request that is sent to the device
        :param skip: number of bytes to skip for end of transmission decoding
        :return ascii string returned by device (optional)
        """
        # clear existing buffer
        self._connection.reset_output_buffer()
        self._connection.reset_input_buffer()

        LOG.debug(f"Sending {self._device_type} @ {self._url}: {request}")

        # send the request and flush all the bytes to the connection
        self._connection.write(request)
        self._connection.flush()

        eol = self._protocol_defs.get(CONF_RESPONSE_EOL).encode("ascii")
        eol_len = len(eol)

        # receive response (if any)
        result = bytearray()
        while True:
            # FIXME: this is inefficient, but for now is fine
            c = self._connection.read(1)
            if not c:
                ret = bytes(result)
                LOG.info(result)
                raise serial.SerialTimeoutException(
                    "Connection timed out! Last received bytes {}".format(
                        [hex(a) for a in result]
                    )
                )

            # FIXME: need better name/description for skip
            result += c
            if len(result) > skip and eol == result[-eol_len:]:
                break

        ret = bytes(result)
        LOG.debug("Received from {self._device_type} @ {self._url}: %s", ret)
        return ret.decode("ascii")


# -----------------------------------------------------------------------------


class DeviceControllerAsync(DeviceControllerBase):
    def __init__(self, loop, device_type, url, serial_config, protocol_name):
        DeviceControllerBase.__init__(device_type, url, serial_config, protocol_name)
        self._loop = loop
        self._connection_ref = None

    async def _connection(self):
        """
        :return the connection to the RS232 device (lazy connect if none)
        """
        if not self._connection_ref:
            LOG.debug(
                f"Connecting to {self._device_type}/{self._protocol_name} @ {self._url}: %s %s",
                self._serial_config,
                self._protocol_config,
            )
            self._connection_ref = await async_get_rs232_protocol(
                self._url,
                DEVICE_CONFIG[self._device_type],
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


class DeviceController:
    @classmethod
    def create_device_controller(
        self, device_type: str, url: str, serial_config_overrides={}, event_loop=None
    ) -> DeviceControllerBase:
        """
        Create an instance of an DeviceControllerBase object given
        details about the given device.

        If an event_loop argument is passed in this will return the
        asynchronous implementation. By default the synchronous interface
        is returned.

        :param device_type: identifier for type of device (e.g. mcintosh)
        :param url: pyserial supported url for communication (e.g. '/dev/ttyUSB0' or 'socket://remote-host:7000/')
        :param config_overrides: dictionary of serial port configuration overrides (e.g. baudrate)

        :param event_loop: to get an interface that can be used asynchronously, pass in an event loop

        :return an instance of DeviceControllerBase
        """
        # ensure caller has specified a valid device_type
        config = DEVICE_CONFIG.get(device_type)
        if not config:
            LOG.error(f"Unsupported device type '{device_type}'")
            return None

        # caller can override the default serial port config for a given type
        # of device since the user could have changed settings on their
        # physical device (e.g. increasing the baudrate)
        serial_config = get_device_config(device_type, CONF_SERIAL_CONFIG)
        if serial_config_overrides:
            LOG.debug(f"Overriding serial config for {url}: {serial_config_overrides}")
            serial_config.update(serial_config_overrides)

        # ensure the device has a protocol defined
        protocol_name = get_device_config(device_type, CONF_PROTOCOL_NAME)
        if not protocol_name:
            LOG.error(
                f"Device type {device_type} is missing '{CONF_PROTOCOL_NAME}' config key"
            )
            return

        if event_loop:
            return DeviceControllerAsync(
                event_loop, device_type, url, serial_config, protocol_name
            )

        return DeviceControllerSync(device_type, url, serial_config, protocol_name)
