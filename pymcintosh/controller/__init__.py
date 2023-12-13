import logging

from ..connection import ConnectionBase
from ..const import *  # noqa: F403
from ..models import DeviceModel
from .base import DeviceControllerBase

LOG = logging.getLogger(__name__)

class DeviceController:
    @staticmethod
    def create(
        model_id: str, url: str, serial_config_overrides={}, event_loop=None
    ) -> DeviceControllerBase:
        """
        Convenience function that creates a DeviceController instance using 
        the standard pyserial Connection types supported by this library when
        given details about the model and connection url.
        
        This simplifies calling code which only need the typical use of this
        library, therefore skipping the need to wire the model/connection/controller
        instances together manually using dependency injection.

        If an event_loop argument is passed in this will return the
        asynchronous implementation. By default the synchronous interface
        is returned.

        :param model: identifier for the device model (e.g. mx160)
        :param url: pyserial supported url for communication (e.g. '/dev/ttyUSB0' or 'socket://remote-host:4999/')
        :param serial_config_overrides: dictionary of serial port configuration overrides (e.g. baudrate)

        :param event_loop: optionally to get an interface that can be used asynchronously, pass in an event loop

        :return an instance of DeviceControllerBase
        """
        LOG.debug(f"Connecting to model {model_id} at {url}")
        device = DeviceModel(model_id)

        # caller can override the default serial port config for a given type
        # of device since the user could have changed settings on their
        # physical device (e.g. increasing the baud rate)
        serial_config = device.config.get('communication', {}).get(CONF_SERIAL_CONFIG)
        if serial_config_overrides:
            LOG.info(
                f"Overriding {model} serial config: {serial_config_overrides}; url={url}"
            )
            serial_config.update(serial_config_overrides)

        if event_loop:
            # lazy import the async controller to avoid loading both sync/async
            from .asynchronous import DeviceControllerAsync

            return DeviceControllerAsync(
                device, url, serial_config, event_loop
            )

        # lazy import the sync controller to avoid loading both sync/async
        from .synchronous import DeviceControllerSync

        return DeviceControllerSync(device, url, serial_config)
