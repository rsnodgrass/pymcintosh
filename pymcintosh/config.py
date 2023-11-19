""" Read the configuration for supported devices """
import logging

from .const import *  # noqa: F403
from .core import *  # noqa: F403

LOG = logging.getLogger(__name__)

PROTOCOL_CONFIG = load_yaml_dir(f"{CONFIG_DIR}/protocols")
