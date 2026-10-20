# Wraith *v0.2.0*

DJing without the decks: A virtual DJ controller controlled entirely with your hand movements in the air using your webcam. It works by utilising the latest AI/ML tools for detecting hand movements in video and maps this into MIDI signals a DJ software like Mixxx can understand.

## Latest update (v0.2.0)

- **Pinch to control**: pinch your thumb against a finger and move your hand up or down to set that control. Each finger drives its own control (index for volume, middle for low EQ, ring for mid EQ, pinky for high EQ), so one hand can work four controls.
- **Two decks, one per side**: the left half of the screen controls deck 1 and the right half controls deck 2. It's where your hand is that counts, not which hand it is, so either hand can work either deck.
- **Steadier control**: a pinch has to be held briefly before it counts, and a hand that drops out of view for a moment keeps its state, so controls don't flicker or jump.
- **Controls hold their value**: let go of a pinch or move your hand out of view and the control stays where you left it.
- **Settings file**: settings are saved to your user config folder, and a broken or outdated settings file falls back to defaults instead of stopping the app. You can turn the hand skeleton overlay on or off there.