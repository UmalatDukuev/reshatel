from PyQt5.QtCore import QLineF, Qt
from PyQt5.QtGui import QPen, QBrush
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene

import storage
from gui.drawings.event_handlers import Mover, LineDrawer, Deleter, Chooser
from gui.event_bus import Event


def get_pen(color, width):
    pen = QPen(color)
    pen.setWidth(width)
    return pen


class GraphicsView(QGraphicsView):
    POINT_RADIUS = 2
    tmpobj = []

    def __init__(self, event_bus):
        self.start = None
        self.end = None
        self.item = None
        self.path = None
        self.handlers_mapping = {
            'move': Mover(self),
            'new_line': LineDrawer(self),
            'delete': Deleter(self),
            'constraint': Chooser(self),
        }

        self.task_result_handlers = {
            'add_line': self.on_line_add,
            'delete_line': self.on_line_delete,
            'move_line': self.on_line_moved,
            'move_point': self.on_point_moved,
            'add_constraint': self.on_constraint_applied,
            # 'clicked_constraint': self.on_constraint_clicked,
        }

        self.lines = {}
        self.points = {}
        self.blocked = False
        self.line_id_counter = 0
        self.point_id_counter = 0
        self.storage = storage.Storage()
        self.event_bus = event_bus

        super(GraphicsView, self).__init__()
        self.setScene(QGraphicsScene())
        self.handler = LineDrawer(self)

    def set_handler(self, mode):
        self.handler = self.handlers_mapping.get(mode, None)
        if self.handler is None:
            raise RuntimeError('mode changed in drawing: unknown mode')

    def block_processing(func):
        def wrapper(self, *args, **kwargs):
            self.event_bus.dispatch(Event('block', is_set=True))
            return func(self, *args, **kwargs)
        return wrapper

    def process_if_enabled(func):
        def wrapper(self, *args, **kwargs):
            if not self.blocked:
                ret_val = func(self, *args, **kwargs)
                return ret_val
            self.event_bus.dispatch(Event(name='error', text='Подождите, идет расчет!'))

        return wrapper

    @process_if_enabled
    def mousePressEvent(self, event):
        self.handler.handle_mouse_pressed(event)

    @process_if_enabled
    def mouseMoveEvent(self, event):
        self.handler.handle_mouse_moved(event)

    @process_if_enabled
    def mouseReleaseEvent(self, event):
        self.handler.handle_mouse_released(event)

    @block_processing
    def launch_add_line(self, point_1, point_2):
        self.event_bus.dispatch(Event(name='add_line', point_1=point_1, point_2=point_2))

    @block_processing
    def launch_delete_line(self, line_id):
        self.event_bus.dispatch(Event(name='delete_line', line_id=line_id))

    @block_processing
    def launch_move_line(self, line_id, move_vector):
        self.event_bus.dispatch(Event(name='move_line', line_id=line_id, move_vector=move_vector))

    @block_processing
    def launch_move_point(self, point_id, move_vector):
        self.event_bus.dispatch(Event(name='move_point', point_id=point_id, move_vector=move_vector))

    def add_new_constraint_object(self, obj_id, obj_type, item):
        success = self.event_bus.dispatch(Event(name='new_constraint_obj', obj_id=obj_id, obj_type=obj_type))

    def highlight_constraint(self, event):
        obj_type = event.params['obj_type']
        if obj_type == 'point':
            item = self.points[event.params['obj_id']]
            tmp = self.scene().addEllipse(item.rect(), pen=get_pen(Qt.green, 4))
        else:
            item = self.lines[event.params['obj_id']]['line']
            tmp = self.scene().addLine(item.line(), pen=get_pen(Qt.green, 3))
        self.tmpobj.append(tmp)

    def on_task_done(self, task_result):
        method = self.task_result_handlers.get(task_result.name)
        if method is None:
            return
        # noinspection PyArgumentList
        method(task_result.params)

    def on_line_add(self, task_result):
        p1_id = task_result.get('p1_id', None)
        p2_id = task_result.get('p2_id', None)
        line_id = task_result.get('line_id', None)
        if None in (p1_id, p2_id, line_id):
            raise RuntimeError('invalid_result')
        point1 = self.storage.points[p1_id]
        point2 = self.storage.points[p2_id]
        line_to_add = QLineF(point1.x(), point1.y(), point2.x(), point2.y())
        line_to_add.id = line_id
        line_handle = self.scene().addLine(line_to_add, pen=get_pen(Qt.black, 3))

        # crutch to know further the id of selected object
        line_handle.id = line_id

        self.lines[line_id] = {'line': line_handle, 'p1_id': p1_id, 'p2_id': p2_id}

        point1_handle = self.scene().addEllipse(point1.x() - self.POINT_RADIUS,
                                                point1.y() - self.POINT_RADIUS,
                                                self.POINT_RADIUS ** 2,
                                                self.POINT_RADIUS ** 2,
                                                get_pen(Qt.blue, 5),
                                                QBrush(Qt.SolidPattern))
        # crutch to know further the id of selected object
        point1_handle.id = p1_id

        point2_handle = self.scene().addEllipse(point2.x() - self.POINT_RADIUS,
                                                point2.y() - self.POINT_RADIUS,
                                                self.POINT_RADIUS ** 2,
                                                self.POINT_RADIUS ** 2,
                                                get_pen(Qt.blue, 5),
                                                QBrush(Qt.SolidPattern))
        # crutch to know further the id of selected object
        point2_handle.id = p2_id

        self.points[p1_id] = point1_handle
        self.points[p2_id] = point2_handle

    def on_line_delete(self, task_result):
        line_id = task_result.get('line_id', None)
        if line_id is None:
            raise RuntimeError('invalid_result')

        line_dict = self.lines.get(line_id, None)
        p1_id = line_dict['p1_id']
        p2_id = line_dict['p2_id']
        point1_handle = self.points.get(p1_id)
        point2_handle = self.points.get(p2_id)
        line_handle = line_dict['line']
        if None in (point1_handle, point2_handle, line_handle):
            raise RuntimeError('invalid ids in result')
        for item in (point1_handle, point2_handle, line_handle):
            self.scene().removeItem(item)

    def on_line_moved(self, task_result):
        self.redraw_scene()

    def on_point_moved(self, task_result):
        self.redraw_scene()

    def clear_highlights(self):
        for elem in self.tmpobj:
            self.scene().removeItem(elem)

    def on_constraint_applied(self, task_result):
        self.clear_highlights()
        self.redraw_scene()

    def on_constraint_clicked(self, event):
        self.clear_highlights()
        constraint_id = event.params['constraint_id']
        objects = self.storage.constraints[constraint_id].objects
        for elem in objects:
            if elem['type'] == 'line':
                item = self.lines[elem['obj']]['line']
                tmp = self.scene().addLine(item.line(), pen=get_pen(Qt.green, 3))
            else:
                item = self.points[elem['obj']]
                tmp = self.scene().addEllipse(item.rect(), pen=get_pen(Qt.green, 4))
            self.tmpobj.append(tmp)


    def redraw_scene(self):
        for key, value in self.storage.lines.items():
            line_dict = self.lines.get(key)  # line should definitely exist
            line_handle = line_dict['line']
            p1_id = value['p1_id']
            p2_id = value['p2_id']

            point1 = self.storage.points.get(p1_id)
            point1_handle = self.points[p1_id]
            point1_handle.setRect(point1.x() - self.POINT_RADIUS,
                                  point1.y() - self.POINT_RADIUS,
                                  self.POINT_RADIUS ** 2,
                                  self.POINT_RADIUS ** 2)

            point2 = self.storage.points.get(p2_id)
            point2_handle = self.points[p2_id]
            point2_handle.setRect(point2.x() - self.POINT_RADIUS,
                                  point2.y() - self.POINT_RADIUS,
                                  self.POINT_RADIUS ** 2,
                                  self.POINT_RADIUS ** 2)

            line_handle.setLine(QLineF(point1.x(), point1.y(), point2.x(), point2.y()))
