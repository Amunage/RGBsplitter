from PySide6.QtCore import QSettings, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QWidget,
)

from .. import styles
from .controls import compact_combo_box

IMAGE_SIZE_ITEMS = ["128", "256", "512", "1024", "2048", "4096"]
FILE_FORMAT_ITEMS = ["tga", "png"]


class ExportControls(QWidget):
    changed = Signal()
    export_requested = Signal()

    def __init__(self, settings_group: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings_group = settings_group
        self._settings = QSettings()
        self._has_saved_size = self._settings.contains(self._key("image_size"))
        self._export_available = False
        self._busy = False
        self._init_ui()

    @property
    def selected_size(self) -> int:
        return int(self.image_size_combo_box.currentText())

    @property
    def file_format(self) -> str:
        return self.file_format_combo_box.currentText()

    @property
    def keep_aspect_ratio(self) -> bool:
        return self.keep_ratio_checkbox.isChecked()

    def set_export_enabled(self, enabled: bool) -> None:
        self._export_available = enabled
        self._apply_enabled_state()

    def set_busy(self, busy: bool, message: str = "") -> None:
        self._busy = busy
        self.progress_bar.setVisible(busy)
        self.set_status(message)
        self._apply_enabled_state()

    def set_status(self, message: str = "") -> None:
        self.status_label.setText(message)
        self.status_label.setVisible(bool(message))

    def set_inferred_size(self, image_size: int) -> None:
        if self._has_saved_size:
            return

        index = self.image_size_combo_box.findText(str(image_size))
        if index >= 0:
            self.image_size_combo_box.setCurrentIndex(index)

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.keep_ratio_checkbox = QCheckBox("Keep Ratio")
        self.keep_ratio_checkbox.setStyleSheet(styles.CHECKBOX)
        self.keep_ratio_checkbox.setChecked(self._settings_bool("keep_ratio", False))
        layout.addWidget(self.keep_ratio_checkbox)

        self.image_size_combo_box = compact_combo_box(QComboBox())
        self.image_size_combo_box.addItems(IMAGE_SIZE_ITEMS)
        self.image_size_combo_box.setCurrentText(self._settings_text("image_size", "4096", IMAGE_SIZE_ITEMS))
        layout.addWidget(self.image_size_combo_box)

        self.file_format_combo_box = compact_combo_box(QComboBox())
        self.file_format_combo_box.addItems(FILE_FORMAT_ITEMS)
        self.file_format_combo_box.setCurrentText(self._settings_text("file_format", "tga", FILE_FORMAT_ITEMS))
        layout.addWidget(self.file_format_combo_box)

        self.export_button = QPushButton("Export")
        self.export_button.setStyleSheet(styles.BUTTON)
        layout.addWidget(self.export_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedWidth(54)
        self.progress_bar.setStyleSheet(styles.PROGRESS_BAR)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel()
        self.status_label.setFixedWidth(58)
        self.status_label.setStyleSheet(styles.LABEL)
        self.status_label.hide()
        layout.addWidget(self.status_label)

        self.keep_ratio_checkbox.toggled.connect(self._save_keep_ratio)
        self.keep_ratio_checkbox.toggled.connect(lambda *_: self.changed.emit())
        self.image_size_combo_box.currentTextChanged.connect(self._save_image_size)
        self.image_size_combo_box.currentTextChanged.connect(lambda *_: self.changed.emit())
        self.file_format_combo_box.currentTextChanged.connect(self._save_file_format)
        self.export_button.clicked.connect(self.export_requested.emit)
        self._apply_enabled_state()

    def _settings_text(self, name: str, default: str, allowed_values: list[str]) -> str:
        value = str(self._settings.value(self._key(name), default))
        return value if value in allowed_values else default

    def _settings_bool(self, name: str, default: bool) -> bool:
        value = self._settings.value(self._key(name), default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in {"1", "true", "yes", "on"}
        return bool(value)

    def _save_image_size(self, value: str) -> None:
        self._settings.setValue(self._key("image_size"), value)
        self._has_saved_size = True

    def _save_file_format(self, value: str) -> None:
        self._settings.setValue(self._key("file_format"), value)

    def _save_keep_ratio(self, checked: bool) -> None:
        self._settings.setValue(self._key("keep_ratio"), checked)

    def _key(self, name: str) -> str:
        return f"export/{self._settings_group}/{name}"

    def _apply_enabled_state(self) -> None:
        controls_enabled = not self._busy
        self.keep_ratio_checkbox.setEnabled(controls_enabled)
        self.image_size_combo_box.setEnabled(controls_enabled)
        self.file_format_combo_box.setEnabled(controls_enabled)
        self.export_button.setEnabled(self._export_available and not self._busy)
