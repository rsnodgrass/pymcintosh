import logging
from collections.abc import Callable

from ..connection.asynchronous import async_get_rs232_connection, locked_coro
from ..const import *  # noqa: F403
from .base import DeviceControllerBase

LOG = logging.getLogger(__name__)


class DeviceControllerAsync(DeviceControllerBase):
    def __init__(self, model: str, url: str, serial_config: dict, loop):
        DeviceControllerBase.__init__(self, model, url, serial_config)
        self._loop = loop
        self._connection_ref = None

    @locked_coro
    async def send_raw(self, data: bytes) -> None:
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug(f"Sending {self._model} @ {self._url}: %s", data.decode())

        # send the data and flush all the bytes to the connection
        connection = await self._connection()
        await connection.write(data)
        await connection.flush()

    @locked_coro
    async def send_command(self, data: str) -> None:
        await self.send_raw(data.bytes())

    @locked_coro
    def register_callback(self, callback: Callable[[str], None]) -> None:
        self._callbacks.append(callback)

    @locked_coro
    async def received_message(self):
        for cb in self._callbacks:
            await self._loop.call_soon(cb)

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