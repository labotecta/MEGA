from scipy.optimize import root, minimize
from scipy.optimize import minimize, NonlinearConstraint

def objective(x):
    x1, x2, x3 = x
    res = x1 + x2 + x3**2
    print('*** {:12.5e}      {:12.5e} {:12.5e} {:12.5e} **'.format(res, x1, x2, x3))
    return res

def eq1(x):
    x1, x2, x3 = x
    res = x1 - 1   # x = 1
    print(' 1: {:12.5e}      {:12.5e} {:12.5e} {:12.5e}'.format(res, x1, x2, x3))
    return res

def eq2(x):
    x1, x2, x3 = x
    res = x1**2 + x2**2 - 1  # x1**2 + x2**2 = 1
    print(' 2: {:12.5e}      {:12.5e} {:12.5e} {:12.5e}'.format(res, x1, x2, x3))
    return res

constraints = [{'type': 'eq', 'fun': eq1},
               {'type': 'eq', 'fun': eq2}]

minimize(objective, [0, 0, 0], constraints=constraints)
