import mido
from typing import Tuple

from wraith_app.vision.hand import Hand, HandFrame, ScreenSide

MIDI_MAX = 127
MIDI_CC_NUMBER = 1 # temporary choice for now

# Which half of the screen a hand is in decides the channel it controls -
# not whether it is the user's left or right hand
CHANNEL_FOR_SIDE = {
    ScreenSide.LEFT: 0,
    ScreenSide.RIGHT: 1,
}

def map_hands_to_midi(hand_frame: HandFrame) -> Tuple[mido.Message | None, mido.Message | None]:
    # One message per channel, in screen order (left half, right half). A
    # side with no hand in it gets None and so is left alone
    # Will later be changed to detect and use guestures to decide messages
    return (
        map_side(hand_frame, ScreenSide.LEFT),
        map_side(hand_frame, ScreenSide.RIGHT),
    )

def map_side(hand_frame: HandFrame, side: ScreenSide) -> mido.Message | None:
    hand = controlling_hand(hand_frame, side)
    if hand is None:
        return None

    # Currently just takes the wrist height and converts this into a cc
    # value used for volume
    return mido.Message(
        "control_change",
        channel=CHANNEL_FOR_SIDE[side],
        control=MIDI_CC_NUMBER,
        value=wrist_y_to_cc(hand.wrist.y),
    )

def controlling_hand(hand_frame: HandFrame, side: ScreenSide) -> Hand | None:
    # Both hands can sit in the same half of the frame, so one has to win:
    # take the outermost, i.e. the one nearest that side's edge of the
    # screen. That stays stable as the pair drifts around together, and
    # means bringing a second hand over does not steal the channel
    hands = hand_frame.hands_on(side)
    if not hands:
        return None

    if side is ScreenSide.LEFT:
        return min(hands, key=lambda hand: hand.wrist.x)
    else:
        return max(hands, key=lambda hand: hand.wrist.x)

def wrist_y_to_cc(wrist_y):
    height = 1.0 - wrist_y
    value = round(height * MIDI_MAX)
    return max(0, min(MIDI_MAX, value))
