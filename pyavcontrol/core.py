import logging
import re
from copy import copy, deepcopy
from typing import List

from .const import *  # noqa: F403

LOG = logging.getLogger(__name__)

NAMED_REGEX_PATTERN = re.compile(r"\(\?P\<(?P<name>.+)\>(?P<regex>.+)\)")
FSTRING_ARG_PATTERN = re.compile(r"\{(?P<arg_name>.+)\}")


def extract_named_regex(text: str) -> dict:
    """
    Parse out named regex patterns from text into a dictionary of
    names and associated regex.
    """
    named_regex = {}
    for m in re.finditer(NAMED_REGEX_PATTERN, text):
        named_regex[m.group(1)] = m.group(2)
    return named_regex


def missing_keys_in_dict(required_keys: List[str], d: dict) -> List[str]:
    """
    Checks that the provided dictionary contains all the required keys,
    and if not, return a list of the missing keys.
    """
    missing_keys = []
    for key in required_keys:
        if key not in d:
            missing_keys += key
    return missing_keys


def substitute_fstring_vars(fstring: str, vars: dict) -> str:
    # see also https://stackoverflow.com/questions/42497625/how-to-postpone-defer-the-evaluation-of-f-strings
    return fstring.format(**vars)


def get_fstring_vars(text: str) -> List[str]:
    """
    Parse out all the F-string style arguments from the given string with the
    name and the complete formatting as value.
    """
    vars = []

    # extract args from the regexp pattern of parameters
    for m in re.finditer(FSTRING_ARG_PATTERN, text):
        var = m.group(1)
        # remove any special format strings in the var to just get the name
        var = var.split(":")[0]
        vars.append(var)
    return vars


def camel_case(text: str) -> str:
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


# FIXME: delete this, as we no longer are merging dictionaries at runtime!
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
