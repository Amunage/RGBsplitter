from PySide6.QtWidgets import QHBoxLayout, QProgressBar, QSizePolicy, QWidget

from .. import styles


class ExportStatusBar(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()

    def set_busy(self, busy: bool, message: str = "") -> None:
        self.progress_bar.setVisible(busy)

    def set_status(self, message: str = "") -> None:
        pass

    def _init_ui(self) -> None:
        self.setFixedHeight(4)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.progress_bar.setStyleSheet(styles.PROGRESS_BAR)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
