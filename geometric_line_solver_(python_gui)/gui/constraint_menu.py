from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QGroupBox, QGridLayout, QPushButton, QLabel, QInputDialog
from PyQt5 import QtCore

from constraint import Constraint
from gui.event_bus import Event


class ConstraintMenu(QGroupBox):
    COLS_NUM = 4
    ROWS_NUM = 2
    NAMES = [
        'points_coincidence_constraint',
        'points_dist_constraint',
        'parallel_constraint',
        'perpendicular_constraint',
        'angle_constraint',
        'horizontal_constraint',
        'vertical_constraint',
        'point_belongs_line_constraint'
    ]

    FILES = [
        'icons/coincidence.png',
        'icons/points_dist.png',
        'icons/parallel.png',
        'icons/perpendicular.png',
        'icons/angle.png',
        'icons/horizontal.png',
        'icons/vertical.png',
        'icons/point_belong_line.png'
    ]

    TOOLTIPS = [
        'Совпадение 2х точек',
        'Расстояние между точками',
        'Параллельность',
        'Перпендикулярность',
        'Задание угла',
        'Горизонтальность',
        'Вертикальность',
        'Принадлежность точки прямой отрезка'
    ]
    LINE = 10
    POINT = 1
    # possible variants:
    # 2 points (2 points coincidence, 2 points distance)
    # 2 lines (parallel, perpendicular, angle between 2 lines)
    # 1 line (vertical, horizontal)
    # 1 line and 1 point (point belongs line)

    CONSTRAINTS_MAPPING = {
        0: set(),
        POINT * 1: set(),
        POINT * 2: {
            'points_coincidence_constraint',
            'points_dist_constraint',
        },
        LINE * 2: {
            'parallel_constraint',
            'perpendicular_constraint',
            'angle_constraint',
        },
        LINE * 1: {
            'horizontal_constraint',
            'vertical_constraint',
        },
        LINE * 1 + POINT * 1: {
            'point_belongs_line_constraint',
        },
    }

    NAMES_FILES_MAPPING = dict(zip(NAMES, FILES))
    NAMES_TOOLTIPS_MAPPING = dict(zip(NAMES, TOOLTIPS))

    def __init__(self, parent, event_bus):
        QGroupBox.__init__(self, parent)
        self.event_bus = event_bus
        self.event_bus.register(self)
        self.handled_events = {'mode_changed', 'new_constraint_obj', 'task_done', 'block', 'error'}
        self.methods_mapping = {
            'new_constraint_obj': self.on_new_object_added,
            'mode_changed': self.on_mode_changed,
            'task_done': self.on_task_done,
            'block': self.set_blocked,
            'error': self.on_error
        }

        self.button_click_callbacks = {
            name: partial(self.apply_constraint, name) for name in self.NAMES
        }

        self.points = set()
        self.lines = set()
        self.is_constraint_mode = False
        self.init_ui()
        self.blocked = False

    def init_ui(self):
        self.label = QLabel('Наложить ограничения')
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFixedHeight(20)

        self.constraints_dict = {
            name: QPushButton('') for name in self.NAMES
        }
        for name, button in self.constraints_dict.items():
            icon = QIcon(self.NAMES_FILES_MAPPING[name])
            button.setIcon(icon)
            button.setIconSize(QtCore.QSize(50, 50))
            button.resize(QtCore.QSize(50, 50))
            button.setEnabled(False)
            button.setStyleSheet("background-color: red")
            button.setToolTip(self.NAMES_TOOLTIPS_MAPPING[name])
            button.clicked.connect(self.button_click_callbacks[name])

        self.grid = QGridLayout()
        self.grid.addWidget(self.label, 0, 0, 1, 4)

        for i in range(self.ROWS_NUM):
            for j in range(self.COLS_NUM):
                name = self.NAMES[i * self.COLS_NUM + j]
                self.grid.addWidget(self.constraints_dict[name], 1 + i, j)

        self.setLayout(self.grid)

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
            return func(self, *args, **kwargs)
        return wrapper

    # @process_if_enabled
    def update_available_constraints(self):
        key = len(self.lines) * self.LINE + len(self.points) * self.POINT
        constraints_set = self.CONSTRAINTS_MAPPING[key]
        for name, button in self.constraints_dict.items():
            if name in constraints_set:
                button.setEnabled(True)
                button.setStyleSheet('background-color: green')
            else:
                button.setEnabled(False)
                button.setStyleSheet('background-color: red')

    def on_new_object_added(self, params):
        obj_id = params.get('obj_id')
        obj_type = params.get('obj_type')
        total_length = len(self.lines) + len(self.points)
        if total_length >= 2:
            self.event_bus.dispatch(Event(name='error', text='Слишком много объектов для применения ограничений'))
            return False
        if obj_type == 'line':
            self.lines.add(obj_id)
        elif obj_type == 'point':
            self.points.add(obj_id)

        self.update_available_constraints()
        self.event_bus.dispatch(Event(name='highlight_constraint', obj_type=obj_type, obj_id=obj_id))
        return True

    def on_mode_changed(self, params):
        mode = params['params'].get('mode', None)
        if self.is_constraint_mode:
            if mode != 'constraint':
                self.points.clear()
                self.lines.clear()
                self.is_constraint_mode = False
                self.update_available_constraints()
                return
        else:
            if mode == 'constraint':
                self.is_constraint_mode = True

    def set_blocked(self, params):
        blocked = params.get('is_set')
        if blocked is None:
            blocked = True
        self.blocked = blocked

    @enable_processing
    def on_error(self, params):
        self.points.clear()
        self.lines.clear()
        self.update_available_constraints()

    @enable_processing
    def on_task_done(self, params):
        self.points.clear()
        self.lines.clear()
        self.update_available_constraints()

    def get_value(self, name):
        question = 'Угол(°):' if name == 'angle_constraint' else 'Расстояние:'
        value, ok = QInputDialog.getDouble(self, '',
                                           question)

        if ok:
            return value
        raise RuntimeError('couldn\'t read from dialog')

    @block_processing
    def apply_constraint(self, name):
        objects = [{'type': 'line', 'obj': line} for line in self.lines]
        objects.extend({'type': 'point', 'obj': point} for point in self.points)
        if name in {'points_dist_constraint', 'angle_constraint', }:
            # todo: fix когда ничего не ввели вылетает
            try:
                value = self.get_value(name)
            except RuntimeError:
                self.lines.clear()
                self.points.clear()
                self.event_bus.dispatch(Event(name='cancel'))
                self.update_available_constraints()
                return
            constraint = Constraint(name=name, objects=objects, value=value)
        else:
            constraint = Constraint(name=name, objects=objects)
        self.event_bus.dispatch(Event(name='add_constraint', constraint=constraint))

    def handle(self, event):
        method = self.methods_mapping.get(event.name, None)
        if method is None:
            raise RuntimeError('can\'t handle: {}'.format(event.name))
        # noinspection PyArgumentList
        return method(event.params)

    def can_handle(self, event):
        if event.name == 'task_done':
            result = event.params.get('result')
            return result.name == 'add_constraint'
        return event.name in self.handled_events
