"""Python client library for controlling McIntosh A/V processors and receivers"""

__version__ = "2023.11.18"

DEFAULT_TCP_IP_PORT = 4999 # IP2SL / Virtual IP2SL uses this port

BAUD_RATES = [9600, 14400, 19200, 38400, 57600, 115200]
DEFAULT_BAUD_RATE = 115200