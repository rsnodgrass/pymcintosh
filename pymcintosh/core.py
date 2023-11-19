import logging
import os

import yaml

from .const import *  # noqa: F403

LOG = logging.getLogger(__name__)


def get_subkey(dictionary: dict, top_key: str, key: str, log_missing=True):
    """Load a subkey from a nested dictionary and log if missing"""
    d = dictionary.get(top_key)
    if not d:
        if log_missing:
            LOG.warning(
                f"Missing top level key '{top_key}' for subkey '{key}'; returning None"
            )
        return None

    value = dictionary.get(key)
    if value is None and log_missing:
        LOG.warning(f"Missing subkey '{key}' under key '{top_key}'; returning None")
    return value


def load_yaml_file(filepath: str):
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
                filepath = os.path.join(dir, filename)
                y = load_yaml_file(filepath)
                if y:
                    key_name = filename.split(".yaml")[0]
                    yaml_dict[key_name] = y
        except Exception as e:
            LOG.warning(f"Failed parsing YAML {filename}; ignoring: {e}")

    return yaml_dict
