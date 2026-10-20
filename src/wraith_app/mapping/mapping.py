import mido
from typing import Tuple

from wraith_app.gestures.pose import Pose
from wraith_app.gestures.recognizer import GestureFrame, SideGesture
from wraith_app.vision.hand import ScreenSide

MIDI_MAX = 127

# Which half of the screen a hand is in decides the channel it controls -
# not whether it is the user's left or right hand
CHANNEL_FOR_SIDE = {
    ScreenSide.LEFT: 0,
    ScreenSide.RIGHT: 1,
}

# Each pinch drives its own CC; the attribute names its Pinch on Pinches
PINCH_CONTROLS = {
    Pose.PINCH_INDEX: ("index", 1),
    Pose.PINCH_MIDDLE: ("middle", 2),
    Pose.PINCH_RING: ("ring", 3),
    Pose.PINCH_PINKY: ("pinky", 4),
}

def map_gestures_to_midi(gesture_frame: GestureFrame) -> Tuple[mido.Message | None, mido.Message | None]:
    # One message per channel, in screen order (left half, right half). None
    # leaves that channel alone, so its controls hold their last value
    return (
        map_side(gesture_frame.side(ScreenSide.LEFT), ScreenSide.LEFT),
        map_side(gesture_frame.side(ScreenSide.RIGHT), ScreenSide.RIGHT),
    )

def map_side(gesture: SideGesture, side: ScreenSide) -> mido.Message | None:
    control = PINCH_CONTROLS.get(gesture.pose)
    if control is None or gesture.features is None:
        return None

    finger, cc_number = control
    pinch = getattr(gesture.features.pinches, finger)
    return mido.Message(
        "control_change",
        channel=CHANNEL_FOR_SIDE[side],
        control=cc_number,
        value=y_to_cc(pinch.point.y),
    )

def y_to_cc(y: float) -> int:
    # Top of the frame is MIDI_MAX
    height = 1.0 - y
    value = round(height * MIDI_MAX)
    return max(0, min(MIDI_MAX, value))
