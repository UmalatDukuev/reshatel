import queue
import time

import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal

import storage
from constraint import Constraint
from logic.constraints import recalculate_point_positions
from task import TaskResult

MIN_CONSTRAINTS_TO_ANGLE = 1


class LogicsObject(QObject):
    task_done = pyqtSignal(object)

    def __init__(self):
        QObject.__init__(self)
        self.storage = storage.Storage()
        self.queue = queue.Queue(maxsize=1)
        self.methods_mapping = {
            'add_line': self.add_line,
            'add_constraint': self.add_constraint,
            'delete_line': self.delete_line,
            'delete_constraint': self.delete_constraint,
            'move_line': self.move_line,
            'move_point': self.move_point,
            # 'clicked_constraint': self.click_constraint,
        }

        self.point_id_counter = 0
        self.line_id_counter = 0
        self.constraint_id_counter = 0

    def add_task(self, task):
        try:
            self.queue.put(task)
        except queue.Full:
            print('logics is busy')
            return

    def run(self):
        while True:
            try:
                task = self.queue.get(timeout=1)
                try:
                    method = self.methods_mapping.get(task.name)
                    # time.sleep(5)
                except KeyError:
                    print('Logics Mock: wrong method')
                # noinspection PyArgumentList,PyUnboundLocalVariable
                result = None
                try:
                    result = method(**task.params)
                except RuntimeError as e:
                    self.task_done.emit(TaskResult(name=task.name, params=result, error='{}'.format(e)))
                else:
                    self.task_done.emit(TaskResult(name=task.name, params=result))
                self.queue.task_done()
            except queue.Empty:
                continue

    def add_point_to_storage(self, point):
        point_id = self.point_id_counter
        self.storage.points[point_id] = point
        self.point_id_counter += 1
        return point_id

    def add_fictive_constraint(self, constraint):
        # достанем точки отрезков-сторон угла, на случай если они принадлежат другим ограничениям
        points_id = []
        points_id.append(self.storage.lines[constraint.objects[0]['obj']]['p1_id'])
        points_id.append(self.storage.lines[constraint.objects[0]['obj']]['p2_id'])
        points_id.append(self.storage.lines[constraint.objects[1]['obj']]['p1_id'])
        points_id.append(self.storage.lines[constraint.objects[1]['obj']]['p2_id'])
        fictive_constraints_id = []
        # цикл 1: если есть общие объекты с ограничениями на вер + гор + принадл. т. прямой, то добавим фиктивные отрезки
        for cur_constr in self.storage.constraints:
            if self.storage.constraints[cur_constr].name == 'horizontal_constraint' or \
               self.storage.constraints[cur_constr].name == 'vertical_constraint' or \
               self.storage.constraints[cur_constr].name == 'point_belongs_line_constraint':
                for object in self.storage.constraints[cur_constr].objects:
                    if object['type'] == 'line':
                        for angle_obj in constraint.objects:
                            if angle_obj['type'] == 'line':
                                if angle_obj['obj'] == object['obj']:  # совпадают ли id отрезков
                                    # дальше идет добавление фикт отрезков  и выход из цикла
                                    for object in constraint.objects:
                                        if object['type'] == 'line':
                                            fictive_constraints_id.append(self.create_fictive_line_constraint(object['obj']))
                                    return fictive_constraints_id
                    if object['type'] == 'point':
                        for point_id in points_id:
                            if point_id == object['obj']:
                                # дальше идет добавление фикт отрезков и выход из цикла
                                for object in constraint.objects:
                                    if object['type'] == 'line':
                                        fictive_constraints_id.append(self.create_fictive_line_constraint(object['obj']))
                                return fictive_constraints_id

        # цикл 2: если объекты угла не связаны с другими ограничениями, тоже добавим фиктивные отрезки
        for cur_constr in self.storage.constraints:
            if self.storage.constraints[cur_constr].name != 'angle_constraint':  # не сравнивать его с собой
                for object in self.storage.constraints[cur_constr].objects:
                    if object['type'] == 'line':
                        for angle_obj in constraint.objects:
                            if angle_obj['type'] == 'line':
                                if angle_obj['obj'] == object['obj']:  # совпадают ли id отрезков
                                    return []
                    if object['type'] == 'point':
                        for point_id in points_id:
                            if point_id == object['obj']:
                                return []
        # добавление фиктивных длин отрезкам-сторонам угла, если нет общих точек или отрезков с другими ограничениями
        for object in constraint.objects:
            if object['type'] == 'line':
                fictive_constraints_id.append(self.create_fictive_line_constraint(object['obj']))
        return fictive_constraints_id

    def create_fictive_line_constraint(self, line_id):
        if len(self.storage.lines) == 0:
            return
        line = self.storage.lines[line_id]
        p1_id = line['p1_id']
        p2_id = line['p2_id']
        point_1 = self.storage.points[p1_id]
        point_2 = self.storage.points[p2_id]
        objects = [{'type': 'point', 'obj': p_id} for p_id in (p1_id, p2_id)]

        dist = np.sqrt((point_1.x() - point_2.x()) ** 2 + (point_1.y() - point_2.y()) ** 2)
        constraint = Constraint('points_dist_constraint', objects, dist)
        return self.add_constraint_to_storage(constraint)

    def add_line_to_storage(self, line):
        line_id = self.line_id_counter
        self.storage.lines[line_id] = line
        self.line_id_counter += 1
        return line_id

    def add_constraint_to_storage(self, constraint):
        for constraint_id, existed in self.storage.constraints.items():
            if existed.name == constraint.name:
                # crutch
                equal = existed.objects.__str__() == constraint.objects.__str__()
                if equal:
                    if existed.value:
                        existed.value = constraint.value
                    return constraint_id

        constraint_id = self.constraint_id_counter
        self.storage.constraints[constraint_id] = constraint
        self.constraint_id_counter += 1
        return constraint_id

    def delete_point_from_storage(self, point_id):
        self.storage.points.pop(point_id)

    def delete_line_from_storage(self, line_id):
        line_to_delete = self.storage.lines.pop(line_id)
        self.delete_point_from_storage(line_to_delete['p1_id'])
        self.delete_point_from_storage(line_to_delete['p2_id'])

    def get_line_points_from_storage(self, line_id):
        line_dict = self.storage.lines[line_id]
        point1 = self.storage.points[line_dict['p1_id']]
        point2 = self.storage.points[line_dict['p2_id']]
        return {'id': line_dict['p1_id'], 'point': point1}, {'id': line_dict['p2_id'], 'point': point2}

    def delete_constraint_from_storage(self, constraint_id):
        if constraint_id in self.storage.constraints:
            self.storage.constraints.pop(constraint_id)

    def set_point(self, point_id, point):
        self.storage.points[point_id] = point

    def add_line(self, **params):
        point1 = params.get('point_1')
        point2 = params.get('point_2')
        first_id = self.add_point_to_storage(point1)
        second_id = self.add_point_to_storage(point2)
        line_id = self.add_line_to_storage({'p1_id': first_id, 'p2_id': second_id})
        return {'p1_id': first_id, 'p2_id': second_id, 'line_id': line_id}

    def add_constraint(self, **params):
        constraint = params.get('constraint')
        constraint_id = self.add_constraint_to_storage(constraint)
        fictive_constraints = []
        if constraint.name == 'angle_constraint':
            fictive_constraints = self.add_fictive_constraint(constraint)
        try:
            recalculate_point_positions(self.storage)
        except RuntimeError as e:
            self.delete_constraint_from_storage(constraint_id)
            raise
        for fict_id in fictive_constraints:
            self.delete_constraint_from_storage(fict_id)
        return {'constraint_id': constraint_id, }

    def get_constraints_by_obj(self, obj_type, obj_id):
        points_to_search = []
        lines_to_search = []
        if obj_type == 'point':
            points_to_search.extend([obj_id, ])
        if obj_type == 'line':
            p1_id = self.storage.lines[obj_id]['p1_id']
            p2_id = self.storage.lines[obj_id]['p2_id']
            points_to_search.extend([p1_id, p2_id])
            lines_to_search.append(obj_id)
        constraints_arr = []
        for constraint_id, constraint in self.storage.constraints.items():
            for object_ in constraint.objects:
                if object_['type'] == 'line' and object_['obj'] in lines_to_search:
                    constraints_arr.append(constraint_id)

                if object_['type'] == 'point' and object_['obj'] in points_to_search:
                    constraints_arr.append(constraint_id)

        return constraints_arr

    def delete_line(self, **params):
        line_id = params.get('line_id')
        constraints = self.get_constraints_by_obj('line', line_id)
        for constraint_id in constraints:
            self.delete_constraint_from_storage(constraint_id)
        self.delete_line_from_storage(line_id)
        return {'line_id': line_id, 'constraints': constraints}

    def delete_constraint(self, **params):
        constraint_id = params.get('constraint_id')
        self.delete_constraint_from_storage(constraint_id)
        return {'constraint_id': constraint_id}

    def move_line(self, **params):
        line_id = params.get('line_id')
        move_vector = params.get('move_vector')
        point1_dict, point2_dict = self.get_line_points_from_storage(line_id)
        point1 = point1_dict['point'] + move_vector.toPoint()
        point2 = point2_dict['point'] + move_vector.toPoint()
        self.set_point(point1_dict['id'], point1)
        self.set_point(point2_dict['id'], point2)

        recalculate_point_positions(self.storage)
        return

    def move_point(self, **params):
        point_id = params.get('point_id')
        move_vector = params.get('move_vector')
        point = self.storage.points[point_id]
        point = point + move_vector.toPoint()
        self.set_point(point_id, point)
        recalculate_point_positions(self.storage)
        return

    # def click_constraint(self, **params):
    #     constraint_id = params.get('constraint_id')
    #     return {'constraint_id': constraint_id}
