# Records HandFrames from the webcam to <id>.json files, one row per take in that folder's recordings.csv. 
# Defaults to recordings/fixtures/
#
# Usage: python recordings/record_hands.py [--output_dir DIR] [--middle_line] [--grid] [--max_frames FRAMES]
# --middle_line draws a faint line down the middle to show the two screen halves
# --grid draws a faint 3x3 grid on each half to show the side_location cells
# --max_frames stops a take automatically after that many frames
# The overlays are drawn after detection, so they never affect the recorded landmarks
# Space starts recording, space again stops and asks for the labels in the terminal (Enter keeps the previous take's 
# value, except for notes). Esc discards a take, q quits
#
# Checked and successful takes get moved to tests/fixtures/ along with their CSV row. Ids never clash as the next id is 
# one above the highest in last_id.txt and both CSVs
import argparse
import csv
import time
from datetime import datetime
from pathlib import Path

import cv2

from wraith_app.vision import vision
from wraith_app.vision.recording import RecordedFrame, save_recording

WINDOW_NAME = "Wraith recorder"
RECORDINGS_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = RECORDINGS_DIR / "fixtures"
CURATED_DIR = RECORDINGS_DIR.parent / "tests" / "fixtures"
LAST_ID_PATH = RECORDINGS_DIR / "last_id.txt"
CSV_NAME = "recordings.csv"
REC_COLOR = (0, 0, 255)
OVERLAY_COLOR = (255, 255, 255)
OVERLAY_ALPHA = 0.35
KEY_ESC = 27

# Each label has a list of possible values, however the notes allows free text
LABELS = {
    "gesture": ["index_pinch", "middle_pinch", "ring_pinch", "pinky_pinch", "open", "fist"],
    "hand": ["left", "right"],
    "side": ["left", "right"],
    "side_location": ["NW", "N", "NE", "W", "C", "E", "SW", "S", "SE"],
    "status": ["solid", "marginal", "near_miss", "clear_fail"],
    "person": ["Frank"],
    "dist": ["far", "mid", "near"],
    "direction": ["vertical", "horizontal", "diagonal", "still"],
    "speed": ["still", "slow", "normal", "fast"],
    "tilt": ["upright", "cw", "ccw"],
    "light_level": ["dark", "normal", "light"],
    "notes": None,
}
COLUMNS = ["id", "file", *LABELS, "frames", "recorded_at"]

def highest_id(output_dir: Path) -> int:
    ids = [0]
    if LAST_ID_PATH.exists():
        ids.append(int(LAST_ID_PATH.read_text().strip() or 0))
    for folder in {FIXTURES_DIR, CURATED_DIR, output_dir}:
        path = folder / CSV_NAME
        if path.exists():
            with path.open(newline="") as f:
                ids.extend(int(row["id"]) for row in csv.DictReader(f))
    return max(ids)

def append_row(csv_path: Path, row: dict) -> None:
    new_file = not csv_path.exists()
    with csv_path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        if new_file:
            writer.writeheader()
        writer.writerow(row)

def ask(name: str, options: list | None, previous: str | None) -> str:
    if options is None:
        return input(f"{name} (optional): ").strip()

    default = f" [{previous}]" if previous is not None else ""
    choices = "  ".join(f"{i}) {option}" for i, option in enumerate(options, 1))
    while True:
        answer = input(f"{name}  {choices}{default}: ").strip()
        if not answer and previous is not None:
            return previous
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return options[int(answer) - 1]
        if answer in options:
            return answer
        print(f"  Pick a number or one of: {', '.join(options)}")

def ask_labels(previous: dict) -> dict:
    return {name: ask(name, options, previous.get(name)) for name, options in LABELS.items()}

def confirm(prompt: str) -> bool:
    return input(f"{prompt} [Y/n]: ").strip().lower() in ("", "y", "yes")

def save_take(output_dir: Path, frames: list, labels: dict) -> int:
    take_id = highest_id(output_dir) + 1
    file_name = f"{take_id:06d}.json"
    save_recording(output_dir / file_name, frames)
    append_row(output_dir / CSV_NAME, {
        "id": take_id,
        "file": file_name,
        **labels,
        "frames": len(frames),
        "recorded_at": datetime.now().isoformat(timespec="seconds"),
    })
    LAST_ID_PATH.write_text(f"{take_id}\n")
    return take_id

def draw_guides(frame, middle_line: bool, grid: bool) -> None:
    height, width = frame.shape[:2]
    overlay = frame.copy()
    if middle_line or grid:
        cv2.line(overlay, (width // 2, 0), (width // 2, height), OVERLAY_COLOR, 2)
    if grid:
        for i in (1, 2, 4, 5):
            x = width * i // 6
            cv2.line(overlay, (x, 0), (x, height), OVERLAY_COLOR, 1)
        for i in (1, 2):
            y = height * i // 3
            cv2.line(overlay, (0, y), (width, y), OVERLAY_COLOR, 1)
    cv2.addWeighted(overlay, OVERLAY_ALPHA, frame, 1 - OVERLAY_ALPHA, 0, dst=frame)

def record(output_dir: Path, middle_line: bool = False, grid: bool = False, max_frames: int | None = None) -> None:
    tracker = vision.HandTracker(vision.ensure_model())
    cap = vision.open_camera()
    frames = []
    record_start = None
    previous_labels = {}

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Failed to read from camera, stopping...")
                return

            # Mirrored to match the pipeline, so recorded x coordinates line up
            frame = cv2.flip(frame, 1)
            hand_frame = tracker.detect(frame)
            if middle_line or grid:
                draw_guides(frame, middle_line, grid)
            vision.draw_hands(frame, hand_frame)

            if record_start is not None:
                frames.append(RecordedFrame(time.monotonic() - record_start, hand_frame))
                cv2.circle(frame, (20, 20), 8, REC_COLOR, -1)
                count = f"{len(frames)}/{max_frames}" if max_frames else f"{len(frames)}"
                cv2.putText(frame, f"REC {count}  (Esc to discard)", (35, 27),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, REC_COLOR, 2)
            else:
                cv2.putText(frame, "Space to record, q to quit", (10, 27),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            cv2.imshow(WINDOW_NAME, frame)
            key = cv2.waitKey(1) & 0xFF
            if record_start is None:
                if key == ord("q"):
                    return
                if key == ord(" "):
                    record_start = time.monotonic()
                    print("Recording...")
                continue

            if key == KEY_ESC:
                print(f"Discarded take ({len(frames)} frames)")
                frames, record_start = [], None
                continue

            hit_limit = max_frames is not None and len(frames) >= max_frames
            if key == ord(" ") or hit_limit:
                reason = "Reached the limit of" if hit_limit else "Stopped after"
                print(f"{reason} {len(frames)} frames. Label the take:")
                labels = ask_labels(previous_labels)
                if confirm("Save?"):
                    take_id = save_take(output_dir, frames, labels)
                    previous_labels = labels
                    print(f"Saved take {take_id} to {output_dir}\n")
                else:
                    print("Discarded\n")
                frames, record_start = [], None
    finally:
        cap.release()
        cv2.destroyAllWindows()
        tracker.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record labelled hand takes from the webcam")
    parser.add_argument("--output_dir", type=Path, default=FIXTURES_DIR, metavar="DIR",
                        help="folder to save takes to (default: recordings/fixtures/)")
    parser.add_argument("--middle_line", action="store_true",
                        help="draw a faint line down the middle to show the two screen halves")
    parser.add_argument("--grid", action="store_true",
                        help="draw a faint 3x3 grid on each half to show the side_location cells")
    parser.add_argument("--max_frames", type=int, metavar="FRAMES",
                        help="stop a take automatically after this many frames")
    args = parser.parse_args()
    if args.max_frames is not None and args.max_frames < 1:
        parser.error("--max_frames must be at least 1")
    record(args.output_dir, args.middle_line, args.grid, args.max_frames)
