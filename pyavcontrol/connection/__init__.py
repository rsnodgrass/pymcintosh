import logging

LOG = logging.getLogger(__name__)


class DeviceConnection:
    """
    Connection base class that defines communication APIs.
    """

    def __init__(self):
        LOG.error(f"Use factory method create(url, config_overrides")
        raise NotImplementedError()

    def is_connected(self) -> bool:
        """
        :return: True if the connection is established
        """
        raise NotImplementedError()

    def send(self, data: bytes) -> None:
        """
        Send data to the remote device
        """
        raise NotImplementedError()

    def register_callback(self, callback) -> None:
        """
        Register a callback that will be called for each response from the connection
        """
        raise NotImplementedError()


class Connection:
    @staticmethod
    def create(
        url: str, connection_config=None, event_loop=None
    ) -> DeviceConnection | None:
        """
        Create an Connection instance given details about the given device.

        If an event_loop argument is passed in this will return the
        asynchronous implementation. By default, the synchronous interface
        is returned.

        :param url: pyserial supported url for communication (e.g. '/dev/ttyUSB0' or 'socket://remote-host:7000/')
        :param connection_config: pyserial connection configuration (optional)
        :param event_loop: pass in an event loop to get an interface that can be used asynchronously (optional)

        :return an instance of DeviceConnection
        """
        if not connection_config:
            connection_config = {}

        # FIXME: Types of config needed:
        #  - connection (pyserial style)...must be passed in since it is determined based on connection type (ip, rs232, etc)
        #
        #  - timeouts/etc (from ???)
        #  - encoding (from protocol def)

        LOG.debug(f"Connecting to {url}: %s", connection_config)

        if event_loop:
            from pyavcontrol.connection.async_connection import AsyncDeviceConnection

            return AsyncDeviceConnection(url, connection_config, event_loop)
        else:
            from pyavcontrol.connection.async_connection import SyncDeviceConnection

            return SyncDeviceConnection(url, connection_config, event_loop)
