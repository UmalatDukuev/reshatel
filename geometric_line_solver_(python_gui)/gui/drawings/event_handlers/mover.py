from PyQt5.QtGui import QTransform, QVector2D
from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsEllipseItem
from PyQt5.QtCore import Qt

import gui.drawings.graphics_view as gv

from gui.drawings.event_handlers.drawing_event_handler import EventHandler


class Mover(EventHandler):
    def __init__(self, drawing):
        EventHandler.__init__(self)
        self.drawing = drawing
        self.item_to_move = None
        self.start = None
        self.end = None
        self.item_picked = None
        self.highlight = None

    def handle_mouse_moved(self, event):
        pass

    def handle_mouse_pressed(self, event):
        if self.item_picked is None:
            pos = self.drawing.mapToScene(event.pos())
            item = self.drawing.scene().itemAt(pos, QTransform())
            if item is None or 'id' not in item.__dict__:
                return
            if isinstance(item, QGraphicsLineItem):
                self.item_to_move = item
                self.start = pos
                self.item_picked = 'line'
                self.highlight = self.drawing.scene().addLine(item.line(), pen=gv.get_pen(Qt.green, 3))

            if isinstance(item, QGraphicsEllipseItem):
                self.item_to_move = item
                self.start = pos
                self.item_picked = 'point'
                self.highlight = self.drawing.scene().addEllipse(item.rect(), pen=gv.get_pen(Qt.green, 4))
        else:
            self.end = self.drawing.mapToScene(event.pos())
            move_vector = QVector2D(self.end - self.start)
            if self.item_picked == 'line':
                self.drawing.launch_move_line(self.item_to_move.id, move_vector)
            elif self.item_picked == 'point':
                self.drawing.launch_move_point(self.item_to_move.id, move_vector)
            self.drawing.scene().removeItem(self.highlight)
            for elem in (self.start, self.end, self.item_to_move):
                elem = None
            self.item_picked = None

    def handle_mouse_released(self, event):
        pass

    def handle_paint_event(self, event, painter):
        pass
