import logging
import re

from .const import *  # noqa: F403
from .core import load_yaml_dir

LOG = logging.getLogger(__name__)

# FIXME: protocols are really DEFINITIONS, not "config"

PROTOCOL_DEFS = load_yaml_dir(f"{CONFIG_DIR}/protocols")


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


# FIXME: rewrite this
# cached dictionary pattern matches for all responses for each protocol
def _precompile_response_patterns():
    """Precompile all response patterns"""
    precompiled = {}
    for protocol_type, config in PROTOCOL_DEFS.items():
        LOG.debug(f"Precompiling patterns for protocol {protocol_type}")

        api = config.get("api")
        if not api:
            LOG.error(f"Missing 'api' in protocol {protocol_type}")
            continue

        for group_name, group_def in api.items():
            LOG.debug(f"Processing protocol {protocol_type} group {group_name}")

            actions = group_def.get("actions")
            if not actions:
                LOG.error(f"Missing 'actions' in {protocol_type}.{group_name}")
                continue

            for action_name, action_def in actions.items():
                name = f"{group_name}.{action_name}"
                print(name)

                # check if there is a message response, if so precompile
                msg_pattern = action_def.get("msg")
                if msg_pattern:
                    LOG.debug(f"Precompiling pattern {name}: {msg_pattern}")
                    precompiled[name] = re.compile(msg_pattern)

    return precompiled


RS232_RESPONSE_PATTERNS = _precompile_response_patterns()
