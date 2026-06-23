from __future__ import annotations

from pathlib import Path
from typing import Callable

from PIL import Image
from PIL.ImageQt import toqimage
from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QColor, QDragEnterEvent, QDragMoveEvent, QDropEvent, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from .. import styles
from ..core.image_ops import CachedImage, image_display_name, load_cached_image
from .controls import compact_combo_box


class PreviewArea(QWidget):
    image_list_updated = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.image_paths: list[CachedImage] = []
        self._hover_preview_provider: Callable[[], Image.Image | None] | None = None
        self._hover_preview_image: Image.Image | None = None
        self._is_hover_preview_visible = False
        self._is_pointer_in_image_area = False
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.image_area = QWidget()
        self.image_area.setMouseTracking(True)
        self.image_area.installEventFilter(self)

        self.grid_layout = QGridLayout()
        self.image_area.setLayout(self.grid_layout)

        self.previews = [QLabel() for _ in range(4)]
        for index, preview in enumerate(self.previews):
            preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(preview, index // 2, index % 2)

        self.hover_preview = QLabel()
        self.hover_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hover_preview.hide()
        self.grid_layout.addWidget(self.hover_preview, 0, 0, 2, 2)

        self.combo_box = compact_combo_box(QComboBox())
        self.combo_box.currentIndexChanged.connect(self.update_previews)

        self.pin_preview_checkbox = QCheckBox()
        self.pin_preview_checkbox.setFixedWidth(20)
        self.pin_preview_checkbox.setToolTip("Pin assembled preview")
        self.pin_preview_checkbox.setStyleSheet(styles.CHECKBOX)
        self.pin_preview_checkbox.toggled.connect(self._handle_pin_preview_toggled)

        self.reset_button = QPushButton("Reset")
        self.reset_button.setFixedWidth(80)
        self.reset_button.clicked.connect(self.reset_image_list)
        self.reset_button.setStyleSheet(styles.BUTTON)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setFixedWidth(80)
        self.refresh_button.clicked.connect(self.refresh_image_list)
        self.refresh_button.setStyleSheet(styles.BUTTON)

        sub_layout = QHBoxLayout()
        sub_layout.addWidget(self.pin_preview_checkbox)
        sub_layout.addWidget(self.combo_box)
        sub_layout.addWidget(self.refresh_button)
        sub_layout.addWidget(self.reset_button)

        main_layout.addWidget(self.image_area)
        main_layout.addLayout(sub_layout)
        self.setLayout(main_layout)

    def set_hover_preview_provider(self, provider: Callable[[], Image.Image | None]) -> None:
        self._hover_preview_provider = provider

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self.image_area:
            if event.type() == QEvent.Type.Enter:
                self._is_pointer_in_image_area = True
                self.show_hover_preview()
            elif event.type() == QEvent.Type.Leave:
                self._is_pointer_in_image_area = False
                if not self.pin_preview_checkbox.isChecked():
                    self.clear_hover_preview()

        return super().eventFilter(watched, event)

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
            if self._contains_path(path):
                continue

            cached_image = load_cached_image(path)
            if cached_image is not None:
                self.image_paths.append(cached_image)

        self.image_list_updated.emit(self.image_paths.copy())
        self._update_combo_box_items()
        if self.pin_preview_checkbox.isChecked():
            self.show_hover_preview()

    def update_previews(self, index: int) -> None:
        if self._is_hover_preview_visible:
            return

        if index < 0 or index >= len(self.image_paths):
            return

        max_width = max(1, self.width() // 2 - 10)
        max_height = max(1, self.height() // 2 - 10)
        labels = ("R", "G", "B", "A")

        cached_image = self.image_paths[index]
        channels = cached_image.image.convert("RGBA").split()

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

        self.hover_preview.hide()
        for preview in self.previews:
            preview.show()

    def show_hover_preview(self) -> None:
        if self._hover_preview_provider is None:
            return

        try:
            image = self._hover_preview_provider()
        except OSError as error:
            print(f"[WARN] Hover preview unavailable: {error}")
            self.refresh_image_list()
            return
        if image is None:
            if self._is_hover_preview_visible:
                self.clear_hover_preview()
            return

        self._hover_preview_image = image.copy()
        self._is_hover_preview_visible = True
        self._set_hover_preview_image(self._hover_preview_image)

    def refresh_hover_preview(self) -> None:
        if self._is_hover_preview_visible or self.pin_preview_checkbox.isChecked():
            self.show_hover_preview()

    def clear_hover_preview(self) -> None:
        if not self._is_hover_preview_visible:
            return

        self._is_hover_preview_visible = False
        self._hover_preview_image = None
        self.hover_preview.clear()
        self.hover_preview.hide()
        for preview in self.previews:
            preview.show()
        self.update_previews(self.combo_box.currentIndex())

    def reset_image_list(self) -> None:
        self.image_paths.clear()
        self.combo_box.clear()
        self._hover_preview_image = None
        self._is_hover_preview_visible = False
        self._is_pointer_in_image_area = False
        self.pin_preview_checkbox.setChecked(False)
        self.hover_preview.clear()
        self.hover_preview.hide()
        for preview in self.previews:
            preview.clear()
            preview.show()
        self.image_list_updated.emit(self.image_paths.copy())

    def refresh_image_list(self) -> None:
        current_index = self.combo_box.currentIndex()
        current_path = self.image_paths[current_index].path if 0 <= current_index < len(self.image_paths) else None
        refreshed_images: list[CachedImage] = []

        for cached_image in self.image_paths:
            refreshed_image = load_cached_image(cached_image.path)
            if refreshed_image is not None:
                refreshed_images.append(refreshed_image)

        self.image_paths = refreshed_images
        self.image_list_updated.emit(self.image_paths.copy())
        self._update_combo_box_items()
        if self.pin_preview_checkbox.isChecked():
            self.show_hover_preview()

        current_paths = [cached_image.path for cached_image in self.image_paths]
        if current_path in current_paths:
            current_index = current_paths.index(current_path)
            self.combo_box.setCurrentIndex(current_index)
            self.update_previews(current_index)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._is_hover_preview_visible and self._hover_preview_image is not None:
            self._set_hover_preview_image(self._hover_preview_image)
        else:
            self.update_previews(self.combo_box.currentIndex())

    def _update_combo_box_items(self) -> None:
        self.combo_box.clear()
        items = [image_display_name(image_path) for image_path in self.image_paths]
        self.combo_box.addItems(items)

        if items:
            last_index = len(items) - 1
            self.combo_box.setCurrentIndex(last_index)
            self.update_previews(last_index)
        else:
            self._clear_channel_previews()

    def _set_hover_preview_image(self, image: Image.Image) -> None:
        available_rect = self.grid_layout.geometry()
        max_width = max(1, available_rect.width() - 10)
        max_height = max(1, available_rect.height() - 10)

        if max_width <= 1 or max_height <= 1:
            max_width = max(1, self.width() - 10)
            max_height = max(1, self.height() - self.combo_box.height() - 30)

        qt_image = toqimage(image.convert("RGBA"))
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(
            max_width,
            max_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        for preview in self.previews:
            preview.clear()
            preview.hide()

        self.hover_preview.setPixmap(scaled_pixmap)
        self.hover_preview.show()

    def _clear_channel_previews(self) -> None:
        self.hover_preview.clear()
        self.hover_preview.hide()
        for preview in self.previews:
            preview.clear()
            preview.show()

    def _contains_path(self, image_path: str | Path) -> bool:
        path = Path(image_path)
        return any(cached_image.path == path for cached_image in self.image_paths)

    def _handle_pin_preview_toggled(self, checked: bool) -> None:
        if checked:
            self.show_hover_preview()
            return

        if not self._is_pointer_in_image_area:
            self.clear_hover_preview()
