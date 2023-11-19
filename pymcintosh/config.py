""" Read the configuration for supported devices """
import logging
import os

from .const import *  # noqa: F403

LOG = logging.getLogger(__name__)

DEVICE_CONFIG = {}
PROTOCOL_CONFIG = {}

CONFIG_DIR = os.path.dirname(__file__)


DEVICE_CONFIG = _load_config_dir(f"{CONFIG_DIR}/series")
PROTOCOL_CONFIG = _load_config_dir(f"{CONFIG_DIR}/protocols")
