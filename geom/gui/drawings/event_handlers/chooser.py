from PyQt5.QtGui import QTransform
from PyQt5.QtWidgets import QGraphicsEllipseItem


from gui.drawings.event_handlers.drawing_event_handler import EventHandler


class Chooser(EventHandler):
    def __init__(self, drawing):
        EventHandler.__init__(self)
        self.drawing = drawing

    def handle_mouse_moved(self, event):
        pass

    def handle_mouse_pressed(self, event):
        pos = self.drawing.mapToScene(event.pos())
        item = self.drawing.scene().itemAt(pos, QTransform())
        item_type = 'point'
        if item is None or 'id' not in item.__dict__:
            return
        item_type = 'point' if isinstance(item, QGraphicsEllipseItem) else 'line'
        self.drawing.add_new_constraint_object(item.id, item_type, item)

    def handle_mouse_released(self, event):
        pass

    def handle_paint_event(self, event, painter):
        pass
