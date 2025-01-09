import numpy as np

EPS = 1e-9
MAX_ITER = 10000
ERROR_MAX_ITER = "Превышено число итераций метода Ньютона"


def newtons_method(get_jf, start_v):
    k = 0
    cur_v = start_v
    while k < MAX_ITER:
        j_matrix, f_vector = get_jf(cur_v)
        try:
            delta_vector = np.linalg.solve(j_matrix, -f_vector)
        except np.linalg.LinAlgError as e:
            raise

        cur_v += delta_vector

        S = np.sqrt(np.sum(delta_vector ** 2))
        print('S = {}'.format(S))
        if S <= EPS:
            print('--------------------------------')
            return cur_v
        k = k + 1
    raise RuntimeError(ERROR_MAX_ITER)
