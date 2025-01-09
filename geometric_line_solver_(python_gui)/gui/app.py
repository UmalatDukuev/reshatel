from PyQt5.QtWidgets import QApplication, QGridLayout, QWidget
from PyQt5.Qt import QFontDatabase, QFont, QIcon

from gui.constraint_list import ConstraintList
from gui.constraint_menu import ConstraintMenu
from gui.drawings.drawing import Drawing
from gui.message_handler import MessageHandler, TaskResultHandler
from gui.logics_adapter import LogicsAdapter
from gui.mode_chooser import ModeChooser
from gui.event_bus import EventBus


class App(QApplication):
    def __init__(self, argv):
        QApplication.__init__(self, argv)
        self.main_window = QWidget()

        fid = QFontDatabase.addApplicationFont("./fonts/gosttypeb.ttf")
        family = QFontDatabase.applicationFontFamilies(fid)[0]
        gost = QFont(family)
        self.setFont(gost)
        self.setWindowIcon(QIcon("./fonts/logo_small.original.png"))

        self.main_window.setStyleSheet("background-color: moccasin;")

        self.event_bus = EventBus()

        self.grid = QGridLayout()

        self.mode_chooser = ModeChooser(self.main_window, self.event_bus)
        self.grid.addWidget(self.mode_chooser, 0, 0, 4, 2)

        self.constraint_menu = ConstraintMenu(self.main_window, self.event_bus)
        self.grid.addWidget(self.constraint_menu, 4, 0, 3, 2)

        self.constraint_list = ConstraintList(self.main_window, self.event_bus)
        self.grid.addWidget(self.constraint_list, 7, 0, 5, 2)

        self.drawing = Drawing(self.main_window, self.event_bus)
        self.grid.addWidget(self.drawing, 0, 2, 12, 8)

        # self.confirm_widget = ConfirmWidget(self.main_window, self.event_bus)
        # self.grid.addWidget(self.confirm_widget, 11, 0, 1, 2)

        self.logics = LogicsAdapter(self.event_bus)

        self.message_handler = MessageHandler(self.event_bus)
        self.task_done_notifier = TaskResultHandler(self.event_bus)

        self.main_window.setLayout(self.grid)

        self.main_window.setWindowTitle('решатель')

    def start(self):
        self.main_window.show()
        return self.exec_()
