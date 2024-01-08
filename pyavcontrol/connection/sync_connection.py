import logging
from abc import ABC
from functools import wraps
from threading import RLock

import serial
from syncer import sync

from pyavcontrol.connection import DeviceConnection
from pyavcontrol.connection.async_connection import async_get_rs232_connection
from pyavcontrol.const import CONF_RESPONSE_EOL, DEFAULT_ENCODING, DEFAULT_EOL

LOG = logging.getLogger(__name__)

sync_lock = RLock()


def synchronized(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with sync_lock:
            return func(*args, **kwargs)

    return wrapper


class SyncDeviceConnection(DeviceConnection, ABC):
    """
    Synchronous device connection implementation (NOT YET IMPLEMENTED)
    """

    def __init__(self, url: str, config: dict, connection_config: dict):
        """
        :param url: pyserial compatible url
        """
        super.__init__()

        self._url = url
        self._config = config
        self._connection_config = connection_config

        self._encoding = connection_config.get("encoding", DEFAULT_ENCODING)
        self._eol = connection_config.get(CONF_RESPONSE_EOL, DEFAULT_EOL).encode(
            self._encoding
        )
        # self._skip_bytes

        # FIXME: contemplate on this more, do we really want to reset/clear
        self._clear_before_new_commands = connection_config.get(
            "clear_before_new_commands", False
        )

        self._port = serial.serial_for_url(self._url, **self._connection_config)

    def send(self, data: bytes) -> None:
        """
        :param data: request that is sent to the device
        :param skip: number of bytes to skip for end of transmission decoding
        :return:  string returned by device
        """
        # clear any pending transactions
        if self._clear_before_new_commands:
            self._port.reset_output_buffer()
            self._port.reset_input_buffer()

        # print(f"Sending:  {request}")
        LOG.debug(f"SEND {self._url}: {data}")

        # send data and force flush to send immediately
        self._port.write(data)
        self._port.flush()

    def handle_receive(self) -> str:
        skip = 0

        len_eol = len(self._eol)

        # receive
        result = bytearray()
        while True:
            c = self._port.read(1)
            # print(c)
            if not c:
                ret = bytes(result)
                LOG.info(result)
                raise serial.SerialTimeoutException(
                    "Connection timed out! Last received bytes {}".format(
                        [hex(a) for a in result]
                    )
                )
            result += c
            if len(result) > skip and result[-len_eol:] == self._eol:
                break

        ret = bytes(result)
        LOG.debug(f'Received {self._url} "%s"', ret)
        return ret.decode(self._encoding)

    def register_callback(self, callback) -> None:
        """
        Register a callback that will be called for each response from the connection
        """
        raise NotImplementedError()
