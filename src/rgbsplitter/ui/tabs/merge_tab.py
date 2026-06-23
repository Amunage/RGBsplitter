from PIL import Image
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from ... import styles
from ...core.image_ops import (
    CHANNELS,
    ImageInput,
    MergeSelection,
    build_merge_image,
    channel_item_entries,
    infer_size_from_last_image,
    resolve_output_size,
    save_merge_image,
)
from ..controls import compact_combo_box, current_combo_value, set_combo_entries


class MergeTab(QWidget):
    preview_changed = Signal()

    def __init__(self, image_paths: list[ImageInput] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.image_paths = image_paths or []
        self.channel_widgets: dict[str, QComboBox] = {}
        self._init_ui()
        self._set_export_enabled()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        for channel in CHANNELS:
            row = QHBoxLayout()

            channel_label = QLabel(channel)
            channel_label.setFixedWidth(20)
            channel_label.setStyleSheet(styles.LABEL)

            image_combo = compact_combo_box(QComboBox())
            set_combo_entries(image_combo, channel_item_entries(self.image_paths))
            image_combo.currentIndexChanged.connect(lambda *_: self.preview_changed.emit())

            self.channel_widgets[channel] = image_combo

            row.addWidget(channel_label)
            row.addWidget(image_combo)
            layout.addLayout(row)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter Name")
        self.name_input.setStyleSheet(styles.LINE_EDIT)
        layout.addWidget(self.name_input)

        export_layout = QHBoxLayout()
        self.keep_ratio_checkbox = QCheckBox("Keep Ratio")
        self.keep_ratio_checkbox.setStyleSheet(styles.CHECKBOX)
        self.keep_ratio_checkbox.toggled.connect(lambda *_: self.preview_changed.emit())
        export_layout.addWidget(self.keep_ratio_checkbox)

        self.image_size_combo_box = compact_combo_box(QComboBox())
        self.image_size_combo_box.addItems(["128", "256", "512", "1024", "2048", "4096"])
        self.image_size_combo_box.setCurrentText("4096")
        self.image_size_combo_box.currentIndexChanged.connect(lambda *_: self.preview_changed.emit())
        export_layout.addWidget(self.image_size_combo_box)

        self.file_format_combo_box = compact_combo_box(QComboBox())
        self.file_format_combo_box.addItems(["tga", "png"])
        export_layout.addWidget(self.file_format_combo_box)

        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.export_image)
        self.export_button.setStyleSheet(styles.BUTTON)
        export_layout.addWidget(self.export_button)

        layout.addLayout(export_layout)

    def update_image_list(self, image_paths: list[ImageInput]) -> None:
        self.image_paths = image_paths
        entries = channel_item_entries(self.image_paths)
        last_image_name = entries[-1][0]

        self.name_input.setText(f"{last_image_name}_mix" if self.image_paths else "")

        for channel in CHANNELS:
            combo_box = self.channel_widgets[channel]
            set_combo_entries(combo_box, entries)
            combo_box.setCurrentIndex(len(entries) - 1 if self.image_paths else 0)

        self._update_image_size()
        self._set_export_enabled()
        self.preview_changed.emit()

    def export_image(self) -> None:
        if not self.image_paths:
            return

        output_path = save_merge_image(
            image_paths=self.image_paths,
            selections=self.current_selections(),
            image_size=self.current_output_size(),
            output_name=self.name_input.text().strip(),
            file_format=self.file_format_combo_box.currentText(),
        )
        print(f"Image saved to {output_path}")

    def build_preview_image(self) -> Image.Image | None:
        if not self.image_paths:
            return None

        return build_merge_image(self.image_paths, self.current_selections(), self.current_output_size(preview=True))

    def current_selections(self) -> dict[str, MergeSelection]:
        return {
            channel: MergeSelection(image_name=current_combo_value(self.channel_widgets[channel]))
            for channel in CHANNELS
        }

    def current_output_size(self, preview: bool = False) -> tuple[int, int]:
        selections = self.current_selections()
        selected_size = int(self.image_size_combo_box.currentText())
        if preview:
            selected_size = min(selected_size, 1024)

        return resolve_output_size(
            image_paths=self.image_paths,
            selected_size=selected_size,
            keep_aspect_ratio=self.keep_ratio_checkbox.isChecked(),
            preferred_image_names=[selection.image_name for selection in selections.values()],
        )

    def _update_image_size(self) -> None:
        size = str(infer_size_from_last_image(self.image_paths))
        index = self.image_size_combo_box.findText(size)
        if index >= 0:
            self.image_size_combo_box.setCurrentIndex(index)

    def _set_export_enabled(self) -> None:
        self.export_button.setEnabled(bool(self.image_paths))
