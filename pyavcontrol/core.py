import logging
from copy import copy, deepcopy

from .const import *  # noqa: F403

LOG = logging.getLogger(__name__)


def camel_case(text: str):
    """
    Convert string into a CamelCase format without any spaces or special characters
    """
    return re.sub("[^0-9a-zA-Z]+", "", re.sub("[-_.]+", " ", text).title())


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


def merge_nested_dicts(d1: dict, d2: dict) -> dict:
    """
    Merge two dictionaries with a nested data structure.

    # FIXME: consider using jsonmerge...rather than implementing own
    # complex merger!

    # FIXME: see also https://github.com/adobe/himl

    See https://noteable.io/blog/how-to-merge-dictionaries-in-python/
    """
    for key, value in d2.items():
        if not key in d1:
            d1[key] = value
            continue

        type1 = type(d1[key])
        type2 = type(value)
        if type1 != type2:
            LOG.warning(
                f"When merging dictionaries, different types for key '{key}', overwriting!: {type1} != {type2}"
            )
            d1[key] = value
        elif isinstance(d1[key], dict) and isinstance(value, dict):
            merge_nested_dicts(d1[key], value)
        elif isinstance(d1[key], list):
            # FIXME: what if duplicate items?
            d1[key] += value
        else:
            d1[key] = value
