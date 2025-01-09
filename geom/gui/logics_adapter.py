from PyQt5.QtCore import QObject, QThread

from gui.event_bus import Event
from logic.logics_object import LogicsObject


class LogicsAdapter(QObject):
    def __init__(self, event_bus):
        QObject.__init__(self)
        self.handled_events = {
            'add_line', 'add_constraint', 'delete_line', 'delete_constraint', 'move_line',
            'move_point'
        }
        methods_arr = [self.add_task] * len(self.handled_events)
        self.methods_mapping = dict(zip(self.handled_events, methods_arr))
        self.event_bus = event_bus
        self.event_bus.register(self)

        self.logics_object = LogicsObject()
        self.logics_thread = QThread()
        self.logics_object.moveToThread(self.logics_thread)
        self.logics_object.task_done.connect(self.deal_task_result)
        # noinspection PyUnresolvedReferences
        self.logics_thread.started.connect(self.logics_object.run)
        self.logics_thread.start()

    def handle(self, event):
        method = self.methods_mapping.get(event.name, None)
        if method is None:
            raise RuntimeError('can\'t handle: {}'.format(event.name))
        # noinspection PyArgumentList
        return method(event)

    def can_handle(self, event):
        return event.name in self.handled_events

    def add_task(self, task):
        self.logics_object.add_task(task)

    def deal_task_result(self, result):
        if result.error is not None:
            return self.event_bus.dispatch(Event(name='error', text=result.error))

        self.event_bus.dispatch(Event(name='task_done', result=result))
