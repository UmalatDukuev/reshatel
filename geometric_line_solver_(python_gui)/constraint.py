NAME_TEXT_MAPPING = {
    'points_coincidence_constraint': 'Совпадение точек',
    'points_dist_constraint': 'Расстояние между точками: {}',
    'parallel_constraint': 'Параллельность',
    'perpendicular_constraint': 'Перпендикулярность',
    'angle_constraint': 'Угол между прямыми: {} °',
    'horizontal_constraint': 'Горизонтальность',
    'vertical_constraint': 'Вертикальность',
    'point_belongs_line_constraint': 'Принадлежность точки линии',
}


class Constraint:
    def __init__(self, name, objects, value=None):
        self.name = name
        self.objects = objects
        self.value = value

    def get_text(self):
        text = NAME_TEXT_MAPPING.get(self.name)
        if self.name in {'angle_constraint', 'points_dist_constraint', }:
            text = text.format(self.value)
        return text
