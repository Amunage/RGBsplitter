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
