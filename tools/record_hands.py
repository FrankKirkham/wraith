# Records HandFrames from the webcam to a JSON file for use as test fixtures
#
# Usage: python tools/record_hands.py [output.json]
# Space starts recording, space again stops and saves. q quits without saving
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2

from wraith_app.vision import vision
from wraith_app.vision.recording import RecordedFrame, save_recording

WINDOW_NAME = "Wraith recorder"
FIXTURES_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
REC_COLOR = (0, 0, 255)

def default_output_path() -> Path:
    return FIXTURES_DIR / f"recording-{datetime.now():%Y%m%d-%H%M%S}.json"

def record(output_path: Path) -> None:
    tracker = vision.HandTracker(vision.ensure_model())
    cap = vision.open_camera()
    frames = []
    record_start = None

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Failed to read from camera; stopping")
                return

            # Mirrored to match the pipeline, so recorded x coordinates line up
            frame = cv2.flip(frame, 1)
            hand_frame = tracker.detect(frame)
            vision.draw_hands(frame, hand_frame)

            if record_start is not None:
                frames.append(RecordedFrame(time.monotonic() - record_start, hand_frame))
                cv2.circle(frame, (20, 20), 8, REC_COLOR, -1)
                cv2.putText(frame, f"REC {len(frames)}", (35, 27),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, REC_COLOR, 2)
            else:
                cv2.putText(frame, "Space to record, q to quit", (10, 27),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            cv2.imshow(WINDOW_NAME, frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                print("Quit without saving")
                return
            if key == ord(" "):
                if record_start is None:
                    record_start = time.monotonic()
                    print("Recording...")
                else:
                    save_recording(output_path, frames)
                    print(f"Saved {len(frames)} frames to {output_path}")
                    return
    finally:
        cap.release()
        cv2.destroyAllWindows()
        tracker.close()

if __name__ == "__main__":
    record(Path(sys.argv[1]) if len(sys.argv) > 1 else default_output_path())
