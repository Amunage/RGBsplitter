from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QPushButton


TAB_WIDGET = """
QTabWidget::pane {
    border-top: 2px solid #C2C7CB;
}

QTabWidget::tab-bar {
    left: 5px;
}

QTabBar::tab {
    background: #333333;
    color: #c8c8c8;
    padding: 5px;
    border: 1px solid #C4C4C3;
    border-bottom-color: #C2C7CB;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    min-width: 130px;
}

QTabBar::tab:selected, QTabBar::tab:hover {
    background: #c8c8c8;
    color: #333333;
}

QTabBar::tab:selected {
    border-color: #9B9B9B;
    border-bottom-color: #C2C7CB;
}

QTabBar::tab:!selected {
    margin-top: 2px;
}
"""


COMBOBOX = """
QComboBox {
    background-color: #333333;
    color: #c8c8c8;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 0px 5px;
    min-width: 6em;
}

QComboBox:hover {
    border: 1px solid #aaaaaa;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 15px;
    border-left-width: 1px;
    border-left-color: darkgray;
    border-left-style: solid;
    border-top-right-radius: 3px;
    border-bottom-right-radius: 3px;
    background-color: #555555;
}

QComboBox QAbstractItemView {
    border: 2px solid darkgray;
    selection-background-color: #444444;
    background-color: #333333;
    color: #ffffff;
    outline: 0px;
}

QComboBox QListView::item {
    height: 14px;
    min-height: 14px;
    margin: 0px;
    padding: 0px 4px;
    border: 0px;
}

QComboBox QListView::item:selected {
    background-color: #444444;
}

QComboBox QListView::item:hover {
    background-color: #555555;
    color: #ffffff;
}
"""

LINE_EDIT = """
QLineEdit {
    background-color: #333333;
    color: #c8c8c8;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 2px;
    selection-background-color: #556677;
    selection-color: #eff0f1;
}
"""

BUTTON = """
QPushButton {
    background-color: #333333;
    color: #c8c8c8;
    border: 2px solid #555555;
    border-radius: 4px;
    padding: 5px 10px;
}

QPushButton:hover {
    background-color: #555555;
}

QPushButton:pressed {
    background-color: #777777;
    border: 2px solid #aaaaaa;
}

QPushButton:disabled {
    background-color: #444444;
    border: 2px solid #444444;
    color: #666666;
}
"""

ICON_BUTTON = """
QPushButton {
    background-color: #303030;
    border: 1px solid #4a4a4a;
    border-radius: 3px;
    padding: 0px;
}

QPushButton:hover {
    background-color: #3a3a3a;
    border: 1px solid #707070;
}

QPushButton:pressed {
    background-color: #262626;
    border: 1px solid #8a8a8a;
}

QPushButton:disabled {
    background-color: #292929;
    border: 1px solid #3a3a3a;
}
"""

CHECKBOX = """
QCheckBox {
    color: #c8c8c8;
    spacing: 4px;
}
"""

LABEL = "color: #c8c8c8"

PROGRESS_BAR = """
QProgressBar {
    background-color: #333333;
    border: 1px solid #555555;
    border-radius: 3px;
    max-height: 8px;
    min-height: 8px;
}

QProgressBar::chunk {
    background-color: #8a8a8a;
    border-radius: 2px;
}
"""


def create_icon_button(icon_name: str, tooltip: str, callback) -> QPushButton:
    button = QPushButton()
    button.setIcon(flat_icon(icon_name))
    button.setIconSize(QSize(16, 16))
    button.setFixedSize(24, 22)
    button.setToolTip(tooltip)
    button.setAccessibleName(tooltip)
    button.clicked.connect(callback)
    button.setStyleSheet(ICON_BUTTON)
    return button


def flat_icon(icon_name: str) -> QIcon:
    pixmap = QPixmap(16, 16)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    pen = QPen(QColor(170, 178, 186), 1.8)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    if icon_name == "remove":
        painter.drawLine(5, 5, 11, 11)
        painter.drawLine(11, 5, 5, 11)
    elif icon_name == "reset":
        _draw_reset_icon(painter)
    else:
        _draw_refresh_icon(painter)

    painter.end()
    return QIcon(pixmap)


def _draw_refresh_icon(painter: QPainter) -> None:
    painter.drawArc(QRectF(3.5, 2.8, 9.0, 9.0), 30 * 16, 145 * 16)
    painter.drawArc(QRectF(3.5, 4.2, 9.0, 9.0), 210 * 16, 145 * 16)
    _draw_arrow_head(painter, QPointF(11.4, 3.2), QPointF(13.4, 4.0), QPointF(11.8, 5.8))
    _draw_arrow_head(painter, QPointF(4.6, 12.8), QPointF(2.6, 12.0), QPointF(4.2, 10.2))


def _draw_reset_icon(painter: QPainter) -> None:
    painter.drawArc(QRectF(3.0, 3.0, 10.0, 10.0), 135 * 16, 305 * 16)
    _draw_arrow_head(painter, QPointF(4.4, 5.0), QPointF(3.0, 2.8), QPointF(6.0, 3.2))


def _draw_arrow_head(painter: QPainter, a: QPointF, b: QPointF, c: QPointF) -> None:
    path = QPainterPath()
    path.moveTo(a)
    path.lineTo(b)
    path.lineTo(c)
    path.closeSubpath()
    painter.fillPath(path, QColor(170, 178, 186))
