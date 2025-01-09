from functools import partial

from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QGroupBox

from storage import Storage
from .global_constants import MODES
from .event_bus import Event


class ModeChooser(QGroupBox):
    # mode_changed_signal = pyqtSignal(str, name='mode_changed')

    def __init__(self, parent, event_bus):
        self.storage = Storage()
        QGroupBox.__init__(self, parent)
        self.event_bus = event_bus
        self.event_bus.register(self)
        self.handled_events = {'block', }
        self.methods_mapping = {
            'block': self.set_blocked,
        }
        self.init_ui()
        self.blocked = False

    def process_if_enabled(func):
        def wrapper(self, *args, **kwargs):
            if not self.blocked:
                ret_val = func(self, *args, **kwargs)
                print('can do')
                return ret_val
            print('cannot do')
            self.event_bus.dispatch(Event(name='error', text='Подождите, идет расчет!'))
        return wrapper

    # @process_if_enabled
    def switch_to_new_mode(self, mode):
        if not self.blocked:
            self.event_bus.dispatch(Event(name='mode_changed', params={'mode': mode}))
            return
        self.event_bus.dispatch(Event(name='error', text='Подождите, идет расчет!'))

    def init_ui(self):
        self.buttons = {}
        self.mode_slot_mapping = {}
        for key in MODES.keys():
            method = partial(self.switch_to_new_mode, key)
            self.mode_slot_mapping[key] = method

        self.vbox = QVBoxLayout()

        for key, value in MODES.items():
            self.buttons[key] = QPushButton(value)
            self.buttons[key].clicked.connect(self.mode_slot_mapping[key])
            self.vbox.addWidget(self.buttons[key])

        self.setLayout(self.vbox)

    def set_blocked(self, event):
        blocked = event.params.get('is_set')
        if blocked is None:
            blocked = True
        self.blocked = blocked

    def handle(self, event):
        method = self.methods_mapping.get(event.name, None)
        if method is None:
            raise RuntimeError('can\'t handle: {}'.format(event.name))
        # noinspection PyArgumentList
        return method(event)

    def can_handle(self, event):
        return event.name in self.handled_events
