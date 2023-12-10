import logging

from ..const import *  # noqa: F403
from ..models import DeviceModels
from .base import DeviceControllerBase

LOG = logging.getLogger(__name__)


class DeviceController:
    @staticmethod
    def create(
        model: str, url: str, serial_config_overrides=dict, event_loop=None
    ) -> DeviceControllerBase:
        """
        Create an instance of an DeviceControllerBase object given
        details about the given device.

        If an event_loop argument is passed in this will return the
        asynchronous implementation. By default the synchronous interface
        is returned.

        :param model: identifier for the device model (e.g. mx160) as found in series/
        :param url: pyserial supported url for communication (e.g. '/dev/ttyUSB0' or 'socket://remote-host:7000/')
        :param serial_config_overrides: dictionary of serial port configuration overrides (e.g. baudrate)

        :param event_loop: to get an interface that can be used asynchronously, pass in an event loop

        :return an instance of DeviceControllerBase
        """
        LOG.debug(f"Connecting to model {model} at {url}")

        config = DeviceModels.get_config(model)
        if not config:
            LOG.error(f"Model '{model}' has no definitions found in models/*.yaml")
            return None

        # caller can override the default serial port config for a given type
        # of device since the user could have changed settings on their
        # physical device (e.g. increasing the baud rate)
        serial_config = config.get(CONF_SERIAL_CONFIG)
        if serial_config_overrides:
            LOG.info(
                f"Overriding {model} serial config: {serial_config_overrides}; url={url}"
            )
            serial_config.update(serial_config_overrides)

        # ensure the device has a protocol defined
        protocol_name = config.get(CONF_PROTOCOL_NAME)
        if not protocol_name:
            LOG.error(f"Model {model} missing '{CONF_PROTOCOL_NAME}' config key")
            return

        if event_loop:
            # lazy import the async controller to avoid loading both sync/async
            from .asynchronous import DeviceControllerAsync

            return DeviceControllerAsync(
                model, url, serial_config, protocol_name, event_loop
            )

        # lazy import the sync controller to avoid loading both sync/async
        from .synchronous import DeviceControllerSync

        return DeviceControllerSync(model, url, serial_config, protocol_name)
