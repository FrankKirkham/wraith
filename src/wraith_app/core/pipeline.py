# The main app loop: vision -> mapping -> virtual_midi_port
from wraith_app.mapping import mapping
from wraith_app.midi.virtual_midi_port import VirtualMidiPort
from wraith_app.vision import vision
from wraith_app.vision.vision import HandTracker
import cv2

WINDOW_NAME = "Wraith v0.1.0"
MIDI_PORT_NAME = "Wraith Gesture Controller"

class Pipeline():
    midi_port = None
    hand_tracker = None
    cap = None

    def __init__(self, window_name: str = WINDOW_NAME, midi_port_name: str = MIDI_PORT_NAME) -> None:
        self.window_name = window_name
        self.midi_port_name = midi_port_name

    def start(self):
        # Find or download the hand landmarker model
        model_path = vision.ensure_model()

        # Setup and open the port
        self.midi_port = VirtualMidiPort(self.midi_port_name)
        self.midi_port.open()

        # Setup the hand detector
        self.hand_tracker = HandTracker(model_path)
        # Get the video capture
        self.cap = vision.open_camera()

    def process_frame(self) -> bool:
        # Run one frame through the pipeline; False means the camera is done
        ok, frame = self.cap.read()
        if not ok:
            print("Failed to read from camera; stopping")
            return False

        # Mirror first so everything after works in mirrored
        frame = cv2.flip(frame, 1)

        # Detect the hands
        hands = self.hand_tracker.detect(frame)

        # Draw the hands onto the image
        vision.draw_hands(frame, hands)

        # Map the hands to a midi signal and send this on our port
        if hands.hand_landmarks:
            messages = mapping.map_hands_to_midi(hands)
            self.midi_port.send_message(messages)

        cv2.imshow(self.window_name, frame)
        # Queue the frame and have it shut with 'q'
        return not (cv2.waitKey(1) & 0xFF == ord("q"))

    def run(self):
        self.start()
        try:
            while self.process_frame():
                pass
        finally: # Close down everything (whether it worked or didn't)
            self.close()

    def close(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None

        cv2.destroyAllWindows()

        if self.hand_tracker is not None:
            self.hand_tracker.close()
            self.hand_tracker = None

        if self.midi_port is not None:
            self.midi_port.close()
            self.midi_port = None
