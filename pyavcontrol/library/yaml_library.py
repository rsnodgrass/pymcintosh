"""
Configuration and data structures around device models
"""
import logging
import os
from abc import ABC, abstractmethod
from fnmatch import fnmatch
from typing import List, Set

import yaml

from ..const import DEFAULT_MODEL_LIBRARIES
from .validate import DeviceModel

LOG = logging.getLogger(__name__)


def _load_yaml_file(path: str) -> dict | None:
    try:
        if os.path.isfile(path):
            with open(path, "r") as stream:
                return yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        LOG.error(f"Failed reading YAML {path}: {exc}")
        return None


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
        self._supported_models = set()

    def load_model(self, model_id: str) -> dict | None:
        # FIXME: ensure name does not have any /
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

    def supported_models(self) -> Set[str]:
        if self._supported_models:
            return self._supported_models

        supported_models = set()
        for path in self._dirs:
            for r, d, f in os.walk(path):
                if fnmatch(f, "*.yaml"):
                    print(os.path.join(r, f))
                    name = os.path.join(r, f)

            model_file = f"{dir}/{name}.yaml"
            y = _load_yaml_file(model_file)

        # FIXME: work!!
        self._supported_models = supported_models
        return self._supported_models


class DeviceModelLibraryAsync(DeviceModelLibrary, ABC):
    """
    Asynchronous implementation of DeviceModelLibrary
    """

    def __init__(self, library_dirs: List[str], event_loop):
        self._loop = event_loop
        self._dirs = library_dirs
        self._supported_models = set()

        # For simplicity in initial implementation, skipped writing the
        # asynchronous library and use the sync version for now. Especially
        # since loading model files should be a rare occurrence.
        #
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


class DeviceModelOld:
    @classmethod
    def apply_import_config(model: str, config: dict, previously_loaded=[]):
        """
        Recursively apply model configuration from importing other models.
        """

        # FIXME: this could accidentally create loops...detect and abort!
        # load all the imported_models...and apply before copying over yaml
        combined_config = {}
        for imported_model in config.get("import_protocols", []):
            # FIXME: but multiple imports of the same base.yaml should be allowed
            # as long as there is not a loop!
            if imported_model in previously_loaded:
                LOG.error(
                    f"Cyclical imports detected with {imported_model} for {model}; skipping!"
                )
                continue

            imported = get_config(imported_model)
            if not imported:
                LOG.error(f"Failed to import {imported_model} for {model}; skipping!")
                continue

            # FIXME: since it is a deeply nested structure, we need to probably
            # iterate through and modify to avoid blowing away complex nested
            # dictionaries (or at least patch the final version with just the nested
            # dicts).
            combined_config = combined_config | imported

        # FIXME: process all deletes for the outer layer before merging!!

        merged_config = config | combined_config  # FIXME: order of precedence?
        return merged_config
