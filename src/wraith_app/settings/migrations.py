# Schema version of settings.json, separate from the app version.
#
# Adding a migration: bump SETTINGS_VERSION, add a vN_to_vN+1 function that
# returns the converted dict, register it in MIGRATIONS, and update the
# models in schema.py. Old migrations are never edited.
from typing import Callable, Dict

SETTINGS_VERSION = 2

Migration = Callable[[dict], dict]

def v1_to_v2(data: dict) -> dict:
    # quantisation went from a step count (128, 64 ... 4) to {"level": 1-6}
    levels = {128: 1, 64: 2, 32: 3, 16: 4, 8: 5, 4: 6}
    controls = data.get("controls")
    if not isinstance(controls, dict):
        return data
    for control in controls.values():
        if not isinstance(control, dict) or "quantisation" not in control:
            continue
        steps = control["quantisation"]
        if steps in levels and not isinstance(steps, bool):
            control["quantisation"] = {"level": levels[steps]}
        else:
            del control["quantisation"] # falls back to the default
    return data

# version N -> function taking the raw dict at N and returning it at N+1
MIGRATIONS: Dict[int, Migration] = {
    1: v1_to_v2,
}
