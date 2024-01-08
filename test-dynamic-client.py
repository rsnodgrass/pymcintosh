#!/usr/bin/env python3
#
# Some examples of dynamic class generation
#   https://github.com/boto/boto3
#
# make sure that help(client) called on a client object actually shows documentation!
# show example of using ipython
#
# ``` python
# In [1]: from pyavcontrol import get_model, create_client
# In [2]: m = get_model('mcintosh_mx160')
# In [3] c = create_client(m)
# In [4]: c.
# c.mute       c.power
# c.volume
#
# In [5]: c.mute
# c.mute.on     c.mute.off
#
# In [6]: c.mute.on()
# ```

import logging
from dataclasses import dataclass
from typing import List

import coloredlogs

from pyavcontrol import DeviceClient, DeviceModelLibrary
from pyavcontrol.core import (
    camel_case,
    extract_named_regex,
    get_fstring_vars,
    missing_keys_in_dict,
    substitute_fstring_vars,
)

LOG = logging.getLogger(__name__)
coloredlogs.install(level="DEBUG")

MODELS = [
    "hdfury_vrroom",
    "trinnov_altitude32",
    "lyngdorf_cd2",
    "mcintosh_mx160",
    "xantech_mx88_audio",
    "lyngdorf_tdai3400",
]


class ActionArgsValidator:
    def __init__(self):
        return


class ActionParser:
    def __init__(self):
        return


class DynamicActions:
    """
    Dynamically created class representing a group of actions that can be called
    on a device.
    """

    def __init__(self, model_name, actions_def):
        self._model_name = model_name
        self._actions_def = actions_def


def _create_action_method(
    client: DeviceClient, group_name: str, action_name: str, action_def: dict
):
    """
    Creates a dynamic method that makes calls against the provided client using
    the command format for the given action definition.

    This returns an asynchronous method if an event_loop is provided, otherwise
    a synchronous method is returned by default. Calling code knows whether they
    instantiated a synchronous or asynchronous client.
    """
    required_args = _get_args_for_command(action_def)

    def _prepare_request(**kwargs):
        if missing_keys := missing_keys_in_dict(required_args, kwargs):
            err_msg = f"Call to {group_name}.{action_name} missing required keys {missing_keys}, skipping!"
            LOG.error(err_msg)
            raise ValueError(err_msg)

        if cmd := action_def.get("cmd"):
            if fstring := cmd.get("fstring"):
                request = substitute_fstring_vars(fstring, kwargs)
                return request.encode("ascii")
        return None

    def _activity_call_sync(**kwargs):
        """
        Synchronous version of making a client call
        """
        if request := _prepare_request(**kwargs):
            return client.send_raw(request)
        LOG.warning(f"Failed to make request for {group_name}.{action_name}")

    async def _activity_call_async(self, **kwargs):
        """
        Asynchronous version of making a client call is used when an event_loop
        is provided. Calling code knows whether they instantiated a synchronous
        or asynchronous client.
        """
        if request := _prepare_request(**kwargs):
            return await client.send_raw(request)
        LOG.warning(f"Failed to make request for {group_name}.{action_name}")

    if client.is_async:
        return _activity_call_async
    else:
        return _activity_call_sync


def _get_vars_for_message(action_def: dict) -> dict:
    """
    Parse out all variables that would be returned in the msg response
    for this action.

    :return: list of variables for the message
    """
    if msg := action_def.get("msg"):
        if regex := msg.get("regex"):
            named_regex = extract_named_regex(regex)
            return named_regex
    return {}


def _get_args_for_command(action_def: dict) -> List[str]:
    """
    Parse the command definition into an array of arguments for the action, with a dictionary
    describing additional type information about each argument.

    :return: list of arguments for a given command
    """
    args = []

    if cmd := action_def.get("cmd"):
        if regex := cmd.get("regex"):
            named_regex = extract_named_regex(regex)
            LOG.info(f"Command regex found BUT IGNORING! {named_regex}")

        fstring = cmd.get("fstring")
        if args := get_fstring_vars(fstring):
            # FIXME: embed all the cmd_patterns into this
            return args

    return args


def _generate_docs_for_action(action_name: str, action_def: dict):
    """
    Return formatted Sphinx documentation for a given action definition
    """
    doc = action_def.get("description", "")

    # append details for all command arguments
    if args := _get_args_for_command(action_def):
        args_docs = action_def.get("cmd", {}).get("docs", {})
        for arg in args:
            arg_doc = args_docs.get(arg, "see protocol manual from manufacturer")
            doc += f"\n:param {arg}: {arg_doc}"

    # append details if a response message is defined for this action
    if v := _get_vars_for_message(action_def):
        msg_docs = action_def.get("msg", {}).get("docs", {})
        doc += "\n:return: {"
        for var in v:
            var_doc = msg_docs.get(arg, "see protocol manual from manufacturer")
            doc += f"\n   {var}: {var_doc},"
        doc += "\n}"

    # FIXME: may need type info from the overall api variables section
    return doc


@dataclass(frozen=True)
class ClientAPIGroup:
    client: DeviceClient
    model_id: str
    group_name: str
    actions_model: dict


@dataclass(frozen=True)
class ClientAPIAction:
    group: ClientAPIGroup
    name: str
    definition: dict


def create_activity_group_class(
    client: DeviceClient,
    model_id: str,
    group_name: str,
    actions_model: dict,
    cls_bases=None,
):
    # CamelCase the model and actions group to represent this dynamic class of action methods
    cls_name = camel_case(f"{model_id} {group_name}")

    if not cls_bases:
        cls_bases = (DynamicActions,)
    cls_props = {}

    # dynamically add methods (and associated documentation) for each action
    for action_name, action_def in actions_model["actions"].items():
        # handle yamlfmt/yamlfix rewriting of "on" and "off" as YAML keys into bools
        if type(action_name) is bool:
            action_name = "on" if action_name else "off"

        # ClientAPIAction(group=group, name=action_name, definition=action_def)
        method = _create_action_method(client, group_name, action_name, action_def)
        print(f"{group_name}.{action_name}")

        # FIXME: danger will robinson...potential exploits (need to explore how to filter out)
        method.__name__ = action_name  # FIXME: what about __qualname__
        method.__doc__ = _generate_docs_for_action(action_name, action_def)

        cls_props[action_name] = method

    # return the new dynamic class that contains the above actions
    cls = type(cls_name, cls_bases, cls_props)
    return cls(model_id, actions_model["actions"])


# Process:
#  1. create mixin class
#  2. inject the mixin to the DeviceClient
def inject_client_api(client: DeviceClient, model_id: str, model_def: dict):
    """
    Add a property at the top level of a DeviceClient class that exposes a
    group of actions that can be called. If none are specified in the
    model definition, the client is returned unchanged.
    """
    api = model_def.get("api", {})

    for group_name, group_actions in api.items():
        LOG.debug(f"Adding property for group {group_name}")
        group_class = create_activity_group_class(
            client, model_id, group_name, group_actions
        )
        setattr(type(client), group_name, group_class)

        help(group_class)  # FIXME

    # FIXME: after injection do we change the TYPE of the client to the SPECIFIC model E.g. McIntoshMx160Client
    class_name = camel_case(f"{model_id} Client")
    LOG.debug(f"Created {class_name} client with injected activities")
    #    client.__name__ = class_name
    #    client.__qualname__ = f"pyavcontrol.{class_name}"

    return client


def main():
    url = "socket://localhost:4999"

    library = DeviceModelLibrary.create()
    # supported_models = library.supported_models()
    supported_models = ["mcintosh_mx160"]

    for model_id in supported_models:
        model_def = library.load_model(model_id)

        client = DeviceClient.create(model_def, url)
        print(type(client))

        # FIXME: the type of the returned DeviceClient should be the SPECIFIC model E.g. McIntoshMx160Client
        client = inject_client_api(client, model_id, model_def)
        print(type(client))

        help(client)
        return

    # client.source.get()
    # client.source.next()
    # client.source.set()
    # print(client.software.info())


if __name__ == "__main__":
    main()
