import logging
import re

from .const import *  # noqa: F403

LOG = logging.getLogger(__name__)

# FIXME: protocols are really DEFINITIONS, not "config"


def describe_protocol(self):
    """
    :returns JSON describing all commands and arguments that are available
    for this specific instance.
    """
    docs = {}

    vars = self._protocol_config["vars"]
    api = self._protocol_config["api"]

    for api_group, group_cfg in api.items():
        api_docs = {}

        for action, action_cfg in group_cfg["actions"]:
            action_docs = {}

            # include description, if any
            description = action_cfg["description"]
            if description:
                action_docs["description"] = description

            # extract any variables that are passed into the cmd
            # and include them
            cmd = action_cfg["cmd"]
            if "{" in cmd:
                action_docs["vars"] = {}

                # for var in cmd:
                #   if vars.get(var} ... include details about limits/values
                # FIXME

            api_docs[action] = action_docs

        docs[api_group] = api_docs
    return docs


# cached dictionary pattern matches for all responses for each protocol
def _precompile_response_patterns():
    """Precompile all response patterns"""
    precompiled = {}
    for protocol_type, config in PROTOCOL_CONFIG.items():
        patterns = {}

        LOG.debug(f"Precompile patterns for {protocol_type}")
        for name, pattern in config["responses"].items():
            # LOG.debug(f"Precompiling pattern {name}: {pattern}")
            patterns[name] = re.compile(pattern)
        precompiled[protocol_type] = patterns
    return precompiled


RS232_RESPONSE_PATTERNS = _precompile_response_patterns()
