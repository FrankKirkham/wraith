# Owns the Qt window and drives the pipeline one frame per timer tick
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QDialog, QMainWindow

from wraith_app import settings
from wraith_app.core.pipeline import Pipeline
from wraith_app.ui.settings_dialog import SettingsDialog
from wraith_app.ui.video_view import VideoView

WINDOW_TITLE = "Wraith v0.3.0"

class MainWindow(QMainWindow):
    def __init__(self, pipeline: Pipeline) -> None:
        super().__init__()
        self.pipeline = pipeline
        self.setWindowTitle(WINDOW_TITLE)

        self.video = VideoView()
        self.setCentralWidget(self.video)

        self.menuBar().addAction("Settings", self.open_settings)

        # cap.read() blocks until the next frame, so 0 runs at the camera's rate
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)

    def start(self) -> None:
        self.pipeline.start()
        self.video.set_show_centre_line(self.pipeline.settings.visuals.show_centre_line)
        self.timer.start(0)

    def tick(self) -> None:
        frame = self.pipeline.process_frame()
        if frame is None:
            self.close()
            return
        self.video.set_frame(frame)

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.pipeline.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.pipeline.settings = dialog.result_settings()
            settings.save(self.pipeline.settings)
            self.video.set_show_centre_line(self.pipeline.settings.visuals.show_centre_line)

    def closeEvent(self, event) -> None:
        self.timer.stop()
        self.pipeline.close()
        super().closeEvent(event)
