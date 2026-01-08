
def objective(x):
    x0,x1,x2,x3 = x
    return 0.6224*x0*x2*x3 + 1.7781*x1*x2**2 + 3.1661*x0**2*x3 + 19.84*x0**2*x2

bounds = [(0,1e6)]*4
# with penalty='penalty' applied, solution is:
xs = [0.72759093, 0.35964857, 37.69901188, 240.0]
ys = 5804.3762083

from mystic.symbolic import generate_constraint, generate_solvers, simplify
from mystic.symbolic import generate_penalty, generate_conditions

equations = """
-x0 + 0.0193*x2 <= 0.0
-x1 + 0.00954*x2 <= 0.0
-pi*x2**2*x3 - (4/3.)*pi*x2**3 + 1296000.0 <= 0.0
x3 - 240.0 <= 0.0
"""
cf = generate_constraint(generate_solvers(simplify(equations)))
pf = generate_penalty(generate_conditions(equations), k=1e12)


if __name__ == '__main__':

    from mystic.solvers import diffev2
    from mystic.math import almostEqual
    from mystic.monitors import VerboseMonitor
    mon = VerboseMonitor(10)

    result = diffev2(objective, x0=bounds, bounds=bounds, constraints=cf, penalty=pf, npop=40, gtol=50, disp=False, full_output=True, itermon=mon)

    assert almostEqual(result[0], xs, rel=1e-2)
    assert almostEqual(result[1], ys, rel=1e-2)
