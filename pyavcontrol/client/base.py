from __future__ import (  # postpone eval of annotations (for DeviceClient type annotation)
    annotations,
)

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable

from ..const import *  # noqa: F403

LOG = logging.getLogger(__name__)

# FIXME: at what layer is bytes encoding set?


class DeviceClient(ABC):
    """
    DeviceClientBase base class that defines operations allowed
    to control a device.
    """

    def __init__(self, model_def: dict, url: str, serial_config: dict):
        super().__init__()
        self._protocol_def = model_def
        self._url = url
        self._serial_config = serial_config
        self._callbacks = []

    @property
    def is_async(self):
        """
        :return: True if this client impemenation is asynchronous (asyncio) versus synchronous.
        """
        return False

    @abstractmethod
    def send_command(self, group: str, action: str, **kwargs) -> None:
        """
        Call a command by the group/action and args as defined in the
        device's protocol yaml. E.g.

        client.send_command(group, action, arg1=one, my_arg=my_arg)
        """
        raise NotImplementedError()

    @abstractmethod
    def send_raw(self, data: bytes) -> None:
        """
        Allows sending a raw data to the device. Generally this should not
        be used except for testing, since all commands should be defined in
        the yaml protocol configuration. No response messages are supported.
        """
        raise NotImplementedError()

    @abstractmethod
    def register_callback(self, callback: Callable[[str], None]) -> None:
        """
        Register a callback that is called when a message is received
        from the device.
        """
        raise NotImplementedError()

    def _command(self, model_id: str, format_code: str, args=None):
        """
        Convert group/action/args into the full command string that should be sent

        FIXME: is this still even used/referenced?
        """
        cmd_eol = self._protocol_def.get(CONF_COMMAND_EOL)
        cmd_separator = self._protocol_def.get(CONF_COMMAND_SEPARATOR)

        rs232_commands = self._protocol_def.get("commands")
        command = rs232_commands.get(format_code) + cmd_separator + cmd_eol

        return command.format(**args).encode(
            "ascii"
        )  # FIXME: should be proper encoding

    # @abstractmethod
    def describe(self) -> dict:
        return self._protocol_def

    @classmethod
    def create(
        cls, model_def: dict, url: str, serial_config_overrides=None, event_loop=None
    ) -> DeviceClient:
        """
        Creates a DeviceClient instance using the standard pyserial connection
        types supported by this library when given details about the model
        and connection url.

        NOTE: The model definition could be passed in from any source, though
        it is recommended to only use those from the DeviceClient library. That
        said, it MAY make sense to split the entire connection stuff into a more
        generalized library for serial/IP communication to legacy devices and
        have libraries in separate package that are domain specific.

        If an event_loop argument is passed in this will return the
        asynchronous implementation. By default, the synchronous interface
        is returned.

        :param model_def: dict, dictionary that describes the model
        :param url: pyserial supported url for communication (e.g. '/dev/ttyUSB0' or 'socket://remote-host:4999/')
        :param serial_config_overrides: dictionary of serial port configuration overrides (e.g. baudrate)
        :param event_loop: optionally to get an interface that can be used asynchronously, pass in an event loop

        :return an instance of DeviceControllerBase
        """
        model_id = model_def["id"]
        LOG.debug(f"Connecting to {model_id} at {url}")

        # caller can override the default serial port config for a given type
        # of device since the user could have changed settings on their
        # physical device (e.g. increasing the baud rate)
        serial_config = model_def.get("communication", {}).get(CONF_SERIAL_CONFIG, {})
        if serial_config_overrides:
            LOG.info(
                f"Overriding {model_id} serial config: {serial_config_overrides}; url={url}"
            )
            serial_config.update(serial_config_overrides)

        if event_loop:
            # lazy import the async client to avoid loading both sync/async
            from .async_client import DeviceClientAsync

            return DeviceClientAsync(model_def, url, serial_config, event_loop)
        else:
            from .sync_client import DeviceClientSync

            return DeviceClientSync(model_def, url, serial_config)
