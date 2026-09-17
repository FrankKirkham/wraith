# vision -> mapping -> midi_out
from wraith_app import vision, mapping
from wraith_app.midi_out import VirtualMidiPort
from wraith_app.vision import HandTracker
import cv2

WINDOW_NAME = "Wraith v0.1.0"
MIDI_PORT_NAME = "Wraith Gesture Controller"

def run() -> None:
    print("Starting app...")

    # Find or download the hand landmarker model
    model_path = vision.ensure_model()

    # Setup and open the port
    midi_port = VirtualMidiPort(MIDI_PORT_NAME)
    midi_port.open()

    # Setup the hand detector
    hand_tracker = HandTracker(model_path)
    # Get the video capture
    cap = vision.open_camera()

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Failed to read from camera; stopping")
                break

            # Mirror first so everything after works in mirrored
            frame = cv2.flip(frame, 1)

            # Detect the hands
            hands = hand_tracker.detect(frame)

            # Draw the hands onto the image
            vision.draw_hands(frame, hands)

            # Map the hands to a midi signal and send this on our port
            if hands.hand_landmarks:
                messages = mapping.map_hands_to_midi(hands)
                midi_port.send_message(messages)

            cv2.imshow(WINDOW_NAME, frame)
            # Queue the frame and have it shut with 'q'
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally: # Close down everything (whether it worked or didn't)
        cap.release()
        cv2.destroyAllWindows()
        hand_tracker.close()
        midi_port.close()

if __name__ == "__main__":
    run()