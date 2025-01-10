
from functools import partial

import numpy as np
import math

from logic.newton import newtons_method

DEP_DICT = {
    'points_coincidence_constraint': 6,
    'points_dist_constraint': 5,
    'parallel_constraint': 9,
    'perpendicular_constraint': 9,
    'angle_constraint': 9,
    'horizontal_constraint': 5,
    'vertical_constraint': 5,
    'point_belongs_line_constraint': 7
}

# индексы для всех ограничений, кроме совпадения точек
L = 0  # L (lambda)
X_1 = 1
Y_1 = 2
X_2 = 3
Y_2 = 4
X_3 = 5
Y_3 = 6
X_4 = 7
Y_4 = 8
# для ограничения совпадения двух точек нужны две лямбда, поэтому другие индексы:
# COIN - сокращенно от Coincidence (совпадение)
COIN_L_1 = 0  # L_1 (lambda1)
COIN_L_2 = 1  # L_2 (lambda2)
COIN_X_1 = 2
COIN_Y_1 = 3
COIN_X_2 = 4
COIN_Y_2 = 5


def get_points_coincidence_constraint(v, dv):
    F = np.array([
        v[COIN_X_2] + dv[COIN_X_2] - v[COIN_X_1] - dv[COIN_X_1],
        v[COIN_Y_2] + dv[COIN_Y_2] - v[COIN_Y_1] - dv[COIN_Y_1],
        dv[COIN_X_1] - dv[COIN_L_1],
        dv[COIN_Y_1] - dv[COIN_L_2],
        dv[COIN_X_2] + dv[COIN_L_1],
        dv[COIN_Y_2] + dv[COIN_L_2],
    ])
    J = np.array([
        [0, 0, -1, 0, 1, 0],
        [0, 0, 0, -1, 0, 1],
        [-1, 0, 1, 0, 0, 0],
        [0, -1, 0, 1, 0, 0],
        [1, 0, 0, 0, 1, 0],
        [0, 1, 0, 0, 0, 1]
    ], dtype=np.double)
    return J, F


def get_points_dist_constraint(v, d, dv):
    F = np.array([
        (v[X_2] + dv[X_2] - v[X_1] - dv[X_1]) ** 2 + (v[Y_2] + dv[Y_2] - v[Y_1] - dv[Y_1]) ** 2 - d ** 2,
        dv[X_1] - 2 * dv[L] * (v[X_2] + dv[X_2] - v[X_1] - dv[X_1]),
        dv[Y_1] - 2 * dv[L] * (v[Y_2] + dv[Y_2] - v[Y_1] - dv[Y_1]),
        dv[X_2] + 2 * dv[L] * (v[X_2] + dv[X_2] - v[X_1] - dv[X_1]),
        dv[Y_2] + 2 * dv[L] * (v[Y_2] + dv[Y_2] - v[Y_1] - dv[Y_1])
    ])
    ax = v[X_2] + dv[X_2] - v[X_1] - dv[X_1]
    ay = v[Y_2] + dv[Y_2] - v[Y_1] - dv[Y_1]
    J = np.array([
        [0, -2 * ax, -2 * ay, 2 * ax, 2 * ay],
        [-2 * ax, 1 + 2 * dv[L], 0, -2 * dv[L], 0],
        [-2 * ay, 0, 1 + 2 * dv[L], 0, -2 * dv[L]],
        [2 * ax, -2 * dv[L], 0, 1 + 2 * dv[L], 0],
        [2 * ay, 0, -2 * dv[L], 0, 1 + 2 * dv[L]]
    ], dtype=np.double)
    return J, F


def get_angle_constraint(v, angle, dv):
    # 0 < angle < pi / 2
    # angle += 0.01
    #инициализация тригонометрии
    MIN_VALUE = 1e-5
    cos2 = np.cos(angle * np.pi / 180) ** 2
    if cos2 < MIN_VALUE:
        cos2 = MIN_VALUE
    sin2 = np.sin(angle * np.pi / 180) ** 2
    if sin2 < MIN_VALUE:
        sin2 = MIN_VALUE

    #инициализация начальных векторов

    x12 = v[X_2] + dv[X_2] - v[X_1] - dv[X_1]
    y12 = v[Y_2] + dv[Y_2] - v[Y_1] - dv[Y_1]
    x34 = v[X_4] + dv[X_4] - v[X_3] - dv[X_3]
    y34 = v[Y_4] + dv[Y_4] - v[Y_3] - dv[Y_3]

    # вектор промежуточных вычислений для уравнений и Якобиана.
    a = np.array([
        sin2 * (x12 ** 2 * x34 ** 2 + y12 ** 2 * y34 ** 2) + 2 * x12 * x34 * y12 * y34 - cos2 * (
                x12 ** 2 * y34 ** 2 + y12 ** 2 * x34 ** 2),
        -2 * sin2 * x34 ** 2 * x12 - 2 * x34 * y12 * y34 + 2 * cos2 * y34 ** 2 * x12,
        -2 * sin2 * y34 ** 2 * y12 - 2 * x12 * x34 * y34 + 2 * cos2 * x34 ** 2 * y12,
        2 * sin2 * x34 ** 2 * x12 + 2 * x34 * y12 * y34 - 2 * cos2 * y34 ** 2 * x12,
        2 * sin2 * y34 ** 2 * y12 + 2 * x12 * x34 * y34 - 2 * cos2 * x34 ** 2 * y12,
        -2 * sin2 * x12 ** 2 * x34 - 2 * x12 * y12 * y34 + 2 * cos2 * y12 ** 2 * x34,
        -2 * sin2 * y12 ** 2 * y34 - 2 * x12 * x34 * y12 + 2 * cos2 * x12 ** 2 * y34,
        2 * sin2 * x12 ** 2 * x34 + 2 * x12 * y12 * y34 - 2 * cos2 * y12 ** 2 * x34,
        2 * sin2 * y12 ** 2 * y34 + 2 * x12 * x34 * y12 - 2 * cos2 * x12 ** 2 * y34
    ], dtype=np.double)

    # Вектор F описывает отклонение текущего состояния системы от удовлетворяющего ограничения.
    F = np.array([
        a[0],
        dv[X_1] + dv[L] * a[1],
        dv[Y_1] + dv[L] * a[2],
        dv[X_2] + dv[L] * a[3],
        dv[Y_2] + dv[L] * a[4],
        dv[X_3] + dv[L] * a[5],
        dv[Y_3] + dv[L] * a[6],
        dv[X_4] + dv[L] * a[7],
        dv[Y_4] + dv[L] * a[8]
    ])
    # матрица якоби
    J = np.array([
        [0, a[1], a[2], a[3], a[4], a[5], a[6], a[7], a[8]],
        [a[1], 1 + 2 * dv[L] * (sin2 * x34 ** 2 - cos2 * y34 ** 2), 2 * dv[L] * x34 * y34,
         -2 * dv[L] * (sin2 * x34 ** 2 - cos2 * y34 ** 2), -2 * dv[L] * x34 * y34,
         2 * dv[L] * (2 * sin2 * x12 * x34 + y12 * y34), 2 * dv[L] * (y12 * x34 - 2 * cos2 * x12 * y34),
         -2 * dv[L] * (2 * sin2 * x12 * x34 + y12 * y34), -2 * dv[L] * (y12 * x34 - 2 * cos2 * x12 * y34)],
        [a[2], 2 * dv[L] * x34 * y34, 1 + 2 * dv[L] * (sin2 * y34 ** 2 - cos2 * x34 ** 2), -2 * dv[L] * x34 * y34,
         -2 * dv[L] * (sin2 * y34 ** 2 - cos2 * x34 ** 2), 2 * dv[L] * (x12 * y34 - 2 * cos2 * y12 * x34),
         2 * dv[L] * (2 * sin2 * y12 * y34 + x12 * x34), -2 * dv[L] * (x12 * y34 - 2 * cos2 * y12 * x34),
         -2 * dv[L] * (2 * sin2 * y12 * y34 + x12 * x34)],
        [a[3], 2 * dv[L] * (cos2 * y34 ** 2 - sin2 * x34 ** 2), -2 * dv[L] * x34 * y34,
         1 + 2 * dv[L] * (sin2 * x34 ** 2 - cos2 * y34 ** 2), 2 * dv[L] * x34 * y34,
         -2 * dv[L] * (2 * sin2 * x12 * x34 + y12 * y34), -2 * dv[L] * (x34 * y12 - 2 * cos2 * x12 * y34),
         2 * dv[L] * (2 * sin2 * x12 * x34 + y12 * y34), 2 * dv[L] * (x34 * y12 - 2 * cos2 * x12 * y34)],
        [a[4], -2 * dv[L] * x34 * y34, -2 * dv[L] * (sin2 * y34 ** 2 - cos2 * x34 ** 2), 2 * dv[L] * x34 * y34,
         1 + 2 * dv[L] * (sin2 * y34 ** 2 - cos2 * x34 ** 2), -2 * dv[L] * (x12 * y34 - 2 * cos2 * y12 * x34),
         -2 * dv[L] * (2 * sin2 * y12 * y34 + x12 * x34), 2 * dv[L] * (x12 * y34 - 2 * cos2 * y12 * x34),
         2 * dv[L] * (2 * sin2 * y12 * y34 + x12 * x34)],
        [a[5], 2 * dv[L] * (2 * sin2 * x12 * x34 + y12 * y34), 2 * dv[L] * (x12 * y34 - 2 * cos2 * y12 * x34),
         -2 * dv[L] * (2 * sin2 * x12 * x34 + y12 * y34), -2 * dv[L] * (x12 * y34 - 2 * cos2 * y12 * x34),
         1 + 2 * dv[L] * (sin2 * x12 ** 2 - cos2 * y12 ** 2), 2 * dv[L] * x12 * y12,
         -2 * dv[L] * (sin2 * x12 ** 2 - cos2 * y12 ** 2), -2 * dv[L] * x12 * y12],
        [a[6], 2 * dv[L] * (y12 * x34 - 2 * cos2 * x12 * y34), 2 * dv[L] * (2 * sin2 * y12 * y34 + x12 * x34),
         -2 * dv[L] * (x34 * y12 - 2 * cos2 * x12 * y34), -2 * dv[L] * (2 * sin2 * y12 * y34 + x12 * x34),
         2 * dv[L] * x12 * y12, 1 + 2 * dv[L] * (sin2 * y12 ** 2 - cos2 * x12 ** 2), -2 * dv[L] * x12 * y12,
         -2 * dv[L] * (sin2 * y12 ** 2 - cos2 * x12 ** 2)],
        [a[7], -2 * dv[L] * (2 * sin2 * x12 * x34 + y12 * y34), -2 * dv[L] * (x12 * y34 - 2 * cos2 * y12 * x34),
         2 * dv[L] * (2 * sin2 * x12 * x34 + y12 * y34), 2 * dv[L] * (x12 * y34 - 2 * cos2 * y12 * x34),
         -2 * dv[L] * (sin2 * x12 ** 2 - cos2 * y12 ** 2), -2 * dv[L] * x12 * y12,
         1 + 2 * dv[L] * (sin2 * x12 ** 2 - cos2 * y12 ** 2), 2 * dv[L] * x12 * y12],
        [a[8], -2 * dv[L] * (y12 * x34 - 2 * cos2 * x12 * y34), -2 * dv[L] * (2 * sin2 * y12 * y34 + x12 * x34),
         2 * dv[L] * (x34 * y12 - 2 * cos2 * x12 * y34), 2 * dv[L] * (2 * sin2 * y12 * y34 + x12 * x34),
         -2 * dv[L] * x12 * y12, -2 * dv[L] * (sin2 * y12 ** 2 - cos2 * x12 ** 2), 2 * dv[L] * x12 * y12,
         1 + 2 * dv[L] * (sin2 * y12 ** 2 - cos2 * x12 ** 2)]
    ], dtype=np.double)
    return J, F


def get_horizontal_constraint(v, dv):
    F = np.array([
        v[Y_2] + dv[Y_2] - v[Y_1] - dv[Y_1],
        dv[X_1],
        dv[Y_1] - dv[L],
        dv[X_2],
        dv[Y_2] + dv[L],
    ])
    J = np.array([
        [0, 0, -1, 0, 1],
        [0, 1, 0, 0, 0],
        [-1, 0, 1, 0, 0],
        [0, 0, 0, 1, 0],
        [1, 0, 0, 0, 1]
    ], dtype=np.double)
    return J, F


def get_vertical_constraint(v, dv):
    F = np.array([
        v[X_2] + dv[X_2] - v[X_1] - dv[X_1],
        dv[X_1] - dv[L],
        dv[Y_1],
        dv[X_2] + dv[L],
        dv[Y_2],
    ])
    J = np.array([
        [0, -1, 0, 1, 0],
        [-1, 1, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [1, 0, 0, 1, 0],
        [0, 0, 0, 0, 1]
    ], dtype=np.double)
    return J, F


def get_parallel_constraint(v, dv):
    ay12 = (v[Y_2] + dv[Y_2] - v[Y_1] - dv[Y_1])
    ay34 = (v[Y_4] + dv[Y_4] - v[Y_3] - dv[Y_3])
    ax12 = (v[X_2] + dv[X_2] - v[X_1] - dv[X_1])
    ax34 = (v[X_4] + dv[X_4] - v[X_3] - dv[X_3])

    F = np.array([
        ax12 * ay34 - ax34 * ay12,

        dv[X_1] - dv[L] * ay34,
        dv[Y_1] + dv[L] * ax34,
        dv[X_2] + dv[L] * ay34,
        dv[Y_2] - dv[L] * ax34,

        dv[X_3] + dv[L] * ay12,
        dv[Y_3] - dv[L] * ax12,
        dv[X_4] - dv[L] * ay12,
        dv[Y_4] + dv[L] * ax12,
    ])

    J = np.array([
        [0, -ay34, ax34, ay34, -ax34, ay12, ax12, -ay12, ax12],
        [-ay34, 1, 0, 0, 0, 0, dv[L], 0, -dv[L]],
        [ax34, 0, 1, 0, 0, -dv[L], 0, dv[L], 0],
        [ay34, 0, 0, 1, 0, 0, -dv[L], 0, dv[L]],
        [-ax34, 0, 0, 0, 1, dv[L], 0, -dv[L], 0],
        [ay12, 0, -dv[L], 0, dv[L], 1, 0, 0, 0],
        [-ax12, dv[L], 0, -dv[L], 0, 0, 1, 0, 0],
        [-ay12, 0, dv[L], 0, -dv[L], 0, 0, 1, 0],
        [ax12, -dv[L], 0, dv[L], 0, 0, 0, 0, 1],
    ])
    return J, F


def get_perpendicular_constraint(v, dv):
    ay12 = (v[Y_2] + dv[Y_2] - v[Y_1] - dv[Y_1])
    ay34 = (v[Y_4] + dv[Y_4] - v[Y_3] - dv[Y_3])
    ax12 = (v[X_2] + dv[X_2] - v[X_1] - dv[X_1])
    ax34 = (v[X_4] + dv[X_4] - v[X_3] - dv[X_3])

    F = np.array([
        ax12 * ax34 + ay34 * ay12,

        dv[X_1] - dv[L] * ax34,
        dv[Y_1] - dv[L] * ay34,
        dv[X_2] + dv[L] * ax34,
        dv[Y_2] + dv[L] * ay34,

        dv[X_3] - dv[L] * ax12,
        dv[Y_3] - dv[L] * ay12,
        dv[X_4] + dv[L] * ax12,
        dv[Y_4] + dv[L] * ay12,
    ])

    J = np.array([
        [0, -ax34, -ay34, ax34, ay34, -ax12, -ay12, ax12, ay12],
        [-ax34, 1, 0, 0, 0, dv[L], 0, -dv[L], 0],
        [-ay34, 0, 1, 0, 0, 0, dv[L], 0, -dv[L]],
        [ax34, 0, 0, 1, 0, -dv[L], 0, dv[L], 0],
        [ay34, 0, 0, 0, 1, 0, -dv[L], 0, dv[L]],
        [-ax12, dv[L], 0, -dv[L], 0, 1, 0, 0, 0],
        [-ay12, 0, dv[L], 0, -dv[L], 0, 1, 0, 0],
        [ax12, -dv[L], 0, dv[L], 0, 0, 0, 1, 0],
        [ay12, 0, -dv[L], 0, dv[L], 0, 0, 0, 1],
    ])
    return J, F


def get_point_belongs_line_constraint(v, dv):
    ax31 = (v[X_3] + dv[X_3] - v[X_1] - dv[X_1])
    ay31 = (v[Y_3] + dv[Y_3] - v[Y_1] - dv[Y_1])
    ay23 = (v[Y_2] + dv[Y_2] - v[Y_3] - dv[Y_3])
    ax23 = (v[X_2] + dv[X_2] - v[X_3] - dv[X_3])

    ay21 = (v[Y_2] + dv[Y_2] - v[Y_1] - dv[Y_1])
    ax21 = (v[X_2] + dv[X_2] - v[X_1] - dv[X_1])

    F = np.array([
        ax31 * ay23 - ax23 * ay31,
        dv[X_1] + dv[L] * (-ay23),
        dv[Y_1] + dv[L] * ax23,
        dv[X_2] + dv[L] * (-ay31),
        dv[Y_2] + dv[L] * ax31,
        dv[X_3] + dv[L] * ay21,
        dv[Y_3] + dv[L] * (-ax21),
    ])

    J = np.array([
        [0, -ay23, ax23, -ay31, ax31, ay21, -ax21],
        [-ay23, 1, 0, 0, -dv[L], 0, dv[L]],
        [ax23, 0, 1, dv[L], 0, -dv[L], 0],
        [-ay31, 0, dv[L], 1, 0, 0, -dv[L]],
        [ax31, -dv[L], 0, 0, 1, dv[L], 0],
        [ay21, 0, -dv[L], 0, dv[L], 1, 0],
        [-ax21, dv[L], 0, -dv[L], 0, 0, 1],
    ])
    return J, F


def get_lam_num(storage):
    lam_num = 0
    for constraint in storage.constraints.values():
        if constraint.name != 'points_coincidence_constraint':
            lam_num += 1
        else:
            lam_num += 2
    return lam_num


def get_coords(storage, storage_to_matrix, lam_num):
    coords_vector = [1.] * lam_num

    # get current points position
    for point_id in storage_to_matrix.keys():
        coords_vector.append(storage.points[point_id].x())
        coords_vector.append(storage.points[point_id].y())
    return coords_vector


def get_point_indexes(storage, constraint_id):
    constraints = storage.constraints
    constraint_point_indexes = []
    # at first line objects
    for object in constraints[constraint_id].objects:
        if object['type'] == 'line':
            p1_id = storage.lines[object['obj']]['p1_id']
            p2_id = storage.lines[object['obj']]['p2_id']
            constraint_point_indexes.append(p1_id)
            constraint_point_indexes.append(p2_id)
    # then point objects
    for object in constraints[constraint_id].objects:
        if object['type'] == 'point':
            p_id = object['obj']
            constraint_point_indexes.append(p_id)
    return constraint_point_indexes


def get_indices_mappings(storage):
    storage_to_matrix = {}
    matrix_to_storage = {}
    lam_num = 0
    all_ids = []
    for constraint_id in storage.constraints:
        if storage.constraints[constraint_id].name != 'points_coincidence_constraint':
            lam_num += 1
        else:
            lam_num += 2

        all_ids.extend(get_point_indexes(storage, constraint_id))
    all_ids = [*set(all_ids)]
    for matr_id, storage_id in enumerate(all_ids):
        if storage_id not in storage_to_matrix:
            matrix_to_storage[matr_id] = storage_id
            storage_to_matrix[storage_id] = matr_id
    return storage_to_matrix, matrix_to_storage


def get_jf_func(storage, coords_vector, storage_to_matrix, lam_num, start_delta_x):
    J = np.zeros((len(coords_vector), len(coords_vector)))
    F = np.zeros(len(coords_vector))

    constraints = storage.constraints
    lamdas_counter = 0

    # for each constraint
    for constraint_id in constraints:
        # global indexes list
        constraint_coord_indexes = []

        # find global indexes of lam for this constraint
        if constraints[constraint_id].name != 'points_coincidence_constraint':
            constraint_coord_indexes.append(lamdas_counter)
            lamdas_counter += 1
        else:
            constraint_coord_indexes.append(lamdas_counter)
            constraint_coord_indexes.append(lamdas_counter + 1)
            lamdas_counter += 2

        # find global indexes of x, y for this constraint
        constraint_point_indexes = get_point_indexes(storage, constraint_id)
        for point_index in constraint_point_indexes:
            constraint_coord_indexes.append(lam_num + storage_to_matrix[point_index] * 2)  # x
            constraint_coord_indexes.append(lam_num + storage_to_matrix[point_index] * 2 + 1)  # y

        # find coords for this constraint
        # TODO: иногда при наложении ограничения здесь list index out of range
        local_coords_vector = [coords_vector[index] for index in constraint_coord_indexes]
        local_start_delta_x = [start_delta_x[index] for index in constraint_coord_indexes]

        # find local J, F
        local_J = []
        local_F = []
        # in angle and dist constraints we add as second argument (dist or angle) - constraints[constraint_id].value
        if constraints[constraint_id].name == 'points_coincidence_constraint':
            local_J, local_F = get_points_coincidence_constraint(local_coords_vector, local_start_delta_x)
        if constraints[constraint_id].name == 'points_dist_constraint':
            local_J, local_F = get_points_dist_constraint(local_coords_vector, constraints[constraint_id].value,
                                                          local_start_delta_x)
        if constraints[constraint_id].name == 'parallel_constraint':
            local_J, local_F = get_parallel_constraint(local_coords_vector, local_start_delta_x)
        if constraints[constraint_id].name == 'perpendicular_constraint':
            local_J, local_F = get_perpendicular_constraint(local_coords_vector, local_start_delta_x)
        if constraints[constraint_id].name == 'angle_constraint':
            local_J, local_F = get_angle_constraint(local_coords_vector, constraints[constraint_id].value,
                                                    local_start_delta_x)
        if constraints[constraint_id].name == 'horizontal_constraint':
            local_J, local_F = get_horizontal_constraint(local_coords_vector, local_start_delta_x)
        if constraints[constraint_id].name == 'vertical_constraint':
            local_J, local_F = get_vertical_constraint(local_coords_vector, local_start_delta_x)
        if constraints[constraint_id].name == 'point_belongs_line_constraint':
            local_J, local_F = get_point_belongs_line_constraint(local_coords_vector, local_start_delta_x)

        # add local J, F to global J, F
        # we know global indexes: constraint_coord_indexes
        for i in range(len(local_F)):
            F[constraint_coord_indexes[i]] += local_F[i]

        for i in range(len(local_J)):
            for j in range(len(local_J)):
                J[constraint_coord_indexes[i]][constraint_coord_indexes[j]] += local_J[i][j]

    return J, F


def update_coords_in_storage(storage, coords_vector, lam_num, matrix_to_storage):
    for matrix_id, storage_id in matrix_to_storage.items():
        storage.points[storage_id].setX(coords_vector[lam_num + matrix_id * 2])
        storage.points[storage_id].setY(coords_vector[lam_num + matrix_id * 2 + 1])


def recalculate_point_positions(storage):
    lam_num = get_lam_num(storage)
    storage_to_matrix, matrix_to_storage = get_indices_mappings(storage)
    coords_vector = get_coords(storage, storage_to_matrix, lam_num)
    start_delta_x = [0.] * len(coords_vector)
    for i in range(lam_num):
        start_delta_x[i] = 1.
    get_jf = partial(get_jf_func, storage, coords_vector, storage_to_matrix, lam_num)
    try:
        deltas = newtons_method(get_jf, start_delta_x)
    except np.linalg.LinAlgError as e:
        raise RuntimeError('Ограничение не добавлено. Возможно, ограничения несовместимы!')
    coords_vector += deltas
    # update point coords in storage
    update_coords_in_storage(storage, coords_vector, lam_num, matrix_to_storage)
