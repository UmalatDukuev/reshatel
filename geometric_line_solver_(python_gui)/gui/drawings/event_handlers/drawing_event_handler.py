import abc


class EventHandler:
    @abc.abstractmethod
    def handle_mouse_moved(self, event):
        pass

    @abc.abstractmethod
    def handle_mouse_pressed(self, event):
        pass

    @abc.abstractmethod
    def handle_mouse_released(self, event):
        pass

    @abc.abstractmethod
    def handle_paint_event(self, event, painter):
        pass