
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

from gui.event_bus import Event
from gui.global_constants import MODES
from gui.drawings.graphics_view import GraphicsView


class Drawing(QWidget):
    def __init__(self, parent, event_bus):
        QWidget.__init__(self, parent=parent)

        self.event_bus = event_bus
        self.event_bus.register(self)
        self.handled_events = {'mode_changed', 'task_done', 'block', 'clicked_constraint', 'highlight_constraint',
                               'error', 'cancel'}

        self.init_ui()
        self.methods_mapping = {
            'mode_changed': self.handle_mode_changed,
            'task_done': self.handle_task_done,
            'block': self.set_blocked,
            'clicked_constraint': self.graphics_view.on_constraint_clicked,
            'highlight_constraint': self.graphics_view.highlight_constraint,
            'error': self.on_error,
            'cancel': self.on_cancel
        }

    def init_ui(self):
        self.vbox = QVBoxLayout()
        self.mode_lbl = QLabel('Режим: {}'.format(MODES['new_line']))
        self.mode_lbl.setAlignment(Qt.AlignTop | Qt.AlignRight)
        self.vbox.addWidget(self.mode_lbl)

        # todo:uncomment when (if) this processing is done
        # self.constraints_number_lbl = QLabel('Эскиз полностью определен')
        # self.constraints_number_lbl.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        # self.vbox.addWidget(self.constraints_number_lbl)

        self.graphics_view = GraphicsView(self.event_bus)
        self.vbox.addWidget(self.graphics_view)

        self.setLayout(self.vbox)

    def enable_processing(func):
        def wrapper(self, *args, **kwargs):
            ret_val = func(self, *args, **kwargs)
            self.event_bus.dispatch(Event('block', is_set=False))
            return ret_val

        return wrapper

    def process_if_enabled(func):
        def wrapper(self, *args, **kwargs):
            if not self.graphics_view.blocked:
                ret_val = func(self, *args, **kwargs)
                print('can do')
                return ret_val
            print('cannot do')
            self.event_bus.dispatch(Event(name='error', text='Подождите, идет расчет!'))

        return wrapper

    def handle(self, event):
        method = self.methods_mapping.get(event.name, None)
        if method is None:
            raise RuntimeError('can\'t handle: {}'.format(event.name))
        # noinspection PyArgumentList
        return method(event)

    def can_handle(self, event):
        return event.name in self.handled_events

    def on_cancel(self, event):
        self.graphics_view.clear_highlights()

    @process_if_enabled
    def on_error(self, event):
        self.graphics_view.clear_highlights()

    @process_if_enabled
    def handle_mode_changed(self, event):
        self.graphics_view.clear_highlights()
        print('event: ', event.name, event.params)
        mode = event.params['params'].get('mode', None)
        if mode is None:
            raise RuntimeError('mode changed in drawing: mode parameter is required')
        self.mode_lbl.setText('Режим: {}'.format(MODES[mode]))
        self.graphics_view.set_handler(mode)

    @enable_processing
    def handle_task_done(self, task):
        result = task.params.get('result', None)
        if result is None:
            raise RuntimeError('drawing: handling task result, result is empty')
        self.graphics_view.on_task_done(result)

    def set_blocked(self, event):
        blocked = event.params.get('is_set')
        if blocked is None:
            blocked = True
        self.graphics_view.blocked = blocked
