import logging

from ..connection import ConnectionBase
from ..const import *  # noqa: F403
from .base import DeviceClientBase

LOG = logging.getLogger(__name__)


class DeviceClient:
    @staticmethod
    def create(
        model_def: dict, url: str, serial_config_overrides={}, event_loop=None
    ) -> DeviceClientBase:
        """
        Creates a DeviceClient instance using the standard pyserial connection
        types supported by this library when given details about the model
        and connection url.

        If an event_loop argument is passed in this will return the
        asynchronous implementation. By default the synchronous interface
        is returned.

        :param model: dict, dictionary that describes the model
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
            from .asynchronous import DeviceClientAsync

            return DeviceClientAsync(model_def, url, serial_config, event_loop)

        else:
            from .synchronous import DeviceClientSync

            return DeviceClientSync(model_def, url, serial_config)
