from PySide6.QtCore import QSize
from PySide6.QtWidgets import QComboBox, QListView

from .. import styles


def compact_combo_box(combo_box: QComboBox) -> QComboBox:
    view = QListView(combo_box)
    view.setMouseTracking(True)
    view.viewport().setMouseTracking(True)
    view.setSpacing(0)
    view.setUniformItemSizes(True)
    combo_box.setView(view)
    combo_box.setIconSize(QSize(0, 0))
    combo_box.setStyleSheet(styles.COMBOBOX)
    return combo_box


def set_combo_entries(combo_box: QComboBox, entries: list[tuple[str, str]]) -> None:
    combo_box.clear()
    for display_text, value in entries:
        combo_box.addItem(display_text, value)


def current_combo_value(combo_box: QComboBox) -> str:
    value = combo_box.currentData()
    if value is None:
        return combo_box.currentText()
    return str(value)
