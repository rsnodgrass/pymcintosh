import logging

from ..connection.asynchronous import async_get_rs232_connection, locked_coro
from ..const import *  # noqa: F403
from .base import DeviceControllerBase

LOG = logging.getLogger(__name__)


class DeviceControllerAsync(DeviceControllerBase):
    def __init__(
        self, model: str, url: str, serial_config: dict, protocol_name: str, loop
    ):
        DeviceControllerBase.__init__(self, model, url, serial_config, protocol_name)
        self._loop = loop
        self._connection_ref = None

    @locked_coro
    async def send_raw(self, data: bytes) -> None:
        """
        Send raw data to the device's connection (not a message)
        """
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug(f"Sending {self._model} @ {self._url}: %s", data.decode())

        # send the data and flush all the bytes to the connection
        connection = await self._connection()
        await connection.write(data)
        await connection.flush()

    async def _connection(self):
        """
        :return the connection to the RS232 device (lazy connect if none)
        """
        if not self._connection_ref:
            LOG.debug(
                f"Connecting to {self._model}/{self._protocol_name} @ {self._url}: %s %s",
                self._serial_config,
                self._protocol_def,
            )

            self._connection_ref = await async_get_rs232_connection(
                self._url,
                self._model_def,
                self._serial_config,
                self._protocol_def,
                self._loop,
            )
        return self._connection_ref
