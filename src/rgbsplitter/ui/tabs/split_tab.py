from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget

from ... import styles
from ...core.image_ops import CHANNELS, ImageInput, SplitSelection, infer_size_from_last_image, save_split_images, split_item_entries
from ..controls import compact_combo_box, current_combo_value, set_combo_entries


class SplitTab(QWidget):
    def __init__(self, image_paths: list[ImageInput] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.image_paths = image_paths or []
        self.channel_widgets: dict[tuple[str, str], QComboBox | QLineEdit] = {}
        self._init_ui()
        self._set_export_enabled()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        source_channels = list(CHANNELS)

        for channel in CHANNELS:
            row = QHBoxLayout()

            image_combo = compact_combo_box(QComboBox())
            set_combo_entries(image_combo, split_item_entries(self.image_paths))

            channel_combo = compact_combo_box(QComboBox())
            channel_combo.setFixedWidth(20)
            channel_combo.addItems(source_channels)
            channel_combo.setCurrentText(channel)

            suffix_input = QLineEdit()
            suffix_input.setFixedWidth(60)
            suffix_input.setPlaceholderText(channel)
            suffix_input.setStyleSheet(styles.LINE_EDIT)

            self.channel_widgets[(channel, "image")] = image_combo
            self.channel_widgets[(channel, "channel")] = channel_combo
            self.channel_widgets[(channel, "suffix")] = suffix_input

            row.addWidget(image_combo)
            row.addWidget(channel_combo)
            row.addWidget(suffix_input)
            layout.addLayout(row)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter Name")
        self.name_input.setStyleSheet(styles.LINE_EDIT)
        layout.addWidget(self.name_input)

        export_layout = QHBoxLayout()
        self.keep_ratio_checkbox = QCheckBox("Keep Ratio")
        self.keep_ratio_checkbox.setStyleSheet(styles.CHECKBOX)
        export_layout.addWidget(self.keep_ratio_checkbox)

        self.image_size_combo_box = compact_combo_box(QComboBox())
        self.image_size_combo_box.addItems(["128", "256", "512", "1024", "2048", "4096"])
        self.image_size_combo_box.setCurrentText("4096")
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
        entries = split_item_entries(self.image_paths)
        last_image_name = entries[-1][0]

        self.name_input.setText(last_image_name if self.image_paths else "")

        for channel in CHANNELS:
            combo_box = self.channel_widgets[(channel, "image")]
            if isinstance(combo_box, QComboBox):
                set_combo_entries(combo_box, entries)
                combo_box.setCurrentIndex(len(entries) - 1 if self.image_paths else 0)

        self._update_image_size()
        self._set_export_enabled()

    def export_image(self) -> None:
        if not self.image_paths:
            return

        selections = {}
        for channel in CHANNELS:
            image_combo = self.channel_widgets[(channel, "image")]
            channel_combo = self.channel_widgets[(channel, "channel")]
            suffix_input = self.channel_widgets[(channel, "suffix")]
            if not isinstance(image_combo, QComboBox):
                continue
            if not isinstance(channel_combo, QComboBox):
                continue
            if not isinstance(suffix_input, QLineEdit):
                continue

            selections[channel] = SplitSelection(
                image_name=current_combo_value(image_combo),
                source_channel=current_combo_value(channel_combo),
                suffix=suffix_input.text().strip(),
            )

        output_paths = save_split_images(
            image_paths=self.image_paths,
            selections=selections,
            image_size=int(self.image_size_combo_box.currentText()),
            output_name=self.name_input.text().strip(),
            file_format=self.file_format_combo_box.currentText(),
            keep_aspect_ratio=self.keep_ratio_checkbox.isChecked(),
        )

        for output_path in output_paths:
            print(f"Image saved to {output_path}")

    def _update_image_size(self) -> None:
        size = str(infer_size_from_last_image(self.image_paths))
        index = self.image_size_combo_box.findText(size)
        if index >= 0:
            self.image_size_combo_box.setCurrentIndex(index)

    def _set_export_enabled(self) -> None:
        self.export_button.setEnabled(bool(self.image_paths))
