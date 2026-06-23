from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QSizePolicy, QTabWidget, QVBoxLayout, QWidget

from . import styles
from .resources import SMALL_ICON_PATH
from .ui.preview_area import PreviewArea
from .ui.tabs.merge_tab import MergeTab
from .ui.tabs.mix_tab import MixTab
from .ui.tabs.split_tab import SplitTab


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle("RGB Splitter")
        self.resize(450, 700)
        self.setMinimumSize(450, 700)
        self.setWindowIcon(QIcon(str(SMALL_ICON_PATH)))

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 0)

        self.preview_area = PreviewArea()
        self.preview_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self.preview_area)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.tab_widget = QTabWidget()
        self.tab_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.tab_widget.setStyleSheet(styles.TAB_WIDGET)

        self.mix_tab = MixTab()
        self.merge_tab = MergeTab()
        self.split_tab = SplitTab()

        self.tab_widget.addTab(self.mix_tab, "Mix")
        self.tab_widget.addTab(self.merge_tab, "Merge")
        self.tab_widget.addTab(self.split_tab, "Split")
        main_layout.addWidget(self.tab_widget)

        self.preview_area.image_list_updated.connect(self.mix_tab.update_image_list)
        self.preview_area.image_list_updated.connect(self.merge_tab.update_image_list)
        self.preview_area.image_list_updated.connect(self.split_tab.update_image_list)
