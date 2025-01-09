from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QListWidget, QScrollBar, QListWidgetItem, QVBoxLayout, QGroupBox, QMessageBox, QMenu

import storage
from gui.event_bus import Event


class ConstraintList(QGroupBox):
    def __init__(self, parent, event_bus):
        QGroupBox.__init__(self, parent)
        self.event_bus = event_bus
        self.event_bus.register(self)
        self.handled_events = {'task_done', 'block', 'error'}
        self.methods_mapping = {
            'task_done': self.on_task_done,
            'block': self.set_blocked,
            'error': self.on_error
        }

        self.result_handling_mapping = {
            'add_constraint': self.on_new_constraint,
            'delete_constraint': self.on_constraint_delete,
            'delete_line': self.on_line_delete,
        }

        self.storage = storage.Storage()
        self.init_ui()
        self.constraints = {}
        self.blocked = False

    def enable_processing(func):
        def wrapper(self, *args, **kwargs):
            ret_val = func(self, *args, **kwargs)
            self.event_bus.dispatch(Event('block', is_set=False))
            return ret_val

        return wrapper

    def process_if_enabled(func):
        def wrapper(self, *args, **kwargs):
            if not self.blocked:
                ret_val = func(self, *args, **kwargs)
                print('can do')
                return ret_val
            print('cannot do')
            self.event_bus.dispatch(Event(name='error', text='Подождите, идет расчет!'))

        return wrapper

    def block_processing(func):
        def wrapper(self, *args, **kwargs):
            self.event_bus.dispatch(Event('block', is_set=True))
            if len(args) > 1:
                args = [args[0]]
            return func(self)
        return wrapper

    def init_ui(self):
        self.vbox = QVBoxLayout()
        self.list_widget = QListWidget(self)

        scroll_bar = QScrollBar(self)

        self.list_widget.setVerticalScrollBar(scroll_bar)
        self.create_context_menu()
        self.vbox.addWidget(self.list_widget)
        self.setLayout(self.vbox)
        self.list_widget.itemClicked.connect(self.constraint_clicked)
        # self.list_widget.itemSelectionChanged.connect(self.selected_constrain_changed)

    def create_context_menu(self):
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.menu = QMenu(self.list_widget)
        action = self.menu.addAction('Удалить')
        action.triggered.connect(self.launch_delete_action)

    def constraint_clicked(self, item):
        current_item = self.list_widget.currentItem()
        self.event_bus.dispatch(Event(name='clicked_constraint', constraint_id=item.id))

    # def selected_constrain_changed(self, prev=None, new=None):
    #     a = prev
    #     b = new

    @block_processing
    def launch_delete_action(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setText('Удалить?')
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        retval = msg.exec()
        if retval == QMessageBox.Ok:
            current_item = self.list_widget.currentItem()
            self.event_bus.dispatch(Event(name='delete_constraint', constraint_id=current_item.id))

    @process_if_enabled
    def show_context_menu(self, point):
        current_item = self.list_widget.currentItem()
        if current_item is None:
            return
        self.menu.exec(self.mapToGlobal(point))

    @enable_processing
    def on_error(self, event):
        pass

    @enable_processing
    def on_task_done(self, event):
        result = event.params.get('result')
        method = self.result_handling_mapping.get(result.name)
        if method is None:
            raise ValueError('cannot handle this')
        # noinspection PyArgumentList
        return method(result.params)

    def on_line_delete(self, params):
        constraints = params.get('constraints', [])
        for constraint_id in constraints:
            constraint_to_delete = self.constraints.get(constraint_id)
            if constraint_to_delete is None:
                continue
            self.list_widget.takeItem(self.list_widget.row(constraint_to_delete))

    def on_constraint_delete(self, params):
        # result = params.get('result')
        constraint_id = params.get('constraint_id')
        constraint_to_delete = self.constraints.get(constraint_id)
        if constraint_to_delete is None:
            return
        self.list_widget.takeItem(self.list_widget.row(constraint_to_delete))

    def on_new_constraint(self, params):
        # result = params.get('result')
        constraint_id = params.get('constraint_id')
        constraint = self.storage.constraints[constraint_id]
        text = constraint.get_text()
        if constraint_id in self.constraints:
            self.constraints[constraint_id].setText(text)
            return
        constraint_widget = QListWidgetItem(text)
        constraint_widget.id = constraint_id
        self.constraints[constraint_id] = constraint_widget
        self.list_widget.addItem(constraint_widget)

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
        if event.name == 'task_done':
            result = event.params.get('result')
            return result.name in {'add_constraint', 'delete_constraint', 'delete_line'}
        return event.name in self.handled_events
