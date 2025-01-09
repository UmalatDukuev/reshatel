from PyQt5.QtWidgets import QGroupBox, QPushButton, QVBoxLayout


class ConfirmWidget(QGroupBox):
    def __init__(self, parent, event_bus):
        QGroupBox.__init__(self, parent)
        self.event_bus = event_bus
        self.event_bus.register(self)
        self.handled_events = set()
        self.init_ui()

    def init_ui(self):
        self.new_button = QPushButton('Удалить ограничение')
        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.new_button)
        self.setLayout(self.vbox)

    def handle(self, event):
        pass

    def can_handle(self, event):
        return event.name in self.handled_events
