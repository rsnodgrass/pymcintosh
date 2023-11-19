import logging
import os

import yaml

from .const import *  # noqa: F403

LOG = logging.getLogger(__name__)


def get_with_log(name, dictionary: dict, key: str, log_missing=True):
    value = dictionary.get(key)
    if value is None and log_missing:
        LOG.warning(f"Missing key '{key}' in dictionary '{name}'; returning None")
    return value


def yaml_load_helper(filepath: str):
    """Load the a yaml file with extra logging and extraction of top level"""
    with open(filepath) as stream:
        try:
            y = yaml.load(stream, Loader=yaml.FullLoader)
            return y[0]
        except yaml.YAMLError as exc:
            LOG.error(f"Failed reading YAML {filepath}: {exc}")
            return None


def load_yaml_dir(dir: str):
    """
    Load all *.yaml files in a directory and create a combined
    dictionary of the yaml content.
    """
    yaml_dict = {}

    for filename in os.listdir(dir):
        try:
            if filename.endswith(".yaml"):
                series = filename.split(".yaml")[0]
                filepath = os.path.join(dir, filename)
                y = yaml_load_helper(filepath)
                if y:
                    yaml_dict[series] = config
        except Exception as e:
            LOG.warning(f"Failed parsing YAML {filename}; ignoring: {e}")

    return yaml_dict
