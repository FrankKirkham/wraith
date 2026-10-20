# The label for what the hand is doing right now.

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict

from wraith_app.gestures.features import HandFeatures, Pinches

class Pose(Enum):
    UNKNOWN = auto() # no recognised pose, or no hand
    PINCH_INDEX = auto()
    PINCH_MIDDLE = auto()
    PINCH_RING = auto()
    PINCH_PINKY = auto()

@dataclass(frozen=True)
class PinchThreshold:
    finger: str # attribute on Pinches
    enter: float # in palm sizes
    exit: float

# TODO : values need testing and tweaking
PINCH_THRESHOLDS: Dict[Pose, PinchThreshold] = {
    Pose.PINCH_INDEX: PinchThreshold("index", enter=0.25, exit=0.35),
    Pose.PINCH_MIDDLE: PinchThreshold("middle", enter=0.30, exit=0.40),
    Pose.PINCH_RING: PinchThreshold("ring", enter=0.30, exit=0.40),
    Pose.PINCH_PINKY: PinchThreshold("pinky", enter=0.35, exit=0.45),
}

# TODO : Currently only working for pinch
def classify(features: HandFeatures, previous: Pose) -> Pose:
    # Stricter threshold to enter a pinch than to stay in it, so the pose doesn't flicker 
    # on a boundary. A held pinch wins over a new one; if several fingers enter at once, 
    # the closest to the thumb wins
    held = PINCH_THRESHOLDS.get(previous)
    if held is not None and pinch_distance(features.pinches, held) < held.exit:
        return previous

    entered = {
        pose: pinch_distance(features.pinches, threshold)
        for pose, threshold in PINCH_THRESHOLDS.items()
        if pinch_distance(features.pinches, threshold) < threshold.enter
    }
    if not entered:
        return Pose.UNKNOWN
    return min(entered, key=entered.get)

def pinch_distance(pinches: Pinches, threshold: PinchThreshold) -> float:
    return getattr(pinches, threshold.finger).distance
