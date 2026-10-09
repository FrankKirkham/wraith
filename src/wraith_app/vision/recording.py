# Saving and loading recorded HandFrames as JSON, so later stages can be
# tested against real landmark data without a camera
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple

from wraith_app.vision.hand import Hand, HandFrame, Handedness, Landmark

FORMAT_VERSION = 1
# Landmarks are normalised to [0, 1], so 5 decimal places is well below detector noise
PRECISION = 5

@dataclass(frozen=True)
class RecordedFrame():
    # Seconds since the recording started
    timestamp: float
    hand_frame: HandFrame

def save_recording(path: Path, frames: Iterable[RecordedFrame]) -> None:
    data = {
        "version": FORMAT_VERSION,
        "frames": [frame_to_dict(frame) for frame in frames],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))

def load_recording(path: Path) -> Tuple[RecordedFrame, ...]:
    data = json.loads(path.read_text())
    if data.get("version") != FORMAT_VERSION:
        raise ValueError(
            f"{path} is recording format {data.get('version')}, expected {FORMAT_VERSION}"
        )
    return tuple(frame_from_dict(frame) for frame in data["frames"])

def frame_to_dict(frame: RecordedFrame) -> dict:
    return {
        "t": round(frame.timestamp, 4),
        "hands": [
            {
                "handedness": hand.handedness.value,
                "score": round(hand.handedness_score, 4),
                "landmarks": [
                    [round(lm.x, PRECISION), round(lm.y, PRECISION), round(lm.z, PRECISION)]
                    for lm in hand.landmarks
                ],
            }
            for hand in frame.hand_frame
        ],
    }

def frame_from_dict(data: dict) -> RecordedFrame:
    hands = tuple(
        Hand(
            handedness=Handedness(hand["handedness"]),
            landmarks=tuple(Landmark(x=x, y=y, z=z) for x, y, z in hand["landmarks"]),
            handedness_score=hand["score"],
        )
        for hand in data["hands"]
    )
    return RecordedFrame(timestamp=data["t"], hand_frame=HandFrame(hands=hands))
