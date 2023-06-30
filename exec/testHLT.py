import sys

sys.path.append("..")
from importall import *

eNorm = False

#TODO at present: float implemented, mp not implemented


def init_variables(args_):
    in_ = Inputs()
    in_.tmax = args_.tmax
    in_.periodicity = args_.periodicity
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
    corr = u.Obs(T = par.time_extent, tmax = par.tmax, nms = par.num_boot, is_resampled=True)
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
    S = Smatrix_mp(tmax, type=par.periodicity, T=par.time_extent)
    lambda_bundle = LambdaSearchOptions(lmin = 0.01, lmax = 0.99, ldensity = 20, kfactor = 0.1, star_at = 1)
    matrix_bundle = MatrixBundle(Smatrix=S, Bmatrix=corr.mpcov, bnorm=cNorm)
    #   Wrapper for the Inverse Problem
    HLT = HLTWrapper(par=par, lambda_config=lambda_bundle, matrix_bundle=matrix_bundle, correlator=corr)
    HLT.prepareHLT()

    estar = HLT.espace[3]

    rho_l, drho_l, gag_l = HLT.scanLambda(estar)

    _ = HLT.estimate_sys_error(estar)

    assert(HLT.result_is_filled[3] == True)
    print(LogMessage(), 'rho, drho, sys', HLT.rho_result[3], HLT.drho_result[3],HLT.rho_sys_err[3])

    import matplotlib.pyplot as plt

    plt.errorbar(
        x=gag_l,
        y=rho_l,
        yerr=drho_l,
        marker="o",
        markersize=1.5,
        elinewidth=1.3,
        capsize=2,
        ls="",
        label=r'$\rho(E_*)$'+r'$(\sigma = {:2.2f})$'.format(par.sigma / par.massNorm)+r'$M_\pi$',
        color=u.CB_color_cycle[0],
    )
    plt.xlabel(r"$A[g_\lambda] / A_0$", fontdict=u.timesfont)
    #plt.ylabel("Spectral density", fontdict=u.timesfont)
    plt.legend(prop={"size": 12, "family": "Helvetica"})
    plt.grid()
    plt.tight_layout()

    plt.show()





    end()

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