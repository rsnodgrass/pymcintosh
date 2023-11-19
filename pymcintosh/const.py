"""Python client library for controlling McIntosh A/V processors and receivers"""

import os

DEFAULT_TCP_IP_PORT = 4999  # IP2SL / Virtual IP2SL uses this port
DEFAULT_TIMEOUT = 1.0

CONFIG_DIR = os.path.dirname(__file__)

CONF_SERIAL_CONFIG = "rs232"
CONF_PROTOCOL_NAME = "protocol"

CONF_COMMAND_EOL = "command_eol"
CONF_RESPONSE_EOL = "response_eol"
CONF_COMMAND_SEPARATOR = "command_separator"

CONF_THROTTLE_RATE = "min_time_between_commands"
