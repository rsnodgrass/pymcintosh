import logging
from abc import ABC
from collections.abc import Callable

import serial

from ..connection.sync_connection import synchronized
from ..const import *  # noqa: F403
from .base import DeviceClient

LOG = logging.getLogger(__name__)


class DeviceClientSync(DeviceClient, ABC):
    def __init__(self, model_def: dict, url: str, serial_config: dict):
        DeviceClient.__init__(self, model_def, url, serial_config)
        self._connection = serial.serial_for_url(url, **serial_config)
        self._callback = None
        self._encoding = serial_config.get("encoding", DEFAULT_ENCODING)

    @synchronized
    def send_raw(self, data: bytes) -> None:
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug(f"Sending {self._url}: {data}")

        # send the data and flush all the bytes to the connection
        self._connection.write(data)
        self._connection.flush()

    @synchronized
    def send_command(self, group: str, action: str, **kwargs) -> None:
        # self.send_raw(data.bytes())
        LOG.error(f"Not implemented!")  # FIXME

    @synchronized
    def register_callback(self, callback: Callable[[str], None]) -> None:
        if not callable(callback):
            raise ValueError("Callback is not Callable")
        self._callback = callback

    @synchronized
    def received_message(self):
        if self._callback:
            LOG.error(f"Callback not implemented!! {cb}")  # FIXME
            # self._loop.call_soon(cb)

    @synchronized
    def _write(self, request: bytes, skip=0):
        """
        :param request: request that is sent to the device
        :param skip: number of bytes to skip for end of transmission decoding
        :return ascii string returned by device (optional)
        """
        # clear existing buffer
        self._connection.reset_output_buffer()
        self._connection.reset_input_buffer()

        self.send_raw(request)

        # FIXME: what is this?
        eol = self._protocol_defs.get(CONF_RESPONSE_EOL).encode("ascii")
        eol_len = len(eol)

        # receive response (if any)
        result = bytearray()
        while True:
            # FIXME: this is inefficient, but for now is fine
            c = self._connection.read(1)
            if not c:
                ret = bytes(result)
                LOG.info(result)
                raise serial.SerialTimeoutException(
                    "Connection timed out! Last received bytes {}".format(
                        [hex(a) for a in result]
                    )
                )

            # FIXME: need better name/description for skip
            result += c
            if len(result) > skip and eol == result[-eol_len:]:
                break

        ret = bytes(result)
        LOG.debug("Received from {self._device_type} @ {self._url}: %s", ret)
        return ret.decode("ascii")
