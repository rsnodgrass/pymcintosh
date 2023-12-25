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

import coloredlogs

from pyavcontrol import DeviceController, DeviceModel

LOG = logging.getLogger(__name__)
coloredlogs.install(level="DEBUG")


class ActionArgsValidator:
    def __init__(self):
        return


class ActionParser:
    def __init__(self):
        return


def create_actions(model, cls_name="MyAction", cls_bases=None):
    if not cls_bases:
        cls_bases = (Model_client,)
    cls_props = {}

    for operation_name, operation_model in model["operations"].items():
        method = _get_client_method(operation_model)
        method.__name__ = str(operation_name)
        method.__doc__ = _get_docstring(operation_model)
        cls_props[operation_name] = method

    cls = type(cls_name, cls_bases, cls_props)
    return cls(model)


class DynamicDeviceActions:
    def __init__(self, model_name, actions_def):
        self._model_name = model_name
        self._actions_def = actions_def


def _get_client_method(operation_name):
    def _api_call(self, *args, **kwargs):
        return self.make_modeled_api_call(operation_name, *args, **kwargs)

    return _api_call


def camel_case(text: str):
    """
    Convert string into a CamelCase format without any spaces or special characters
    """
    return re.sub("[^0-9a-zA-Z]+", "", re.sub("[-_.]+", " ", text).title())


def _parse_args(action_name, action_def):
    """
    Parse the definition into an array of arguments for the action, with a dictionary
    describing additional type information about each argument.
    """
    args = []
    if cmd := action_def.get("cmd"):
        pattern = re.compile(r"\{(?P<arg_name>.+)\}")
        # extract args from the regexp pattern of parameters
        for m in re.finditer(pattern, cmd):
            args += [{"name": m.group(1)}]
    return args


def _parse_response_args(action_name, action_def):
    args = []
    if msg := action_def.get("msg"):

        pattern = re.compile(r"\(\?P\<(?P<name>.+)\>(?P<regexp>.+)\)")

        # extract args from the regexp pattern of parameters
        for m in re.finditer(pattern, msg):
            args += {m.group(1): {pattern: m.group(2)}}
    return args


def _document_action(action_name, action_def):
    doc = action_def.get("description")

    # append details on all the command arguments
    if args := _parse_args(action_name, action_def):
        for arg in args:
            arg_doc = arg.get("doc", "unknown")
            doc += f"\n:param {arg['name']}: {arg_doc}"

    # FIXME: may need type info from the overall api variables section
    return doc


def create_activity_group_class(model_name, group_name, actions_model, cls_bases=None):
    # CamelCase the model and group to represent this class of methods
    model_name = camel_case(model_name)
    group_name = camel_case(group_name)
    cls_name = model_name + group_name

    if not cls_bases:
        cls_bases = (DynamicDeviceActions,)
    cls_props = {}

    # dynamically add methods (and associated documentation) for each action
    for action_name, action_def in actions_model["actions"].items():
        method = _get_client_method(action_name)
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
        self._parer = ActionParser()

        # call superclass constructor (if any)

        for action, action_def in actions_def.items():
            action_id = f"{group}.{action}"

            if cmd := action_def.get("msg"):
                print(cmd)

    def make_method_call(self, method, *args, **kwargs):
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

    # raise RuntimeError


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
        pp.pprint(api)

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
    device = DeviceModel(model)

    api = device.config.get("api", {})
    for group, group_def in api.items():
        LOG.debug(f"Adding property for group {group}")

        g = create_activity_group_class(model, group, group_def)
        help(g)
        break
