import sys

sys.path.append("..")
from importall import *

eNorm = False


def init_variables(args_):
    in_ = Inputs()
    in_.tmax = args_.tmax
    in_.prec = args_.prec
    in_.datapath = args_.datapath
    in_.outdir = args_.outdir
    in_.massNorm = args_.mpi
    in_.num_boot = args_.nboot
    in_.sigma = args_.sigma
    in_.emax = args_.emax * args_.mpi   #   we pass it in unit of Mpi, here to turn it into lattice (working) units
    if args_.emin == 0:
        in_.emin = args_.mpi / 20   #TODO get this to be input in lattice units for consistence
    else:
        in_.emin = args_.emin
    in_.e0 = args_.e0
    in_.Ne = args_.ne
    in_.alpha = args_.alpha
    return in_


def main():
    print(LogMessage(), "Initialising")
    args = parseArgumentRhoFromData()
    init_precision(args.prec)
    par = init_variables(args)

    #   Reading datafile, storing correlator
    rawcorr, par.time_extent, par.num_samples = u.read_datafile(par.datapath)
    par.assign_values()
    par.report()
    tmax = par.tmax
    adjust_precision(par.tmax)
    #   Here is the correlator
    rawcorr.evaluate()

    #   Here is the resampling
    corr = u.Obs(par.time_extent, par.num_boot, tmax_=par.tmax, is_resampled=True)
    resample = ParallelBootstrapLoop(par, rawcorr.sample)
    corr.sample = resample.run()
    corr.evaluate()

    print(LogMessage(), "Evaluate covariance")
    corr.evaluate_covmatrix(plot=False)
    corr.corrmat_from_covmat(plot=False)

    #   make it into a mp sample
    print(LogMessage(), "Converting correlator into mpmath type")
    #mpcorr_sample = mp.matrix(par.num_boot, tmax)
    corr.fill_mp_sample()
    cNorm = mpf(str(corr.central[1] ** 2))

    #   Prepare
    S = Smatrix_mp(tmax)
    lambda_bundle = LambdaSearchOptions(lmin = 0.01, lmax = 0.99, ldensity = 20, kfactor = 0.08, star_at = 1)
    matrix_bundle = MatrixBundle(Smatrix=S, Bmatrix=corr.mpcov, bnorm=cNorm)
    #   Wrapper for the Inverse Problem
    HLT = InverseProblemWrapper(par=par, lambda_config=lambda_bundle, matrix_bundle=matrix_bundle, correlator=corr)
    HLT.prepareHLT()
    HLT.init_float64()

    if(0):  #   select library for linear algebra
        for e_i in range(HLT.par.Ne):
            HLT.computeMinimumPrecision(HLT.espace[e_i])

    HLT.run(show_lambda_scan=True)

    if(0):'''

    for e_i in range(HLT.par.Ne):   # finds solution at a specific lambda
        HLT.optimal_lambdas[e_i][0] = HLT.solveHLT_bisectonSearch_float64(HLT.espace[e_i], k_factor=lambda_bundle.k_star)

    for e_i in range(HLT.par.Ne):   # finds solution at another lambda
        HLT.optimal_lambdas[e_i][1] = HLT.solveHLT_bisectonSearch_float64(HLT.espace[e_i], k_factor=lambda_bundle.kfactor)

    HLT.optimal_lambdas_is_filled = True
    assert all(HLT.result_is_filled)

    HLT.estimate_sys_error()    #   uses both solution to estimate systematics due to lambda

    for e_i in range(HLT.par.Ne):
        HLT.solveHLT_fromLambdaList_float64(HLT.espace[e_i])'''

    import matplotlib.pyplot as plt

    plt.errorbar(
        x=HLT.espace / par.massNorm,
        y=HLT.rho,
        yerr=HLT.rho_stat_err,
        marker="o",
        markersize=1.5,
        elinewidth=1.3,
        capsize=2,
        ls="",
        label="Stat error only (sigma = {:2.2f} Mpi)".format(par.sigma / par.massNorm),
        color=u.CB_color_cycle[0],
    )
    plt.errorbar(
        x=HLT.espace / par.massNorm,
        y=HLT.rho,
        yerr=HLT.rho_sys_err,
        marker="o",
        markersize=1.5,
        elinewidth=1.3,
        capsize=2,
        ls="",
        label="Sys error only (sigma = {:2.2f} Mpi)".format(par.sigma / par.massNorm),
        color=u.CB_color_cycle[1],
    )
    plt.errorbar(
        x=HLT.espace / par.massNorm,
        y=HLT.rho,
        yerr=HLT.rho_quadrature_err,
        marker="o",
        markersize=1.5,
        elinewidth=1.3,
        capsize=2,
        ls="",
        label="Quadrature sum (sigma = {:2.2f} Mpi)".format(par.sigma / par.massNorm),
        color=u.CB_color_cycle[2],
    )

    plt.xlabel("Energy/Mpi", fontdict=u.timesfont)
    plt.ylabel("Spectral density", fontdict=u.timesfont)
    plt.legend(prop={"size": 12, "family": "Helvetica"})
    plt.grid()
    plt.tight_layout()
    plt.show()

    #   ciao!
    end()

if __name__ == "__main__":
    main()