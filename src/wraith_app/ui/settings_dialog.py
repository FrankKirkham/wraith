from PySide6.QtWidgets import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QGroupBox

from wraith_app import settings
from wraith_app.mapping.quantisation import eq_steps, volume_steps

# (attribute on Controls, label)
CONTROLS = (
    ("volume_slider", "Volume"),
    ("high_eq_knob", "High EQ"),
    ("mid_eq_knob", "Mid EQ"),
    ("low_eq_knob", "Low EQ"),
)

class SettingsDialog(QDialog):
    def __init__(self, current: settings.Settings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self._current = current

        self.show_hand_overlay = QCheckBox()
        self.show_hand_overlay.setChecked(current.visuals.show_hand_overlay)

        self.show_centre_line = QCheckBox()
        self.show_centre_line.setChecked(current.visuals.show_centre_line)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QFormLayout(self)
        layout.addRow("Show hand overlay", self.show_hand_overlay)
        layout.addRow("Show centre line", self.show_centre_line)

        self.levels: dict[str, QComboBox] = {}
        self.negative_eq_only: dict[str, QCheckBox] = {}
        for name, label in CONTROLS:
            control = getattr(current.controls, name)
            group = QGroupBox(label)
            group_layout = QFormLayout(group)

            level = QComboBox()
            for value in settings.QUANTISATION_LEVELS:
                level.addItem("", value)
            level.setCurrentIndex(level.findData(control.quantisation.level))
            self.levels[name] = level
            group_layout.addRow("Quantisation", level)

            if isinstance(control, settings.EqKnob):
                negative = QCheckBox()
                negative.setChecked(control.negative_eq_only)
                negative.toggled.connect(lambda _, name=name: self._label_levels(name))
                self.negative_eq_only[name] = negative
                group_layout.addRow("Negative EQ only", negative)

            self._label_levels(name)
            layout.addRow(group)

        layout.addRow(buttons)

        # Added to make it look better, was a temporary fix so feel free to change later!
        hint = self.sizeHint()
        self.resize(int(hint.width() * 1.5), hint.height())

    def _label_levels(self, name: str) -> None:
        # Users only see the value count; the level stays internal
        combo = self.levels[name]
        negative = self.negative_eq_only.get(name)
        for index in range(combo.count()):
            level = combo.itemData(index)
            if negative is None:
                count = volume_steps(level)
            else:
                count = eq_steps(level, negative.isChecked())
            combo.setItemText(index, f"{count} values")

    def result_settings(self) -> settings.Settings:
        updated = self._current.model_copy(deep=True)
        updated.visuals.show_hand_overlay = self.show_hand_overlay.isChecked()
        updated.visuals.show_centre_line = self.show_centre_line.isChecked()
        for name, combo in self.levels.items():
            control = getattr(updated.controls, name)
            control.quantisation.level = combo.currentData()
            if name in self.negative_eq_only:
                control.negative_eq_only = self.negative_eq_only[name].isChecked()
        return updated
