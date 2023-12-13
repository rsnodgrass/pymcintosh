"""Configuration and data structures around device models"""

import logging
from pprint import pprint

from ..const import CONFIG_DIR
from ..core import load_yaml_file

LOG = logging.getLogger(__name__)


class DeviceModel:
    def __init__(self, model_id: str):
        self._model_id = model_id
        self._config = DeviceModel.get_config(model_id)

        if not self._config:
            LOG.error(
                f"No such model {model_id} found, please check the list of supported models."
            )
            raise NotImplementedError()

    @property
    def id(self) -> str:
        return self._model_id

    @property
    def config(self) -> dict:
        """
        :return the complete config associated with this device
        """
        return self._config

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

    def apply_imported_config(previous: dict, new: dict):
        return

    @classmethod
    def get_config(cls, model_id: str) -> dict:
        model_file = f"{CONFIG_DIR}/models/{model_id}.yaml"
        config = load_yaml_file(model_file)
        # pprint(config)

        return config

    @classmethod
    def get_supported_models(cls) -> dict:
        """@return dictionary of all supported models and associated config"""
        return MODELS_CONFIG  # FIXME: consider copy.deepcopy(MODELS_CONFIG)
