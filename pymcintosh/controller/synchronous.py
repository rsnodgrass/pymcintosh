import logging

import serial

from ..connection.sync import synchronized
from ..const import *  # noqa: F403
from .base import DeviceControllerBase

LOG = logging.getLogger(__name__)


class DeviceControllerSync(DeviceControllerBase):
    def __init__(self, model: str, url: str, serial_config: dict, protocol_name: str):
        DeviceControllerBase.__init__(self, model, url, serial_config, protocol_name)
        self._connection = serial.serial_for_url(url, **serial_config)

    @synchronized
    def send_raw(self, data: bytes) -> None:
        """
        Send raw data to the device's connection
        """
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug(f"Sending {self._model} @ {self._url}: %s", data.decode())

        # send the data and flush all the bytes to the connection
        self._connection.write(data)
        self._connection.flush()

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

        self.send_raw(bytes)

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
