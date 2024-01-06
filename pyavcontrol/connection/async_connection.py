import logging
import asyncio
import functools
import time
from functools import wraps

from ratelimit import limits
from serial_asyncio import create_serial_connection

from ..const import *  # noqa: F403

LOG = logging.getLogger(__name__)

FIVE_MINUTES = 5 * 60

# FIXME: for a specific instance we do not want communication to happen
# simultaneously...for now just lock ALL accesses to ANY device.
async_lock = asyncio.Lock()


def locked_coro(coro):
    @wraps(coro)
    async def wrapper(*args, **kwargs):
        async with async_lock:
            return await coro(*args, **kwargs)

    return wrapper


def get_connection_config(config, serial_config):
    return {}


async def async_get_rs232_connection(
    serial_port: str, config: dict, serial_config: dict, protocol_config: dict, loop
):
    # ensure only a single, ordered command is sent to RS232 at a time (non-reentrant lock)
    def locked_method(method):
        @wraps(method)
        async def wrapper(self, *method_args, **method_kwargs):
            async with self._lock:
                return await method(self, *method_args, **method_kwargs)

        return wrapper

    # check if connected, and abort calling provided method if no connection before timeout
    def ensure_connected(method):
        @wraps(method)
        async def wrapper(self, *method_args, **method_kwargs):
            try:
                await asyncio.wait_for(self._connected.wait(), self._timeout)
            except Exception:
                LOG.debug(
                    f"Timeout sending data to {self._serial_port}, no connection!"
                )
                return
            return await method(self, *method_args, **method_kwargs)

        return wrapper

    class RS232ControlProtocol(asyncio.Protocol):
        def __init__(self, serial_port, config, serial_config, protocol_config, loop):
            super().__init__()

            self._serial_port = serial_port
            self._config = config
            self._serial_config = serial_config
            self._loop = loop

            self._encoding = "ascii"
            self._response_eol = protocol_config[CONF_RESPONSE_EOL].encode(
                self._encoding
            )
            self._response_callback = None

            self._last_send = time.time() - 1
            self._timeout = self._config.get("timeout", DEFAULT_TIMEOUT)
            LOG.info(f"Timeout set to {self._timeout}")

            self._transport = None
            self._connected = asyncio.Event()
            self._q = asyncio.Queue()

            # ensure only a single, ordered command is sent to RS232 at a time (non-reentrant lock)
            self._lock = asyncio.Lock()

        def register_callback(self, callback) -> None:
            """Register a callback that is called for each response line"""
            self._response_callback = callback

        def connection_made(self, transport):
            self._transport = transport
            LOG.debug(f"Port {self._serial_port} opened {self._transport}")
            self._connected.set()

        def data_received(self, data):
            #            LOG.debug(f"Received from {self._serial_port}: {data}")
            asyncio.ensure_future(self._q.put(data))  # , loop=self._loop)

        def connection_lost(self, exc):
            LOG.debug(f"Port {self._serial_port} closed")

        async def _throttle_requests(self):
            """Throttle the number of RS232 sends per second to avoid causing timeouts"""
            min_time_between_commands = self._config[CONF_THROTTLE_RATE]
            delta_since_last_send = time.time() - self._last_send

            if delta_since_last_send < 0:
                delay = -1 * delta_since_last_send
                LOG.debug(f"Sleeping {delay} seconds until sending next RS232 request")
                await asyncio.sleep(delay)

            elif delta_since_last_send < min_time_between_commands:
                delay = min(
                    max(0, min_time_between_commands - delta_since_last_send),
                    min_time_between_commands,
                )
                await asyncio.sleep(delay)

        @locked_method
        @ensure_connected
        async def send(self, request: bytes, wait_for_reply=True, skip_initial_bytes=0):
            await self._throttle_requests()

            # clear all buffers of any data waiting to be read before sending the request
            self._transport.serial.reset_output_buffer()
            self._transport.serial.reset_input_buffer()
            while not self._q.empty():
                self._q.get_nowait()

            # send the request
            LOG.debug("Sending RS232 data %s", request)
            self._last_send = time.time()
            self._transport.serial.write(request)

            if not wait_for_reply:
                return

            # read the response
            data = bytearray()
            try:
                while True:
                    data += await asyncio.wait_for(self._q.get(), self._timeout)

                    # FIXME: investigate more robust reading data with prefixes (vs just skipping some bytes)
                    if self._response_eol in data[skip_initial_bytes:]:
                        # only return the first line
                        LOG.debug(
                            f"Received: %s (len=%d, eol={self._response_eol})",
                            bytes(data).decode(self._encoding, errors="ignore"),
                            len(data),
                        )
                        result_lines = data.split(self._response_eol)

                        # strip out any blank lines
                        result_lines = [value for value in result_lines if value != b""]

                        if len(result_lines) > 1:
                            LOG.debug(
                                "Multiple response lines passed to callbacks, but only returning first: %s",
                                result_lines,
                            )

                        # pass all lines to any registered callback
                        first_result = None
                        for line in result_lines:
                            # NOTE: May want to catch decode failures to figure out when
                            # characters are returned that do not match the encoding type
                            # e.g. DAX88 can return non-ASCII chars
                            result = line.decode(self._encoding, errors="ignore")
                            self._response_callback(result)

                            if not first_result:
                                first_result = result

                        return first_result

            except asyncio.TimeoutError:
                # log up to two times within a time period to avoid saturating the logs
                @limits(calls=2, period=FIVE_MINUTES)
                def log_timeout():
                    LOG.info(
                        f"Timeout for request '%s': received='%s' ({self._timeout} sec)",
                        request,
                        data,
                    )

                log_timeout()
                raise

    factory = functools.partial(
        RS232ControlProtocol, serial_port, config, serial_config, protocol_config, loop
    )

    LOG.info(f"Connecting to {serial_port}: {serial_config}")
    _, protocol = await create_serial_connection(
        loop, factory, serial_port, **serial_config
    )
    return protocol
