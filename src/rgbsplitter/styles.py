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

CHECKBOX = """
QCheckBox {
    color: #c8c8c8;
    spacing: 4px;
}
"""

LABEL = "color: #c8c8c8"
