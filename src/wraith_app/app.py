# Entry point; the frame loop lives in ui/main_window.py and core/pipeline.py
import os
import sys

from PySide6.QtWidgets import QApplication

from wraith_app.core.pipeline import Pipeline
from wraith_app.ui.main_window import MainWindow

def run() -> None:
    print("Starting app...")
    # Importing cv2 points Qt at OpenCV's bundled plugins, which clash with PySide6's
    os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)
    os.environ.pop("QT_QPA_FONTDIR", None)
    app = QApplication(sys.argv)
    pipeline = Pipeline()
    window = MainWindow(pipeline)
    try:
        window.start()
        window.show()
        exit_code = app.exec()
    finally: # Close down everything (whether it worked or not)
        pipeline.close()
    sys.exit(exit_code)

if __name__ == "__main__":
    run()
