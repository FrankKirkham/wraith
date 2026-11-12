import mido
from typing import Tuple

from wraith_app.gestures.pose import Pose
from wraith_app.gestures.recognizer import GestureFrame, SideGesture
from wraith_app.mapping.quantisation import quantise
from wraith_app.settings import Controls
from wraith_app.vision.hand import ScreenSide

# Which half of the screen a hand is on decides the channel it controls, NOT whether it is the left or right hand
CHANNEL_FOR_SIDE = {
    ScreenSide.LEFT: 0,
    ScreenSide.RIGHT: 1,
}

# Each pinch drives its own CC: (finger on Pinches, CC number, control on Controls)
PINCH_CONTROLS = {
    Pose.PINCH_INDEX: ("index", 1, "volume_slider"),
    Pose.PINCH_MIDDLE: ("middle", 2, "low_eq_knob"),
    Pose.PINCH_RING: ("ring", 3, "mid_eq_knob"),
    Pose.PINCH_PINKY: ("pinky", 4, "high_eq_knob"),
}

def map_gestures_to_midi(gesture_frame: GestureFrame, 
                         controls: Controls) -> Tuple[mido.Message | None, mido.Message | None]:
    # One message per channel, in screen order (left half, right half). None
    # leaves that channel alone, so its controls hold their last value
    return (
        map_side(gesture_frame.side(ScreenSide.LEFT), ScreenSide.LEFT, controls),
        map_side(gesture_frame.side(ScreenSide.RIGHT), ScreenSide.RIGHT, controls),
    )

def map_side(gesture: SideGesture, side: ScreenSide, controls: Controls) -> mido.Message | None:
    pinch_control = PINCH_CONTROLS.get(gesture.pose)
    if pinch_control is None or gesture.features is None:
        return None

    finger, cc_number, control_name = pinch_control
    pinch = getattr(gesture.features.pinches, finger)
    height = 1.0 - pinch.point.y # 0 at the bottom of the frame, 1 at the top
    position = active_position(height, controls.active_height)
    return mido.Message(
        "control_change",
        channel=CHANNEL_FOR_SIDE[side],
        control=cc_number,
        value=quantise(getattr(controls, control_name), position),
    )

def active_position(height: float, active_height: int) -> float:
    # Returns 0 at the bottom of the active height and 1 at the top. Pinches above it give more than 1 and below it
    # less than 0, quantise deals with this by clamping it to 0 or 1, so we don't need to worry about it here
    active = active_height / 100
    margin = (1.0 - active) / 2
    return (height - margin) / active
