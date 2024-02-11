import sys


import lattice-inverse-problem.rhoUtils as u
from lattice-inverse-problem.rhoUtils import init_precision
from lattice-inverse-problem.rhoUtils import LogMessage
from lattice-inverse-problem.rhoUtils import end
from lattice-inverse-problem.rhoUtils import Obs
from lattice-inverse-problem.rhoUtils import adjust_precision
from lattice-inverse-problem.rhoUtils import Inputs
from lattice-inverse-problem.rhoUtils import *
from lattice-inverse-problem.rhoStat import *
from lattice-inverse-problem.rhoMath import *
from lattice-inverse-problem.core import *
from lattice-inverse-problem.rhoParser import *
from lattice-inverse-problem.transform import *
from lattice-inverse-problem.abw import *
from lattice-inverse-problem.rhoParallelUtils import *
from lattice-inverse-problem.HLT_class import *
from lattice-inverse-problem.GPHLT_class import *
from lattice-inverse-problem.GP_class import *
from lattice-inverse-problem.correlatorUtils import foldPeriodicCorrelator
from lattice-inverse-problem.correlatorUtils import symmetrisePeriodicCorrelator
from mpmath import mp, mpf
from lattice-inverse-problem.InverseProblemWrapper import *
from lattice-inverse-problem.plotutils import *


import time

def integrate_exponential(alpha, s, t1,t2, E0, periodicity, T, precision):
    delta_x = 1e-3
    integral = 0.0

    x = E0
    while True:
        integral = mp.fadd(integral, integrandSigmaMat_DEBUG(x, alpha, s, t1, t2, E0, periodicity, T) * delta_x)
        x += delta_x

        if integrandSigmaMat_DEBUG(x, alpha, s, t1, t2, E0, periodicity, T) < precision:
            break

    return integral


def main():
    mp.dps = 120

    start = time.time()
    integral = mp.quad(lambda x: integrandSigmaMat_DEBUG(x, 0, s=0.1, t1=3, t2=3, E0=0, periodicity='COSH', T=16),
                       [0, mp.inf], error=True, method='tanh-sinh')
    end=time.time()
    print(LogMessage(), float(integral[0]), "in ", end-start, "s")

    start = time.time()
    integral = integrate_exponential(alpha=0, s=0.1, t1=3,t2=3, E0=0, periodicity='COSH', T=16, precision=1e-20)
    end=time.time()
    print(LogMessage(), float(integral), "in ", end-start, "s")

    exit(1)


if __name__ == "__main__":
    main()