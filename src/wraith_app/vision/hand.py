# Classes / Data Types for detected hands
#
# Nothing in here knows about MediaPipe (or OpenCV): vision.py converts the
# raw detector output into these, and every later stage of the pipeline
# (gestures, mapping, ui) works with these instead

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Iterator, Tuple

class Handedness(Enum):
    LEFT = "Left"
    RIGHT = "Right"

class HandLandmark(IntEnum):
    # Index of each landmark within a hand's 21-point list, in the order
    # the hand landmarker returns them.
    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_FINGER_MCP = 5
    INDEX_FINGER_PIP = 6
    INDEX_FINGER_DIP = 7
    INDEX_FINGER_TIP = 8
    MIDDLE_FINGER_MCP = 9
    MIDDLE_FINGER_PIP = 10
    MIDDLE_FINGER_DIP = 11
    MIDDLE_FINGER_TIP = 12
    RING_FINGER_MCP = 13
    RING_FINGER_PIP = 14
    RING_FINGER_DIP = 15
    RING_FINGER_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20

LANDMARK_COUNT = len(HandLandmark)

@dataclass(frozen=True)
class Landmark():
    # A single joint. x and y are normalised to [0, 1] across the frame
    # (x from the left edge, y from the top edge), z is depth relative to
    # the wrist, in roughly the same scale as x, and is negative towards
    # the camera.
    x: float
    y: float
    z: float

@dataclass(frozen=True)
class Hand():
    handedness: Handedness
    landmarks: Tuple[Landmark, ...]
    # Detector confidence in the handedness label, in [0, 1]
    handedness_score: float

    def landmark(self, which: HandLandmark) -> Landmark:
        return self.landmarks[which]

    @property
    def wrist(self) -> Landmark:
        return self.landmark(HandLandmark.WRIST)

    @property
    def is_left(self) -> bool:
        return self.handedness is Handedness.LEFT

    @property
    def is_right(self) -> bool:
        return self.handedness is Handedness.RIGHT

@dataclass(frozen=True)
class HandFrame():
    # The hands found in one camera frame - empty when nothing was detected.
    hands: Tuple[Hand, ...] = ()

    @property
    def left(self) -> Hand | None:
        # First left hand, or None. The detector is capped at two hands but
        # can still label both the same, so take the first match either way
        return next((hand for hand in self.hands if hand.is_left), None)

    @property
    def right(self) -> Hand | None:
        return next((hand for hand in self.hands if hand.is_right), None)

    def __iter__(self) -> Iterator[Hand]:
        return iter(self.hands)

    def __len__(self) -> int:
        return len(self.hands)

    def __bool__(self) -> bool:
        return bool(self.hands)
