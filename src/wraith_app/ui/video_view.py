# Shows the latest camera frame, scaled to fit
from PySide6.QtCore import QPointF, QRect, QSize, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QWidget

class VideoView(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._frame = None
        self._image = None
        self._show_centre_line = False
        self.setMinimumSize(320, 240)

    def set_frame(self, frame) -> None:
        # frame is a BGR numpy array from OpenCV
        height, width = frame.shape[:2]
        # QImage doesn't copy the buffer, so keep the array alive alongside it
        self._frame = frame
        self._image = QImage(frame.data, width, height, frame.strides[0], QImage.Format.Format_BGR888)
        self.update()

    def set_show_centre_line(self, show: bool) -> None:
        self._show_centre_line = show
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.black)

        if self._image is None:
            return

        # Fit the frame to the widget, keeping its aspect ratio
        size = self._image.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        target = QRect(self.rect().topLeft(), size)
        target.moveCenter(self.rect().center())

        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawImage(target, self._image)

        # Marks the split between the left and right decks
        if self._show_centre_line:
            painter.setPen(QPen(QColor(0, 0, 0, 120), 2))
            x = target.x() + target.width() / 2
            painter.drawLine(QPointF(x, target.top()), QPointF(x, target.top() + target.height()))

    def sizeHint(self) -> QSize:
        return QSize(960, 720)
