from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QPushButton

ICON_COLOR = QColor(170, 178, 186)
TOGGLE_ICON_COLOR = QColor(99, 190, 255)


TAB_WIDGET = """
QTabWidget::pane {
    border-top: 2px solid #C2C7CB;
}

QTabWidget::tab-bar {
    alignment: center;
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

LABEL = "color: #c8c8c8"

PROGRESS_BAR = """
QProgressBar {
    background-color: #333333;
    border: 0px;
    border-radius: 0px;
    max-height: 3px;
    min-height: 3px;
}

QProgressBar::chunk {
    background-color: #8a8a8a;
    border-radius: 0px;
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


def create_toggle_icon_button(icon_name: str, tooltip: str, checked: bool = False) -> QPushButton:
    button = QPushButton()
    button.setCheckable(True)
    button.setIconSize(QSize(16, 16))
    button.setFixedSize(24, 22)
    button.setToolTip(tooltip)
    button.setAccessibleName(tooltip)
    button.setStyleSheet(ICON_BUTTON)
    button.setChecked(checked)
    button.setIcon(flat_icon(icon_name, TOGGLE_ICON_COLOR if checked else ICON_COLOR, checked))
    button.toggled.connect(
        lambda is_checked: button.setIcon(flat_icon(icon_name, TOGGLE_ICON_COLOR if is_checked else ICON_COLOR, is_checked))
    )
    return button


def flat_icon(icon_name: str, color: QColor | None = None, checked: bool = False) -> QIcon:
    pixmap = QPixmap(16, 16)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    icon_color = color or ICON_COLOR
    pen = QPen(icon_color, 1.8)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    if icon_name == "remove":
        painter.drawLine(5, 5, 11, 11)
        painter.drawLine(11, 5, 5, 11)
    elif icon_name == "reset":
        _draw_reset_icon(painter, icon_color)
    elif icon_name == "pin":
        _draw_assembled_preview_icon(painter, checked)
    elif icon_name == "channels":
        _draw_placed_channels_icon(painter, icon_color, checked)
    elif icon_name == "ratio":
        _draw_ratio_icon(painter, checked)
    else:
        _draw_refresh_icon(painter, icon_color)

    painter.end()
    return QIcon(pixmap)


def _draw_refresh_icon(painter: QPainter, color: QColor) -> None:
    painter.drawArc(QRectF(3.5, 2.8, 9.0, 9.0), 30 * 16, 145 * 16)
    painter.drawArc(QRectF(3.5, 4.2, 9.0, 9.0), 210 * 16, 145 * 16)
    _draw_arrow_head(painter, QPointF(11.4, 3.2), QPointF(13.4, 4.0), QPointF(11.8, 5.8), color)
    _draw_arrow_head(painter, QPointF(4.6, 12.8), QPointF(2.6, 12.0), QPointF(4.2, 10.2), color)


def _draw_reset_icon(painter: QPainter, color: QColor) -> None:
    painter.drawArc(QRectF(3.0, 3.0, 10.0, 10.0), 135 * 16, 305 * 16)
    _draw_arrow_head(painter, QPointF(4.4, 5.0), QPointF(3.0, 2.8), QPointF(6.0, 3.2), color)


def _draw_assembled_preview_icon(painter: QPainter, checked: bool) -> None:
    if checked:
        painter.drawRoundedRect(QRectF(4.2, 4.2, 7.6, 7.6), 0.9, 0.9)
        return

    for x in (3.2, 8.8):
        for y in (3.2, 8.8):
            painter.drawRoundedRect(QRectF(x, y, 4.0, 4.0), 0.7, 0.7)


def _draw_placed_channels_icon(painter: QPainter, color: QColor, checked: bool) -> None:
    path = QPainterPath()
    if checked:
        path.moveTo(3.6, 5.0)
        path.lineTo(12.4, 5.0)
        path.lineTo(8.0, 12.0)
        path.closeSubpath()
        painter.fillPath(path, color)
        return

    path.moveTo(8.0, 3.8)
    path.lineTo(12.2, 11.4)
    path.lineTo(3.8, 11.4)
    path.closeSubpath()
    painter.drawPath(path)


def _draw_ratio_icon(painter: QPainter, checked: bool) -> None:
    if checked:
        _draw_corner_box_icon(painter, 4.1, 4.1, 11.9, 11.9, 2.3)
        return

    _draw_corner_box_icon(painter, 3.4, 4.0, 12.6, 12.0, 2.9)


def _draw_corner_box_icon(painter: QPainter, left: float, top: float, right: float, bottom: float, arm: float) -> None:
    painter.drawLine(QPointF(left, top), QPointF(left + arm, top))
    painter.drawLine(QPointF(left, top), QPointF(left, top + arm))
    painter.drawLine(QPointF(right, top), QPointF(right - arm, top))
    painter.drawLine(QPointF(right, top), QPointF(right, top + arm))
    painter.drawLine(QPointF(left, bottom), QPointF(left + arm, bottom))
    painter.drawLine(QPointF(left, bottom), QPointF(left, bottom - arm))
    painter.drawLine(QPointF(right, bottom), QPointF(right - arm, bottom))
    painter.drawLine(QPointF(right, bottom), QPointF(right, bottom - arm))


def _draw_arrow_head(painter: QPainter, a: QPointF, b: QPointF, c: QPointF, color: QColor) -> None:
    path = QPainterPath()
    path.moveTo(a)
    path.lineTo(b)
    path.lineTo(c)
    path.closeSubpath()
    painter.fillPath(path, color)
