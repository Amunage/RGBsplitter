from pathlib import Path

from PIL import Image
from PIL.ImageQt import toqimage
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QDragEnterEvent, QDragMoveEvent, QDropEvent, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QComboBox, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from .. import styles
from .controls import compact_combo_box


class PreviewArea(QWidget):
    image_list_updated = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.image_paths: list[str] = []
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.grid_layout = QGridLayout()
        self.previews = [QLabel() for _ in range(4)]
        for index, preview in enumerate(self.previews):
            preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(preview, index // 2, index % 2)

        self.combo_box = compact_combo_box(QComboBox())
        self.combo_box.currentIndexChanged.connect(self.update_previews)

        self.reset_button = QPushButton("Reset")
        self.reset_button.setFixedWidth(80)
        self.reset_button.clicked.connect(self.reset_image_list)
        self.reset_button.setStyleSheet(styles.BUTTON)

        sub_layout = QHBoxLayout()
        sub_layout.addWidget(self.combo_box)
        sub_layout.addWidget(self.reset_button)

        main_layout.addLayout(self.grid_layout)
        main_layout.addLayout(sub_layout)
        self.setLayout(main_layout)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue

            path = url.toLocalFile()
            if path not in self.image_paths:
                self.image_paths.append(path)

        self.image_list_updated.emit(self.image_paths.copy())
        self._update_combo_box_items()

    def update_previews(self, index: int) -> None:
        if index < 0 or index >= len(self.image_paths):
            return

        max_width = max(1, self.width() // 2 - 10)
        max_height = max(1, self.height() // 2 - 10)
        labels = ("R", "G", "B", "A")

        with Image.open(self.image_paths[index]) as image:
            channels = image.convert("RGBA").split()

        for channel_index, channel in enumerate(channels):
            qt_image = toqimage(channel)
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(
                max_width,
                max_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            labeled_pixmap = QPixmap(scaled_pixmap.size())
            labeled_pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(labeled_pixmap)
            painter.drawPixmap(0, 0, scaled_pixmap)
            painter.setPen(QColor(50, 50, 50))
            painter.setFont(QFont("Arial", 10))

            text_rect = labeled_pixmap.rect()
            text_rect.setBottom(text_rect.bottom() - 5)
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
                labels[channel_index],
            )
            painter.end()

            self.previews[channel_index].setPixmap(labeled_pixmap)

    def reset_image_list(self) -> None:
        self.image_paths.clear()
        self.combo_box.clear()
        for preview in self.previews:
            preview.clear()
        self.image_list_updated.emit(self.image_paths.copy())

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.update_previews(self.combo_box.currentIndex())

    def _update_combo_box_items(self) -> None:
        self.combo_box.clear()
        items = [Path(image_path).stem for image_path in self.image_paths]
        self.combo_box.addItems(items)

        if items:
            last_index = len(items) - 1
            self.combo_box.setCurrentIndex(last_index)
            self.update_previews(last_index)
