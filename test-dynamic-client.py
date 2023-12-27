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
import pprint as pp
import re
from typing import List

import coloredlogs

from pyavcontrol import DeviceClient, DeviceModelLibrary
from pyavcontrol.core import camel_case, missing_keys_in_dict

LOG = logging.getLogger(__name__)
coloredlogs.install(level="DEBUG")

FSTRING_ARG_PATTERN = re.compile(
    r"\{(?P<arg_name>.+)[:.,]*\}"
)  # FIXME: also parse any format strings out


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
    group_name: str, action_name: str, action_def: dict, event_loop=None
):
    required_args = _get_required_args_for_command(action_def)

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
        required_args = _get_required_args_for_command(action_def)

        if missing_keys := missing_keys_in_dict(required_args, kwargs):
            err_msg = f"Call to {group_name}.{action_name} missing required keys {missing_keys}, skipping!"
            LOG.error(err_msg)
            raise IllegalArgumentError(err_msg)

        if cmd := action_def.get("cmd"):
            if fstring := cmd.get("fstring"):
                request = substitute_fstring_vars(fstring, kwargs)
                return self.send_raw(request)

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
                request = substitute_fstring_vars(fstring, kwargs)
                return await self.send_command(request)

    if event_loop:
        return _activity_call_async
    else:
        return _activity_call_sync


def _get_required_args_for_command(action_def: dict) -> List[str]:
    """
    Parse the command definition into an array of arguments for the action, with a dictionary
    describing additional type information about each argument.

    :return: list of arguments for a given command
    """
    args = []

    if cmd := action_def.get("cmd"):
        if regex := cmd.get("regex"):
            named_regex = extract_named_regex(regex)
            LOG.warning(f"Command regex found BUT IGNORING! {matches}")

        fstring = cmd.get("fstring")
        if args := _get_fstring_vars(fstring):
            # FIXME: embed all the cmd_patterns into this
            return args

    return args


def _get_fstring_vars(text: str) -> List[str]:
    """
    Parse out all the F-string style arguments from the given string
    """
    args = []

    # FIXME: remove any special format strings in the args???

    # extract args from the regexp pattern of parameters
    for m in re.finditer(FSTRING_ARG_PATTERN, text):
        args += [{"name": m.group(1)}]

    # get dictionary containing the parts of your text
    # info = re.match(retext, text).groupdict()

    return args


# FIXME: why do I need this func now?
def _parse_response_args(action_name: str, action_def: dict) -> List[str]:
    if msg := action_def.get("msg"):
        return extract_named_regex(msg).keys()
    return []


def _document_action(action_name: str, action_def: dict):
    doc = action_def.get("description")

    # append details on all the command arguments
    if args := _parse_args(action_name, action_def):
        for arg in args:
            arg_doc = arg.get("doc", "unknown")
            doc += f"\n:param {arg['name']}: {arg_doc}"

    # append details of any response message for this action
    if args := _parse_response_args(action_name, action_def):
        doc += "\n:return: {"
        for arg in args:
            arg_doc = arg.get("doc", "unknown")
            doc += f" {arg['name']}: {arg_doc}, "
        doc += "}\n"

    # FIXME: may need type info from the overall api variables section
    return doc


def create_activity_group_class(
    model_name: str,
    group_name: str,
    actions_model: dict,
    cls_bases=None,
    event_loop=None,
):
    # CamelCase the model and group to represent this class of methods
    cls_name = camel_case(f"{model_name} {group_name}")

    if not cls_bases:
        cls_bases = (DynamicActions,)
    cls_props = {}

    # dynamically add methods (and associated documentation) for each action
    for action_name, action_def in actions_model["actions"].items():
        method = _get_client_method(group_name, action_name, action_def, event_loop)
        method.__name__ = action_name
        method.__doc__ = _document_action(action_name, action_def)
        cls_props[action_name] = method

    # return the new dynamic class that represents this device's group of actions
    cls = type(cls_name, cls_bases, cls_props)
    return cls(model_name, actions_model["actions"])


class GroupActions:
    """ """

    def __init__(self, group: str, actions_def):
        self._group = group
        self._actions_def = actions

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
        operation_models = self.model_["operations"]
        if method not in operation_models:
            raise RuntimeError("Unknown operation: %s" % method)
        return operation_models[method]


class ModelInterface:
    """
    Dynamic class generation to represent a device model based on its API definition for
    RS232/IP communication.
    """

    def __init__(self, device):
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


if __name__ == "__main__":
    model = "mcintosh_mx160"

    model_def = DeviceModelLibrary.create().load_model(model)
    client = DeviceClient.create(
        model_def, args.url, serial_config_overrides={"baudrate": args.baud}
    )

    api = model_def.get("api", {})
    for group, group_def in api.items():
        LOG.debug(f"Adding property for group {group}")

        g = create_activity_group_class(model, group, group_def)
        g.min()
        # help(g)
        break
