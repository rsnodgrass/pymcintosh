import logging

from ..const import *  # noqa: F403
from ..models import Models
from ..protocol import PROTOCOL_DEFS

LOG = logging.getLogger(__name__)


class DeviceControllerBase:
    """
    DeviceControllerBase base class that defines operations allowed
    to control a device.
    """

    def __init__(self, model: str, url: str, serial_config: dict, protocol_name: str):
        self._model = model
        self._model_def = Models.get_config(self._model)

        self._url = url
        self._serial_config = serial_config

        self._protocol_name = protocol_name
        self._protocol_def = PROTOCOL_DEFS[protocol_name]

    def describe(self) -> dict:
        return self._model_def

    def send_raw(self, data: bytes) -> None:
        """
        Send raw data to the device's connection (not a message)
        """
        raise NotImplementedError()

    def _write(self, data: bytes, skip=0):
        """
        Write the provided data to the connected device.
        """
        raise NotImplementedError()

    def _command(self, model: str, format_code: str, args={}):
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
