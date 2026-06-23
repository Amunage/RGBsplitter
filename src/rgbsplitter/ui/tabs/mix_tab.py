from PIL import Image
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from ... import styles
from ...core.image_ops import (
    CHANNELS,
    ImageInput,
    MixSelection,
    build_mix_image,
    channel_item_entries,
    infer_size_from_last_image,
    resolve_output_size,
    save_mix_image,
)
from ..controls import compact_combo_box, current_combo_value, set_combo_entries
from ..export_controls import ExportControls


class MixTab(QWidget):
    preview_changed = Signal()

    def __init__(self, image_paths: list[ImageInput] | None = None, parent: QWidget | None = None) -> None:
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
            set_combo_entries(image_combo, channel_item_entries(self.image_paths))
            image_combo.currentIndexChanged.connect(lambda *_: self.preview_changed.emit())

            channel_combo = compact_combo_box(QComboBox())
            channel_combo.setFixedWidth(20)
            channel_combo.addItems(source_channels)
            channel_combo.setCurrentText(channel)
            channel_combo.currentIndexChanged.connect(lambda *_: self.preview_changed.emit())

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

        self.export_controls = ExportControls("mix")
        self.export_controls.changed.connect(self.preview_changed.emit)
        self.export_controls.export_requested.connect(self.export_image)
        layout.addWidget(self.export_controls)

    def update_image_list(self, image_paths: list[ImageInput]) -> None:
        self.image_paths = image_paths
        entries = channel_item_entries(self.image_paths)
        last_image_name = entries[-1][0]

        self.name_input.setText(f"{last_image_name}_mix" if self.image_paths else "")

        for channel in CHANNELS:
            combo_box = self.channel_widgets[(channel, "image")]
            set_combo_entries(combo_box, entries)
            combo_box.setCurrentIndex(len(entries) - 1 if self.image_paths else 0)

        self._update_image_size()
        self._set_export_enabled()
        self.preview_changed.emit()

    def export_image(self) -> None:
        if not self.image_paths:
            return

        output_path = save_mix_image(
            image_paths=self.image_paths,
            selections=self.current_selections(),
            image_size=self.current_output_size(),
            output_name=self.name_input.text().strip(),
            file_format=self.export_controls.file_format,
        )
        print(f"Image saved to {output_path}")

    def build_preview_image(self) -> Image.Image | None:
        if not self.image_paths:
            return None

        return build_mix_image(self.image_paths, self.current_selections(), self.current_output_size(preview=True))

    def current_selections(self) -> dict[str, MixSelection]:
        return {
            channel: MixSelection(
                image_name=current_combo_value(self.channel_widgets[(channel, "image")]),
                source_channel=current_combo_value(self.channel_widgets[(channel, "channel")]),
            )
            for channel in CHANNELS
        }

    def current_output_size(self, preview: bool = False) -> tuple[int, int]:
        selections = self.current_selections()
        selected_size = self.export_controls.selected_size
        if preview:
            selected_size = min(selected_size, 1024)

        return resolve_output_size(
            image_paths=self.image_paths,
            selected_size=selected_size,
            keep_aspect_ratio=self.export_controls.keep_aspect_ratio,
            preferred_image_names=[selection.image_name for selection in selections.values()],
        )

    def _update_image_size(self) -> None:
        size = str(infer_size_from_last_image(self.image_paths))
        self.export_controls.set_inferred_size(int(size))

    def _set_export_enabled(self) -> None:
        self.export_controls.set_export_enabled(bool(self.image_paths))
