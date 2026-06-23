import sys

from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from .main_window import MainWindow
from .ui.update_controller import UpdateController


def apply_dark_palette(app: QApplication) -> None:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(32, 32, 32))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(200, 200, 200))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(100, 100, 100))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)


def main() -> int:
    app = QApplication(sys.argv)
    app.setOrganizationName("Amunage")
    app.setApplicationName("RGBsplitter")
    apply_dark_palette(app)

    main_window = MainWindow()
    main_window.show()
    main_window.update_controller = UpdateController(main_window)
    QTimer.singleShot(1200, main_window.update_controller.start)

    return app.exec()
