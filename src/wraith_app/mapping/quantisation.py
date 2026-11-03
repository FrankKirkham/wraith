# Snaps a control's position to the values its quantisation level allows
from wraith_app.settings import Control, EqKnob

MIDI_MAX = 127
EQ_CENTRE = 64 # unity gain on an EQ knob

def volume_steps(level: int) -> int:
    # 128, 64, 32, 16, 8, 4
    return 128 >> (level - 1)

def eq_steps(level: int, negative_only: bool = False) -> int:
    if negative_only:
        # 65, 33, 17, 9, 5, 3, from 0 up to the centre
        return (64 >> (level - 1)) + 1
    if level == 1:
        return 128
    # 65, 33, 17, 9, 5: odd, so the centre is one of the values
    return (128 >> (level - 1)) + 1

def steps(control: Control) -> int:
    level = control.quantisation.level
    if isinstance(control, EqKnob):
        return eq_steps(level, control.negative_eq_only)
    return volume_steps(level)

def top(control: Control) -> int:
    # The value the highest step lands on. Full-range EQ uses 128 so the steps are evenly spaced and one of them is 
    # EQ_CENTRE; 128 itself becomes 127
    if isinstance(control, EqKnob):
        if control.negative_eq_only:
            return EQ_CENTRE
        if control.quantisation.level > 1:
            return 128
    return MIDI_MAX

def quantise(control: Control, position: float) -> int:
    # position runs 0 to 1 over the control's whole range
    position = max(0.0, min(1.0, position))
    count = steps(control)
    index = round(position * (count - 1))
    return min(MIDI_MAX, round(index * top(control) / (count - 1)))
