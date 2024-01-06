"""
This includes all models to ensure that Sphinx documentation picks up all the
dynamically created classes.

THIS SHOULD NOT BE INCLUDED IN PRODUCTION CODE, it is specifically to force
documentation to be generated.

FIXME: We may want to move this to tools/ or docs/
"""
from . import DeviceModel, DeviceModelLibrary

MODELS = [
    "hdfury_vrroom",
    "trinnov_altitude32",
    "lyngdorf_cd2",
    "mcintosh_mx160",
    "xantech_mx88_audio",
    "lyngdorf_tdai3400",
]

for model in MODELS:
    model_def = DeviceModelLibrary.create().load_model(model)
