import logging

LOG = logging.getLogger(__name__)

class ConnectionBase:

    """
    Connection base class that defines communication APIs.
    """
    def __init__(self):
        LOG.error(f"Use factory method create(url, config_overrides")
        raise NotImplementedError()

    def send(self, data: bytes):
        raise NotImplementedError()

    def register_response_callback(self, callback):
        """
        Register a callback that is called for each response line
        """
        self._response_callback = callback


class Connection:
    @staticmethod
    def create(
        url: str, config={}, event_loop=None
    ) -> ConnectionBase:
        """
        Create an Connection instance given details about the given device.

        If an event_loop argument is passed in this will return the
        asynchronous implementation. By default the synchronous interface
        is returned.

        :param url: pyserial supported url for communication (e.g. '/dev/ttyUSB0' or 'socket://remote-host:7000/')
        :param event_loop: to get an interface that can be used asynchronously, pass in an event loop

        :return an instance of ConnectionBase
        """
        LOG.debug(f"Connecting to {url}: %s", config)
        return None
    
        #if event_loop:
            # lazy import the async controller to avoid loading both sync/async
        #    from asynchronous import DeviceControllerAsync

        #    return DeviceControllerAsync(
        #        model, url, connection_config, event_loop
        #    )

        # lazy import the sync controller to avoid loading both sync/async
        #from sync import DeviceControllerSync

        #return DeviceControllerSync(model, url, connection_config)

    