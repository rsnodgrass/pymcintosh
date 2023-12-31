"""
Configuration and data structures around device models
"""
import logging
import os
import pathlib
from abc import ABC, abstractmethod
from typing import List, Set

import yaml

from ..const import DEFAULT_MODEL_LIBRARIES
from .validate import DeviceModel

LOG = logging.getLogger(__name__)


def _load_yaml_file(path: str) -> dict:
    try:
        if os.path.isfile(path):
            with open(path, "r") as stream:
                return yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        LOG.error(f"Failed reading YAML {path}: {exc}")
        return {}


class DeviceModelLibrary(ABC):
    @abstractmethod
    def load_model(self, name: str) -> dict:
        """
        :param name: model name or a complete path to a file
        """
        raise NotImplementedError("Subclasses must implement!")

    @abstractmethod
    def supported_models(self) -> Set[str]:
        """
        :return: all model names supported by this library
        """
        raise NotImplementedError("Subclasses must implement!")

    #        # FIXME: read all yaml files
    #        supported_models = {}
    #        supported_models["mcintosh_mx160"] = {
    #            "manufacturer": "McIntosh",
    #            "model": "MX160",
    #            "tested": True,
    #        }
    #        return supported_models

    @staticmethod
    def create(library_dirs=DEFAULT_MODEL_LIBRARIES, event_loop=None):
        """
        Create an DeviceModelLibrary object representing all the complete
        library for resolving models and includes.

        If an event_loop argument is passed in this will return the
        asynchronous implementation. By default the synchronous interface
        is returned.

        :param library_dirs: paths used to resolve model names and includes (default=pyavcontrol's library)
        :param event_loop: to get an interface that can be used asynchronously, pass in an event loop

        :return an instance of DeviceLibraryModel
        """
        if event_loop:
            return DeviceModelLibraryAsync(library_dirs, event_loop)
        else:
            return DeviceModelLibrarySync(library_dirs)


class DeviceModelLibrarySync(DeviceModelLibrary, ABC):
    """
    Synchronous implementation of DeviceModelLibrary
    """

    def __init__(self, library_dirs: List[str]):
        self._dirs = library_dirs
        self._supported_models = frozenset()

    def load_model(self, model_id: str) -> dict | None:
        if "/" in model_id:
            LOG.error(f"Invalid model '{model_id}': cannot contain / in identifier")

        model = None
        for path in self._dirs:
            model_file = f"{path}/{model_id}.yaml"
            model = _load_yaml_file(model_file)
            if model:
                break

        if not model:
            LOG.warning(f"Could not find model '{model_id}' in the library")
            return None

        if not DeviceModel.validate_model_definition(model):
            LOG.warning(f"Error in model {model_id} definition, returning anyway")

        return model

    def supported_models(self) -> frozenset[str]:
        if self._supported_models:
            return self._supported_models

        # build and cache the list of supported models based all the
        # yaml device definition files that are included in the library
        supported_models = {}
        for path in self._dirs:
            for root, dirs, filenames in os.walk(path):
                for fn in filenames:
                    if fn.endswith(".yaml"):
                        model_file = os.path.join(root, fn)
                        name = pathlib.Path(model_file).stem
                        supported_models[name] = model_file

        self._supported_models = frozenset(supported_models.keys())  # immutable
        return self._supported_models


class DeviceModelLibraryAsync(DeviceModelLibrary, ABC):
    """
    Asynchronous implementation of DeviceModelLibrary

    NOTE: For simplicity in initial implementation, skipped writing the
    asynchronous library and use the sync version for now. Especially
    since loading all the model files should be a rare occurrence).
    """

    def __init__(self, library_dirs: List[str], event_loop):
        self._loop = event_loop
        self._dirs = library_dirs
        self._supported_models = set()

        # FUTURE: consider implementing async method
        self._sync = DeviceModelLibrarySync(library_dirs)

    async def load_model(self, name: str) -> dict:
        result = await self._loop.run_in_executor(
            None, self._sync.load_model, self, name
        )
        return result

    async def supported_models(self) -> Set[str]:
        result = await self._loop.run_in_executor(
            None, self._sync.supported_models, self
        )
        return result
