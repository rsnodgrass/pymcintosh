"""Handle all configuration and data structures around device models"""

import logging
from pprint import pprint

from ..const import CONFIG_DIR
from ..core import load_yaml_dir

LOG = logging.getLogger(__name__)

RAW_CONFIG = None
MODELS_CONFIG = {}


def load_model_config():
    # lazy load configuration on first call
    global RAW_CONFIG
    if not RAW_CONFIG:
        RAW_CONFIG = load_yaml_dir(f"{CONFIG_DIR}/models")
        pprint(RAW_CONFIG)

        for series, config in RAW_CONFIG.items():
            # the default config that applies to all models (can be overridden)
            default_config = config.get("default_config", {})
            default_config["tested"] = False

            for model in config.models:
                # detect accident duplicate models in the configuration
                if model in MODELS_CONFIG:
                    name = config.get("name")
                    old_model_name = MODELS_CONFIG.get("name")
                    LOG.warning(
                        f"Duplicate model '{model}' defined in models/*.yaml ({old_model_name} -> {name})"
                    )

                # merge any global settings from the model series into the model config
                blended_config = {**default_config, **config}
                MODELS_CONFIG[model] = blended_config
    return MODELS_CONFIG


def get_model_config(model: str) -> dict:
    model_config = load_model_config()
    return model_config.get(model)
