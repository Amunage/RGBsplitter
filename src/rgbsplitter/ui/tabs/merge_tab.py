from collections.abc import Callable

from PIL import Image
from PySide6.QtCore import QThreadPool, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

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
from ..controls import compact_combo_box, current_combo_value, set_combo_entries, set_combo_entries_with_value
from ..export_controls import ExportControls
from ..workers import BackgroundTask


class MergeTab(QWidget):
    preview_changed = Signal()

    def __init__(self, image_paths: list[ImageInput] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.image_paths = image_paths or []
        self.channel_widgets: dict[str, QComboBox] = {}
        self._export_task: BackgroundTask | None = None
        self._init_ui()
        self._set_export_enabled()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        margins = layout.contentsMargins()
        layout.setContentsMargins(margins.left(), margins.top(), margins.right(), 0)

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

        self.export_controls = ExportControls("merge")
        self.export_controls.changed.connect(self.preview_changed.emit)
        self.export_controls.export_requested.connect(self.export_image)
        layout.addWidget(self.export_controls)

    def update_image_list(self, image_paths: list[ImageInput]) -> None:
        had_images = bool(self.image_paths)
        current_image_values = {
            channel: current_combo_value(self.channel_widgets[channel])
            for channel in CHANNELS
        }
        self.image_paths = image_paths
        entries = channel_item_entries(self.image_paths)
        last_image_name = entries[-1][0]
        initial_image_value = entries[-1][1] if self.image_paths else "None"

        self.name_input.setText(f"{last_image_name}_mix" if self.image_paths else "")

        for channel in CHANNELS:
            combo_box = self.channel_widgets[channel]
            selected_value = initial_image_value if self.image_paths and not had_images else current_image_values[channel]
            set_combo_entries_with_value(combo_box, entries, selected_value, "None")

        self._update_image_size()
        self._set_export_enabled()
        self.preview_changed.emit()

    def export_image(self) -> None:
        if not self.image_paths or self._export_task is not None:
            return

        image_paths = self.image_paths.copy()
        selections = self.current_selections()
        image_size = self.current_output_size()
        output_name = self.name_input.text().strip()
        file_format = self.export_controls.file_format

        task = BackgroundTask(
            lambda: save_merge_image(
                image_paths=image_paths,
                selections=selections,
                image_size=image_size,
                output_name=output_name,
                file_format=file_format,
            )
        )
        task.signals.finished.connect(self._handle_export_finished)
        task.signals.failed.connect(self._handle_export_failed)
        self._export_task = task
        self.export_controls.set_busy(True, "Saving...")
        QThreadPool.globalInstance().start(task)

    def build_preview_image(self) -> Image.Image | None:
        if not self.image_paths:
            return None

        return build_merge_image(self.image_paths, self.current_selections(), self.current_output_size(preview=True))

    def build_preview_job(self) -> Callable[[], Image.Image] | None:
        if not self.image_paths:
            return None

        image_paths = self.image_paths.copy()
        selections = self.current_selections()
        output_size = self.current_output_size(preview=True)
        return lambda: build_merge_image(image_paths, selections, output_size)

    def current_selections(self) -> dict[str, MergeSelection]:
        return {
            channel: MergeSelection(image_name=current_combo_value(self.channel_widgets[channel]))
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

    def _handle_export_finished(self, output_path: object) -> None:
        self._export_task = None
        self.export_controls.set_busy(False)
        self.export_controls.set_status("Saved")
        print(f"Image saved to {output_path}")

    def _handle_export_failed(self, error: str) -> None:
        self._export_task = None
        self.export_controls.set_busy(False)
        self.export_controls.set_status("Failed")
        print(f"[ERROR] Export failed:\n{error}")
