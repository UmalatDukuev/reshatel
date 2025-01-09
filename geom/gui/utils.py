from PyQt5.QtCore import QPoint


def convert_array_to_point(arr_point):
    point = QPoint(arr_point[0], arr_point[1])
    return point
