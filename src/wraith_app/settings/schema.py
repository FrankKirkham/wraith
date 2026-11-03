import logging
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

log = logging.getLogger(__name__)

class _Base(BaseModel):
    model_config = ConfigDict(extra="ignore")

class Visuals(_Base):
    show_hand_overlay: bool = True
    show_centre_line: bool = False

QUANTISATION_LEVELS = (1, 2, 3, 4, 5, 6)

class Quantisation(_Base):
    # 1 is full resolution; each level up halves the number of values. A level rather than a value count, so it 
    # survives switching modes like negative_eq_only
    level: Literal[1, 2, 3, 4, 5, 6] = 1

class Control(_Base):
    quantisation: Quantisation = Field(default_factory=Quantisation)

class VolumeSlider(Control):
    pass

class EqKnob(Control):
    negative_eq_only: bool = False # only cut, from the centre value down

class LowEqKnob(EqKnob):
    pass

class MidEqKnob(EqKnob):
    pass

class HighEqKnob(EqKnob):
    pass

class Controls(_Base):
    volume_slider: VolumeSlider = Field(default_factory=VolumeSlider)
    high_eq_knob: HighEqKnob = Field(default_factory=HighEqKnob)
    mid_eq_knob: MidEqKnob = Field(default_factory=MidEqKnob)
    low_eq_knob: LowEqKnob = Field(default_factory=LowEqKnob)


class Settings(_Base):
    visuals: Visuals = Field(default_factory=Visuals)
    controls: Controls = Field(default_factory=Controls)


def validate(data: dict) -> Settings:
    # Drop only the fields that fail validation so they fall back to their defaults, 
    # rather than rejecting the whole file
    data = dict(data)
    for _ in range(50):
        try:
            return Settings.model_validate(data)
        except ValidationError as exc:
            removed_any = False
            for error in exc.errors():
                loc = error["loc"]
                if _remove_path(data, loc):
                    removed_any = True
                    log.warning(
                        "Ignoring invalid setting %s (%s); using default",
                        ".".join(str(part) for part in loc),
                        error["msg"],
                    )
            if not removed_any:
                break

    log.warning("Could not repair settings; using defaults")
    return Settings()

def _remove_path(data: dict, loc: tuple) -> bool:
    if not loc:
        return False

    parent = data
    for key in loc[:-1]:
        if isinstance(parent, dict) and key in parent:
            parent = parent[key]
        elif isinstance(parent, list) and isinstance(key, int) and key < len(parent):
            parent = parent[key]
        else:
            return False

    last = loc[-1]
    if isinstance(parent, dict) and last in parent:
        del parent[last]
        return True
    if isinstance(parent, list) and isinstance(last, int) and last < len(parent):
        del parent[last]
        return True
    return False
