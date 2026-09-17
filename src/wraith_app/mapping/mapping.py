import mido
from typing import Tuple

MIDI_MAX = 127
MIDI_CHANNEL = 0
MIDI_CC_NUMBER = 1 # temporary choice for now

def map_hands_to_midi(hands) -> Tuple[mido.Message | None, mido.Message | None]:
    # Currently just takes the wrist height of the first hand and converts
    # this into a cc value used for volume
    # Will later be changed to detect and use guestures to decide messages
    wrist = hands.hand_landmarks[0][0]
    cc_value = wrist_y_to_cc(wrist.y)

    return (mido.Message(
        "control_change",
        channel=MIDI_CHANNEL,
        control=MIDI_CC_NUMBER,
        value=cc_value
    ), None)

def wrist_y_to_cc(wrist_y):
    height = 1.0 - wrist_y
    value = round(height * MIDI_MAX)
    return max(0, min(MIDI_MAX, value))