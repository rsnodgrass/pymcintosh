import logging

from ..connection.asynchronous import async_get_rs232_connection, locked_coro
from ..const import *  # noqa: F403
from .base import DeviceControllerBase

LOG = logging.getLogger(__name__)


class DeviceControllerAsync(DeviceControllerBase):
    def __init__(
        self, model: str, url: str, serial_config: dict, protocol_name: str, loop
    ):
        DeviceControllerBase.__init__(model, url, serial_config, protocol_name)
        self._loop = loop
        self._connection_ref = None

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

    @locked_coro
    async def zone_status(self, zone: int):
        # FIXME: this has nothing to do with amp_type?  protocol!

        # if there is a list of zone status commands, execute that (some don't have a single command for status)
        # if get_protocol_config(amp_type, 'zone_status_commands'):
        #    return await self._zone_status_manual(zone)

        cmd = _zone_status_cmd(self._amp_type, zone)
        skip = get_device_config(amp_type, "zone_status_skip") or 0
        status_string = await self._protocol.send(cmd, skip=skip)

        status = ZoneStatus.from_string(self._amp_type, status_string)
        LOG.debug("Status: %s (string: %s)", status, status_string)
        if status:
            return status.dict
        return None
