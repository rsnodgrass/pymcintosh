"""Configuration and data structures around device models"""

import logging
from pprint import pprint

from ..const import CONFIG_DIR
from ..core import load_yaml_file

LOG = logging.getLogger(__name__)

RAW_CONFIG = None
MODELS_CONFIG = {}


class DeviceModels:
    _config = {}

    @classmethod
    def _load_config_old(cls, model="mx160"):
        # lazy load configuration on first call
        global RAW_CONFIG
        if not RAW_CONFIG:
            RAW_CONFIG = load_yaml_dir(f"{CONFIG_DIR}/models")
            pprint(RAW_CONFIG)

            for series, series_info in RAW_CONFIG.items():
                # the default config that applies to all models (can be overridden)
                default_config = series_info.get("default_config", {})
                default_config["series"] = series
                default_config["tested"] = False

                for model_config in series_info.get("models"):
                    model = model_config.get("model")

                    # detect accident duplicate models in the configuration
                    if model in MODELS_CONFIG:
                        name = model_config.get("name")
                        old_model_name = MODELS_CONFIG.get("name")
                        LOG.warning(
                            f"Duplicate model '{model}' defined in models/*.yaml ({old_model_name} -> {series}/{name})"
                        )

                    # merge any global settings from the model series into the model config
                    blended_config = {**default_config, **model_config}
                    MODELS_CONFIG[model] = blended_config

        return MODELS_CONFIG

    @classmethod
    def apply_import_config(model: str, config: dict, previously_loaded=[]):
        """
        Recursively apply model configuration from importing other models.
        """
        
        # FIXME: this could accidentally create loops...detect and abort!
        # load all the imported_models...and apply before copying over yaml
        combined_config = {}
        for imported_model in config.get('import_protocols', []):
            # FIXME: but multiple imports of the same base.yaml should be allowed
            # as long as there is not a loop!
            if imported_model in previously_loaded:
                LOG.error(f"Cyclical imports detected with {imported_model} for {model}; skipping!")
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

        merged_config = config | combined_config # FIXME: order of precedence?
        return merged_config
   
    def apply_imported_config(previous: dict, new: dict):
        return        

    @classmethod
    def get_config(cls, model: str) -> dict:
        model_file = f"{CONFIG_DIR}/models/{model}.yaml"
        config = load_yaml_file(model_file)
        return config 

    @classmethod
    def get_supported_models(cls) -> dict:
        """@return dictionary of all supported models and associated config"""
        return MODELS_CONFIG  # FIXME: consider copy.deepcopy(MODELS_CONFIG)
