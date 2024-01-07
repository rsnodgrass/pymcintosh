import logging
import asyncio
from abc import ABC
from functools import wraps
from threading import RLock

import serial
from syncer import sync

from pyavcontrol.connection import DeviceConnection
from pyavcontrol.connection.async_connection import async_get_rs232_connection

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

    def __init__(
        self, url: str, config: dict, serial_config: dict, protocol_config: dict
    ):
        """
        :param url: pyserial compatible url
        """
        super.__init__()

        self._url = url
        self._config = config
        self._serial_config = serial_config
        self._protocol_config = protocol_config

        self._encoding = protocol_config.get("encoding", "ascii")

        # FIXME: contemplate on this more, do we really want to reset/clear
        self._clear_before_new_commands = True

        self._port = serial.serial_for_url(self._url, **self._serial_config)

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
        LOG.debug(f"Sending:  {data}")

        # send
        self._port.write(data)
        self._port.flush()

    def handle_receive(self) -> str:
        skip = 0

        self._response_eol = protocol_config[CONF_RESPONSE_EOL].encode(self._encoding)
        len_eol = len(self._response_eol)

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
            if len(result) > skip and result[-len_eol:] == self._response_eol.encode(
                self._encoding
            ):
                break

        ret = bytes(result)
        LOG.debug('Received "%s"', ret)
        #            print(f"Received: {ret}")
        return ret.decode(self._encoding)

    def register_callback(self, callback) -> None:
        """
        Register a callback that will be called for each response from the connection
        """
        raise NotImplementedError()
