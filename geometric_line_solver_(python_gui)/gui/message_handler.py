from PyQt5.QtWidgets import QMessageBox

from gui.event_bus import Event
from gui.message_emitter import MessageEmitter


class MessageHandler(MessageEmitter):
    def __init__(self, event_bus):
        MessageEmitter.__init__(self, event_bus, handled_events={'error', 'notification'})

    def can_handle(self, event):
        return event.name in self.handled_events

    def handle(self, event):
        text = event.params.get('text')
        if text is None:
            return
        msg = QMessageBox()
        icon_to_set = QMessageBox.Critical if event.name == 'error' else QMessageBox.Information
        msg.setIcon(icon_to_set)
        msg.setText(text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()


class TaskResultHandler:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.event_bus.register(self)
        self.handled_events = {'task_done', }

    def can_handle(self, event):
        return event.name in self.handled_events

    def handle(self, event):
        pass
        # self.event_bus.dispatch(Event(name='notification', text='Готово!'))
