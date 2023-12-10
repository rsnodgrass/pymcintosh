import logging
from collections.abc import Callable

from ..const import *  # noqa: F403
from ..models import DeviceModels
from ..protocols import protocol_definitions

LOG = logging.getLogger(__name__)


class DeviceControllerBase:
    """
    DeviceControllerBase base class that defines operations allowed
    to control a device.
    """

    def __init__(self, model: str, url: str, serial_config: dict, protocol_name: str):
        self._model = model
        self._model_def = DeviceModels.get_config(model)

        self._url = url
        self._serial_config = serial_config

        self._protocol_name = protocol_name
        self._protocol_def = protocol_definitions()[protocol_name]

        self._callbacks = []

    def send_command(self, group: str, action: str, **kwargs):
        """
        Call a command by the group/action and args as defined in the
        device's protocol yaml.
        """
        LOG.error(f"Should be calling {group}.{action}({kwargs})")
        raise NotImplementedError()

    def send_raw(self, data: bytes) -> None:
        """
        Allows sending a raw data to the device. Generally this should not
        be used except for testing, since all commands should be defined in
        the yaml protocol configuration. No response messages are supported.
        """
        raise NotImplementedError()

    def register_callback(self, callback: Callable[[str], None]) -> None:
        """
        Register a callback that is called when a message is received
        from the device.
        """
        raise NotImplementedError()

    def _command(self, model: str, format_code: str, args={}):
        cmd_eol = self._protocol_def.get(CONF_COMMAND_EOL)
        cmd_separator = self._protocol_def.get(CONF_COMMAND_SEPARATOR)

        rs232_commands = self._protocol_def.get("commands")
        command = rs232_commands.get(format_code) + cmd_separator + cmd_eol

        return command.format(**args).encode("ascii")

    def describe(self) -> dict:
        return self._model_def

    def protocol(self):
        return self._protocol_def
