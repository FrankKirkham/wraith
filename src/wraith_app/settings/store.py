import json
import logging
import os
import shutil
from pathlib import Path

from platformdirs import user_config_dir

from wraith_app.settings.migrations import MIGRATIONS, SETTINGS_VERSION
from wraith_app.settings.schema import Settings, validate

log = logging.getLogger(__name__)

APP_NAME = "Wraith"
SETTINGS_PATH = Path(user_config_dir(APP_NAME)) / "settings.json"

VERSION_KEY = "settings_version"

# Set when the file came from a newer app, so save() never overwrites it
_read_only = False


def is_read_only() -> bool:
    return _read_only


def load(path: Path = SETTINGS_PATH) -> Settings:
    global _read_only
    _read_only = False

    if not path.exists():
        return Settings()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("top level is not an object")
    except (ValueError, OSError) as exc:
        corrupt_path = path.with_name("settings.corrupt")
        log.warning("Settings file %s is unreadable (%s); copying to %s and using defaults",
                    path, exc, corrupt_path)
        try:
            shutil.copyfile(path, corrupt_path)
        except OSError as copy_exc:
            log.warning("Could not copy corrupt settings: %s", copy_exc)
        return Settings()

    file_version = _file_version(data)

    if file_version > SETTINGS_VERSION:
        log.warning("Settings file is version %d but this app knows version %d; "
                    "loading read-only", file_version, SETTINGS_VERSION)
        _read_only = True
        return validate(data)

    if file_version < SETTINGS_VERSION:
        backup_path = path.with_name(f"settings.v{file_version}.bak")
        log.info("Migrating settings from version %d to %d (backup at %s)",
                 file_version, SETTINGS_VERSION, backup_path)
        shutil.copyfile(path, backup_path)
        data = _migrate(data, file_version)
        settings = validate(data)
        save(settings, path)
        return settings

    return validate(data)


def save(settings: Settings, path: Path = SETTINGS_PATH) -> None:
    if _read_only:
        log.warning("Settings are read-only (file from a newer app); not saving")
        return

    path.parent.mkdir(parents=True, exist_ok=True)

    data = {VERSION_KEY: SETTINGS_VERSION, **settings.model_dump()}
    tmp_path = path.with_name("settings.tmp")
    tmp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp_path, path)


def _file_version(data: dict) -> int:
    # Files from before versioning have no key, so count as version 1
    version = data.get(VERSION_KEY, 1)
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        log.warning("Ignoring invalid settings_version %r; treating as 1", version)
        return 1
    return version


def _migrate(data: dict, from_version: int) -> dict:
    for version in range(from_version, SETTINGS_VERSION):
        migrate = MIGRATIONS.get(version)
        if migrate is None:
            raise RuntimeError(f"No migration from settings version {version} to {version + 1}")
        data = migrate(data)
        data[VERSION_KEY] = version + 1
    return data
