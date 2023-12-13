"""Configuration and data structures around device models"""

import logging
from pprint import pprint

from ..const import CONFIG_DIR
from ..core import load_yaml_dir

LOG = logging.getLogger(__name__)

RAW_CONFIG = None
MODELS_CONFIG = {}


class DeviceModels:
    _config = {}

    @classmethod
    def _load_config(cls):
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
    def get_config(cls, model: str) -> dict:
        model_config = cls._load_config()
        return model_config.get(model)

    @classmethod
    def get_supported_models(cls) -> dict:
        """@return dictionary of all supported models and associated config"""
        return MODELS_CONFIG  # FIXME: consider copy.deepcopy(MODELS_CONFIG)
