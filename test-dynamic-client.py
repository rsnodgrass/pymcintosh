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


def _get_client_method(
    client: DeviceClient,
    group_name: str,
    action_name: str,
    action_def: dict,
    event_loop=None,
):
    required_args = _get_args_for_command(action_def)

    def _prepare_cmd(**kwargs):
        if cmd := action_def.get("cmd"):
            if fstring := cmd.get("fstring"):
                return substitute_fstring_vars(fstring, kwargs)
        return None

    def _activity_call_sync(self, **kwargs):
        """
        Synchronous version of making a client call
        """
        #    def _activity_call(self, *args, **kwargs):
        required_args = _get_args_for_command(action_def)

        if missing_keys := missing_keys_in_dict(required_args, kwargs):
            err_msg = f"Call to {group_name}.{action_name} missing required keys {missing_keys}, skipping!"
            LOG.error(err_msg)
            raise ValueError(err_msg)

        if cmd := action_def.get("cmd"):
            if fstring := cmd.get("fstring"):
                request = fstring.format(**kwargs).encode("ascii")
                return client.send_raw(request)
        LOG.warning(f"Failed to make request for {group_name}.{action_name}")

    async def _activity_call_async(self, **kwargs):
        """
        Asynchronous version of making a client call is used when an event_loop
        is provided. Calling code knows whether they instantiated a synchronous
        or asynchronous client.
        """
        required_args = _get_command_args(action_def)

        if missing_keys := missing_keys_in_dict(required_args, kwargs):
            err_msg = f"Call to {group_name}.{action_name} missing required keys {missing_keys}, skipping!"
            LOG.error(err_msg)
            raise IllegalArgumentError(err_msg)

        if cmd := action_def.get("cmd"):
            if fstring := cmd.get("fstring"):
                request = fstring.format(**kwargs).encode("ascii")
                return await client.send_raw(request)
        LOG.warning(f"Failed to make request for {group_name}.{action_name}")

    if event_loop:
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
            LOG.warning(f"Command regex found BUT IGNORING! {named_regex}")

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

    # append details on all the command arguments
    if args := _get_args_for_command(action_def):
        args_docs = action_def.get("cmd", {}).get("docs", {})
        for arg in args:
            arg_description = args_docs.get(arg, "see manufacturer's protocol manual")
            doc += f"\n:param {arg}: {arg_description}"

    # append details of any response message for this action
    if v := _get_vars_for_message(action_def):
        doc += "\n:return: {"
        for var in v:
            doc += f"\n  {var}: ..., "
        doc += "\n}"

    # FIXME: may need type info from the overall api variables section
    return doc


def create_activity_group_class(
    client: DeviceClient,
    model_id: str,
    group_name: str,
    actions_model: dict,
    cls_bases=None,
    event_loop=None,
):
    # CamelCase the model and actions group to represent this dynamic class of action methods
    cls_name = camel_case(f"{model_id} {group_name}")

    if not cls_bases:
        cls_bases = (DynamicActions,)
    cls_props = {}

    # dynamically add methods (and associated documentation) for each action
    for action_name, action_def in actions_model["actions"].items():
        # handle yamlfmt/yamlfix rewriting of "on" and "off" as YAML keys into bools
        if type(action_name) == bool:
            if not action_name:
                action_name = "off"
            else:
                action_name = "on"

        method = _get_client_method(
            client, group_name, action_name, action_def, event_loop
        )

        print(f"{group_name}.{action_name}")
        # FIXME: danger will robinson...potential exploits (need to explore how to filter out)
        method.__name__ = action_name  # FIXME: what about __qualname__
        method.__doc__ = _generate_docs_for_action(action_name, action_def)

        cls_props[action_name] = method

    # return the new dynamic class that contains the above actions
    cls = type(cls_name, cls_bases, cls_props)
    return cls(model_id, actions_model["actions"])


class GroupActions:
    """ """

    def __init__(self, group: str, actions_def):
        self._group = group
        self._actions_def = actions_def

        self._validator = ActionArgsValidator()
        self._parser = ActionParser()

        # call superclass constructor (if any)

        for action, action_def in actions_def.items():
            if cmd := action_def.get("msg"):
                print(cmd)

    def make_method_call(self, method, *args, **kwargs):
        """
        Call the action on the remote device
        """
        validated_params = self._validate_params(method, *args, **kwargs)
        api_response = self.make_api_call(method, validated_Params)
        return self._parse_api_response(method, api_respons)

    def _validate_params(self, method, *args, **kwargs):
        """
        Validate that the required params for this method have been passed in
        """
        input_model = self.get_operation_model(method)["input"]
        return self._validator.validate(input_model, *args, **kwargs)

    def _parse_response(self, method, api_repsonse):
        output_model = self.get_operational_model(method)["output"]
        return self._parser.parse(output_model, api_response)

    def _get_operation_model(self, method):
        operation_models = self._model_def["operations"]
        if method not in operation_models:
            raise RuntimeError("Unknown operation: %s" % method)
        return operation_models[method]


class ModelInterface:
    """
    Dynamic class generation to represent a device model based on its API
    definition for RS232/IP communication.
    """

    def __init__(self, device):
        variable = "test"

        def _f(captured_variable=variable):
            print(captured_variable)

        # get the API model for the device
        api = device.config.get("api", {})
        for group, group_def in api.items():
            LOG.debug(f"Adding property for group {group}")
            property_name = group
            setattr(type(self), property_name, _f)

            # create class that handles all the actions for the API
            actions_def = group_def.get("actions", {})
            actions = GroupActions(group, actions_def)

            # set a property of this class that references the object containing all
            # the dynamic methods for each action
            setattr(type(self), property_name, _f)

            # FIXME: display help for the new class
            # help(cls)


# Process:
#  1. create mixin class
#  2. inject the mixin to the DeviceClient
def inject_client_activity_groups(model_id: str, client: DeviceClient, model_def: dict):
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
    print(library.supported_models())
    return

    supported_models = MODELS  # [ "mcintosh_mx160" ]
    for model_id in supported_models:
        model_def = DeviceModelLibrary.create().load_model(model_id)
        client = DeviceClient.create(model_def, url)
        # FIXME: the type of the returned DeviceClient should be the SPECIFIC model E.g. McIntoshMx160Client
        return inject_client_activity_groups(model_id, client, model_def)

    # FIXME: the above construct_dynamic_classes(model, url) needs to be in DeviceClient.create()
    client = DeviceClient.create(model_def, url)

    help(client)
    # client.source.get()
    # client.source.next()
    # client.source.set()
    # print(client.software.info())


if __name__ == "__main__":
    main()
22
