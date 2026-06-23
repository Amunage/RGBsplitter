from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLineEdit, QVBoxLayout, QWidget

from ... import styles
from ...core.image_ops import CHANNELS, ImageInput, SplitSelection, infer_size_from_last_image, save_split_images, split_item_entries
from ..controls import compact_combo_box, current_combo_value, set_combo_entries
from ..export_controls import ExportControls
from ..workers import BackgroundTask


class SplitTab(QWidget):
    def __init__(self, image_paths: list[ImageInput] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.image_paths = image_paths or []
        self.channel_widgets: dict[tuple[str, str], QComboBox | QLineEdit] = {}
        self._export_task: BackgroundTask | None = None
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

        self.export_controls = ExportControls("split")
        self.export_controls.export_requested.connect(self.export_image)
        layout.addWidget(self.export_controls)

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
        if not self.image_paths or self._export_task is not None:
            return

        image_paths = self.image_paths.copy()
        selections = self.current_selections()
        image_size = self.export_controls.selected_size
        output_name = self.name_input.text().strip()
        file_format = self.export_controls.file_format
        keep_aspect_ratio = self.export_controls.keep_aspect_ratio

        task = BackgroundTask(
            lambda: save_split_images(
                image_paths=image_paths,
                selections=selections,
                image_size=image_size,
                output_name=output_name,
                file_format=file_format,
                keep_aspect_ratio=keep_aspect_ratio,
            )
        )
        task.signals.finished.connect(self._handle_export_finished)
        task.signals.failed.connect(self._handle_export_failed)
        self._export_task = task
        self.export_controls.set_busy(True, "Saving...")
        QThreadPool.globalInstance().start(task)

    def current_selections(self) -> dict[str, SplitSelection]:
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

        return selections

    def _update_image_size(self) -> None:
        size = str(infer_size_from_last_image(self.image_paths))
        self.export_controls.set_inferred_size(int(size))

    def _set_export_enabled(self) -> None:
        self.export_controls.set_export_enabled(bool(self.image_paths))

    def _handle_export_finished(self, output_paths: object) -> None:
        self._export_task = None
        self.export_controls.set_busy(False)
        self.export_controls.set_status("Saved")
        if isinstance(output_paths, list):
            for output_path in output_paths:
                print(f"Image saved to {output_path}")

    def _handle_export_failed(self, error: str) -> None:
        self._export_task = None
        self.export_controls.set_busy(False)
        self.export_controls.set_status("Failed")
        print(f"[ERROR] Export failed:\n{error}")
