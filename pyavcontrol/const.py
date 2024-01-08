"""Python client library for controlling A/V processors and receivers"""

import os

DEFAULT_TCP_IP_PORT = 4999  # IP2SL / Virtual IP2SL uses this port
DEFAULT_TIMEOUT = 1.0

PACKAGE_PATH = os.path.dirname(__file__)

DEFAULT_MODEL_LIBRARIES = [
    f"{PACKAGE_PATH}/data/flattened",
    f"{PACKAGE_PATH}/data/src",
]  # FIXME: remove this later

DEFAULT_ENCODING = "ascii"
DEFAULT_EOL = "\r\n"

CONF_COMMAND_EOL = "command_eol"
CONF_RESPONSE_EOL = "response_eol"
CONF_COMMAND_SEPARATOR = "command_separator"
CONF_SERIAL_CONFIG = "rs232"

CONF_THROTTLE_RATE = "min_time_between_commands"
