from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from ... import styles
from ...core.image_ops import CHANNELS, MixSelection, channel_items, infer_size_from_last_image, save_mix_image
from ..controls import compact_combo_box


class MixTab(QWidget):
    def __init__(self, image_paths: list[str] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.image_paths = image_paths or []
        self.channel_widgets: dict[tuple[str, str], QComboBox] = {}
        self._init_ui()
        self._set_export_enabled()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        source_channels = list(CHANNELS)

        for channel in CHANNELS:
            row = QHBoxLayout()

            channel_label = QLabel(channel)
            channel_label.setFixedWidth(20)
            channel_label.setStyleSheet(styles.LABEL)

            image_combo = compact_combo_box(QComboBox())
            image_combo.addItems(channel_items(self.image_paths))

            channel_combo = compact_combo_box(QComboBox())
            channel_combo.setFixedWidth(20)
            channel_combo.addItems(source_channels)
            channel_combo.setCurrentText(channel)

            self.channel_widgets[(channel, "image")] = image_combo
            self.channel_widgets[(channel, "channel")] = channel_combo

            row.addWidget(channel_label)
            row.addWidget(image_combo)
            row.addWidget(channel_combo)
            layout.addLayout(row)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter Name")
        self.name_input.setStyleSheet(styles.LINE_EDIT)
        layout.addWidget(self.name_input)

        export_layout = QHBoxLayout()
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

    def update_image_list(self, image_paths: list[str]) -> None:
        self.image_paths = image_paths
        items = channel_items(self.image_paths)
        last_image_name = items[-1]

        self.name_input.setText(f"{last_image_name}_mix" if self.image_paths else "")

        for channel in CHANNELS:
            combo_box = self.channel_widgets[(channel, "image")]
            combo_box.clear()
            combo_box.addItems(items)
            combo_box.setCurrentIndex(len(items) - 1 if self.image_paths else 0)

        self._update_image_size()
        self._set_export_enabled()

    def export_image(self) -> None:
        if not self.image_paths:
            return

        selections = {
            channel: MixSelection(
                image_name=self.channel_widgets[(channel, "image")].currentText(),
                source_channel=self.channel_widgets[(channel, "channel")].currentText(),
            )
            for channel in CHANNELS
        }

        output_path = save_mix_image(
            image_paths=self.image_paths,
            selections=selections,
            image_size=int(self.image_size_combo_box.currentText()),
            output_name=self.name_input.text().strip(),
            file_format=self.file_format_combo_box.currentText(),
        )
        print(f"Image saved to {output_path}")

    def _update_image_size(self) -> None:
        size = str(infer_size_from_last_image(self.image_paths))
        index = self.image_size_combo_box.findText(size)
        if index >= 0:
            self.image_size_combo_box.setCurrentIndex(index)

    def _set_export_enabled(self) -> None:
        self.export_button.setEnabled(bool(self.image_paths))
