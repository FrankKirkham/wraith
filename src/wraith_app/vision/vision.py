# The only module that touches MediaPipe: it turns raw detector output into
# the plain Hand/HandFrame types from hand.py before anything else sees it.
import urllib.request
from pathlib import Path
from mediapipe.tasks.python import vision, BaseOptions
import mediapipe as mp
import cv2
import time

from wraith_app.vision.hand import Hand, HandFrame, Handedness, Landmark

#### Constants ####
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/latest/hand_landmarker.task"
)
# This file is in src/wraith_app/vision so need to go up three to the repo
# root, then into the models/ dir
MODEL_PATH = Path(__file__).resolve().parents[3] / "models" / "hand_landmarker.task"

HAND_CONNECTIONS = vision.HandLandmarksConnections.HAND_CONNECTIONS

## Drawing styles (BGR, because of OpenCV)
# 'Bones' / Lines
CONNECTION_COLOR = (0, 255, 0) # green bones between joints
CONNECTION_THICKNESS = 2
# 'Joints' / Points
LANDMARK_COLOR = (0, 0, 255) # red dots on joints
LANDMARK_RADIUS = 4

class HandTracker():
    landmarker = None
    start_time = None

    def __init__(self, model_path) -> None:
        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)
        self.start_time = time.monotonic()

    def detect(self, frame) -> HandFrame:
        # Open cv gives BGR, MediaPipe works with RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        # Mediapipe video requires a timestamp
        timestamp_ms = int((time.monotonic() - self.start_time) * 1000)
        # Run the detection and classificiation
        result = self.landmarker.detect_for_video(mp_image, timestamp_ms)

        return to_hand_frame(result)

    def close(self):
        if self.landmarker is not None:
            self.landmarker.close()


def to_hand_frame(result) -> HandFrame:
    # Convert a MediaPipe HandLandmarkerResult into our own types.
    hands = []

    for landmarks, handedness in zip(result.hand_landmarks, result.handedness):
        category = handedness[0]
        hands.append(Hand(
            handedness=to_handedness(category.category_name),
            landmarks=tuple(
                Landmark(x=lm.x, y=lm.y, z=lm.z) for lm in landmarks
            ),
            handedness_score=category.score,
        ))

    return HandFrame(hands=tuple(hands))

def to_handedness(category_name: str) -> Handedness:
    # The frame is mirrored before detection, so MediaPipe's label is the
    # opposite of the hand the user is actually holding up.
    return Handedness.RIGHT if category_name == "Left" else Handedness.LEFT

def ensure_model() -> Path:
    if not MODEL_PATH.exists():
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading hand landmarker model to {MODEL_PATH} ...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    return MODEL_PATH

def open_camera(max_index=5):
    # 0 might not be the correct camera index, so try all up to max_index
    for index in range(max_index + 1):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            print(f"Opened camera at index {index}")
            return cap
        cap.release()

    raise SystemExit(f"Could not open any camera (tried indices 0-{max_index})")

def draw_hands(frame, hand_frame: HandFrame):
    height, width = frame.shape[:2]

    for hand in hand_frame:
        # Convert normalised ([0, 1]) coords to pixel points
        points = [(int(lm.x * width), int(lm.y * height)) for lm in hand.landmarks]

        # Draw the lines then the points on top
        for connection in HAND_CONNECTIONS:
            cv2.line(
                frame,
                points[connection.start],
                points[connection.end],
                CONNECTION_COLOR,
                CONNECTION_THICKNESS,
            )
        for point in points:
            cv2.circle(frame, point, LANDMARK_RADIUS, LANDMARK_COLOR, -1)

        # Label the hand on the video next to its wrist.
        cv2.putText(
            frame,
            hand.handedness.value,
            (points[0][0] + 10, points[0][1] + 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )