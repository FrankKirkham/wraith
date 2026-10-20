# Turns a stream of HandFrames into GestureFrames
#
# Holds all memory between frames: debounce, dropout grace and multi-frame detectors. 
# One SideTracker per half of the screen, so each side's pose and features follow 
# whichever hand controls that side

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Tuple

from wraith_app.gestures.features import HandFeatures
from wraith_app.gestures.pose import Pose, classify
from wraith_app.vision.hand import Hand, HandFrame, ScreenSide

HOLD_TIME = 0.08 # seconds a new pose must hold before it's reported
DROPOUT_GRACE = 0.2 # seconds a lost hand keeps its state

class GestureKind(Enum):
    # Discrete things that happen over several frames
    OPENED = auto()
    CLOSED = auto()

@dataclass(frozen=True)
class GestureEvent:
    """One discrete gesture firing."""
    kind: GestureKind
    side: ScreenSide
    timestamp: float # seconds

@dataclass(frozen=True)
class SideGesture:
    """The current state of one half of the screen."""
    pose: Pose = Pose.UNKNOWN
    features: HandFeatures | None = None # None when no hand on that side

@dataclass(frozen=True)
class GestureFrame:
    """Everything the gesture layer outputs for one frame."""
    sides: Dict[ScreenSide, SideGesture] = field(default_factory=dict)
    events: Tuple[GestureEvent, ...] = ()

    def side(self, side: ScreenSide) -> SideGesture:
        return self.sides.get(side, SideGesture())

def controlling_hand(hand_frame: HandFrame, side: ScreenSide) -> Hand | None:
    # Both hands can sit in the same half of the frame, so one has to win: take the 
    # outermost, i.e. the one nearest that side's edge of the screen. 
    hands = hand_frame.hands_on(side)
    if not hands:
        return None

    if side is ScreenSide.LEFT:
        return min(hands, key=lambda hand: hand.wrist.x)
    else:
        return max(hands, key=lambda hand: hand.wrist.x)

class SideTracker:
    """All memory for one half of the screen between frames."""

    def __init__(self, side: ScreenSide):
        self.side = side
        self.detectors: List = [] # multi-frame detectors, none yet
        self.reset()

    def reset(self) -> None:
        self.current = SideGesture() # last reported state
        self.candidate = Pose.UNKNOWN # raw pose waiting to be confirmed
        self.candidate_since = 0.0
        self.last_seen: float | None = None

    def update(self, t: float, hand: Hand | None) -> Tuple[SideGesture, List[GestureEvent]]:
        if hand is None:
            # Brief detector dropouts keep the last state so controls don't jump
            if self.last_seen is None or t - self.last_seen > DROPOUT_GRACE:
                self.reset()
            return self.current, []

        self.last_seen = t
        features = HandFeatures.from_hand(hand)

        # Hysteresis runs on the raw pose, so it's fed the last raw result
        raw = classify(features, self.candidate)
        if raw is not self.candidate:
            self.candidate = raw
            self.candidate_since = t

        # A new pose is only reported once it has held for HOLD_TIME
        pose = self.current.pose
        if self.candidate is not pose and t - self.candidate_since >= HOLD_TIME:
            pose = self.candidate

        # Features are always fresh, even while a pose change is pending
        self.current = SideGesture(pose, features)

        events: List[GestureEvent] = []
        for detector in self.detectors:
            events.extend(detector.update(t, self.current))
        return self.current, events

class GestureRecognizer:
    """The single object Pipeline talks to."""

    def __init__(self):
        self.trackers: Dict[ScreenSide, SideTracker] = {side: SideTracker(side) for side in ScreenSide}

    def update(self, t: float, hand_frame: HandFrame) -> GestureFrame:
        # Call every frame, including ones with no hands, so dropout timing works
        sides: Dict[ScreenSide, SideGesture] = {}
        events: List[GestureEvent] = []
        for side, tracker in self.trackers.items():
            sides[side], side_events = tracker.update(t, controlling_hand(hand_frame, side))
            events.extend(side_events)
        return GestureFrame(sides, tuple(events))
