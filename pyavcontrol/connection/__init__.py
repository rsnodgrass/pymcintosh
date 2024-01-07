import logging

LOG = logging.getLogger(__name__)


# FIXME: implement sync and async


class DeviceConnection:
    """
    Connection base class that defines communication APIs.
    """

    def __init__(self):
        LOG.error(f"Use factory method create(url, config_overrides")
        raise NotImplementedError()

    def send(self, data: bytes) -> None:
        """
        Send data
        """
        raise NotImplementedError()

    def register_callback(self, callback) -> None:
        """
        Register a callback that will be called for each response from the connection
        """
        raise NotImplementedError()


class Connection:
    @staticmethod
    def create(url: str, config=None, event_loop=None) -> ConnectionBase | None:
        """
        Create an Connection instance given details about the given device.

        If an event_loop argument is passed in this will return the
        asynchronous implementation. By default the synchronous interface
        is returned.

        :param url: pyserial supported url for communication (e.g. '/dev/ttyUSB0' or 'socket://remote-host:7000/')
        :param config: optional serial connection configuration
        :param event_loop: to get an interface that can be used asynchronously, pass in an event loop

        :return an instance of ConnectionBase
        """
        if config is None:
            config = {}

        LOG.debug(f"Connecting to {url}: %s", config)
        return None

        if event_loop:
            return None
            # lazy import the async controller to avoid loading both sync/async
        #    from .async_connection import DeviceControllerAsync

        #    return DeviceControllerAsync(
        #        model, url, connection_config, event_loop
        #    )

        # lazy import the sync controller to avoid loading both sync/async
        # from sync import DeviceControllerSync

        # return DeviceControllerSync(model, url, connection_config)
