# TODO   Not sure if we need this function

from PyQt5.QtCore import Qt

from gui.drawings.event_handlers.drawing_event_handler import EventHandler


class LineDrawer(EventHandler):
    def __init__(self, drawing):
        self.drawing = drawing
        self.started = False

    def handle_mouse_moved(self, event):
        pass

    def handle_mouse_pressed(self, event):
        if event.button() == Qt.RightButton:
            return
        if event.button() == Qt.LeftButton:
            if not self.started:
                self.drawing.start = self.drawing.mapToScene(event.pos())

    def handle_mouse_released(self, event):
        if event.button() == Qt.LeftButton:
            if not self.started:
                self.started = True
            else:
                self.started = False
                self.drawing.end = self.drawing.mapToScene(event.pos())
                self.drawing.launch_add_line(self.drawing.start, self.drawing.end)
                self.drawing.start = None
                self.drawing.end = None
