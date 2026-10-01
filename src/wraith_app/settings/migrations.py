# Schema version of settings.json, separate from the app version.
#
# Adding a migration: bump SETTINGS_VERSION, add a vN_to_vN+1 function that
# returns the converted dict, register it in MIGRATIONS, and update the
# models in schema.py. Old migrations are never edited.
from typing import Callable, Dict

SETTINGS_VERSION = 1

Migration = Callable[[dict], dict]

# version N -> function taking the raw dict at N and returning it at N+1
MIGRATIONS: Dict[int, Migration] = {}
