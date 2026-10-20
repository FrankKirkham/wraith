# Measurements taken from one hand in one frame
#
# No memory between frames: anything that needs history (debounce, dropout,
# multi-frame gestures) belongs in the recognizer. Distances are relative to
# palm size so they don't change with distance from the camera; positions
# stay normalised to the frame

from __future__ import annotations # Stops incorrectly complaining about type annotations

import math
from dataclasses import dataclass
from wraith_app.vision.hand import Hand, HandLandmark, Landmark

# Floor for palm size, so a hand edge-on to the camera can't divide by zero
MIN_PALM_SIZE = 1e-6

@dataclass(frozen=True)
class Position2D:
    """2D Position."""
    x: float
    y: float

@dataclass(frozen=True)
class Pinch:
    """Thumb tip against one finger tip."""
    distance: float     # relative to palm size
    point: Position2D   # midpoint of the two tips, normalised [0, 1]

@dataclass(frozen=True)
class Pinches:
    """A pinch for each finger against the thumb."""
    index: Pinch
    middle: Pinch
    ring: Pinch
    pinky: Pinch

@dataclass(frozen=True)
class HandFeatures:
    pinches: Pinches
    wrist_pos: Position2D

    @classmethod
    def from_hand(cls, hand: Hand) -> HandFeatures:
        # Palm size is wrist to middle knuckle
        palm_size = max(distance(hand.wrist, hand.landmark(HandLandmark.MIDDLE_FINGER_MCP)), MIN_PALM_SIZE)
        thumb_tip = hand.landmark(HandLandmark.THUMB_TIP)

        def pinch_with(which: HandLandmark) -> Pinch:
            tip = hand.landmark(which)
            return Pinch(distance(thumb_tip, tip) / palm_size, midpoint(thumb_tip, tip))

        pinches = Pinches(
            index=pinch_with(HandLandmark.INDEX_FINGER_TIP),
            middle=pinch_with(HandLandmark.MIDDLE_FINGER_TIP),
            ring=pinch_with(HandLandmark.RING_FINGER_TIP),
            pinky=pinch_with(HandLandmark.PINKY_TIP),
        )

        wrist_pos = Position2D(hand.wrist.x, hand.wrist.y)

        return cls(pinches, wrist_pos)

def distance(a: Landmark, b: Landmark) -> float:
    # 2D only, z is too noisy
    return math.hypot(a.x - b.x, a.y - b.y)

def midpoint(a: Landmark, b: Landmark) -> Position2D:
    return Position2D((a.x + b.x) / 2, (a.y + b.y) / 2)
