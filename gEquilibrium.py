import numpy as np
from functools import partial
from gBegin import MaxRavelAbs, KeyDelete
from gBCs import VarsBCs
from gCalculator import ka2_SumI0, njeSet, Sum_nj_Set, rhoFixModify
IPs, OPs, ctrl = {}, {}, {} #changed by main program
FC = {True: 'complex128', False: 'float64'}
# =============================================================================
# interface
# =============================================================================
def eSolver():
    PD = {}
    rType = lambda x: x+('_r' if ctrl['Sys']['major']=='a' else '')
    for OI in ctrl['Sys']['eVars']:
        PD[OI] = {0: OPs['PD'][OI][0], 'L2':  OPs['PD'][OI][rType('L2')]}
        if ctrl['Sys']['m']['IL']: PD[OI]['L4'] = OPs['PD'][OI][rType('L4')]
    phie = phieSolver(PD=PD, BCf=VarsBCs, Names=ctrl['Sys']['eVars'])
    return ePostTreatment(phie)
def ePostTreatment(phie):
    nje, grad_phie = {}, {}
    for OI in ctrl['Sys']['OI']:
        if OI in ctrl['Sys']['eVars']:
            nje[OI] = njeSet(phie[OI])
        else:
            phie[OI] = IPs['zeta']*np.ones(OPs['n'][OI].shape)
            nje[OI] = {j: np.zeros(OPs['n'][OI].shape) \
                       for j in IPs['zj'].keys()}
        if ctrl['Sys']['major']=='a':
            grad_phie[OI] = {'n': np.matmul(OPs['grad'][OI]['n'], phie[OI]), \
                             's': np.zeros(phie[OI].shape)}
        elif ctrl['Sys']['major'] in 'bc':
            grad_phie[OI] = {ns: np.matmul(OPs['grad'][OI][ns], phie[OI]) \
                             for ns in 'ns'}
    return phie, nje, grad_phie
# =============================================================================
# phie solver (linear -> nonlinear)
# =============================================================================
def phieSolver(PD, BCf, Names):
    def phieIteration(phie):
        for nIter in range(ctrl['N']['Niter']):
            AB = {}
            for OI in phie.keys():
                BCs = BCsModify(phie[OI])
                Eq = partial(phieNonLinearEq, phie=phie)
                AB[OI] = phieABset(Eq=Eq, BCs=BCs, PD=PD, OI=OI, Names=Names)
            phieNew = MatrixSolver(AB=AB, Np=1)
            error = max(tuple(MaxRavelAbs(phieNew[OI]-phie[OI]) \
                              for OI in phie.keys()))
            if error<ctrl['N']['tol'] or np.isnan(error): break
            else: phie = phieNew
        ErrorTest(nIter=nIter, error=error, ctrlN=ctrl['N'])
        return phieNew
    BCsModify = lambda phieOI: partial(BCf, Phie=phieOI)
    if 'phie' in OPs.keys() and ctrl['Do']['e']['old->']:
        phie = OPs['phie'].copy() #MatrixSolver(AB=AB, Np=1)
    else:
        phie, AB = {}, {}
        for OI in Names:
            phie[OI] = np.zeros((OPs['PD'][OI][0].shape[0], 1))
            AB[OI] = phieABset(Eq=phieLinearEq, BCs=BCsModify(phie[OI]), \
                               PD=PD, OI=OI, Names=Names)
        phie = MatrixSolver(AB=AB, Np=1)
    if ctrl['Do']['e']['->NL']: phie = phieIteration(phie)
    return phie
# =============================================================================
# equations
# =============================================================================
def LcTermSet(PD, OI):
    if ctrl['Sys']['m']['IL']: return (IPs['kaLc']/IPs['ka'])**2*PD[OI]['L4']
    else: return 0.0
def phieLinearEq(PD, OI):
    LcTerm = LcTermSet(PD=PD, OI=OI)
    ka2 = IPs['ka']**2
    rhoFix = rhoFixModify(nje=IPs['nj0'], OI=OI)
    ABphie = {}
    ABphie[OI] = PD[OI]['L2']-LcTerm-ka2*PD[OI][0]
    ABphie['B'] = np.zeros((PD[OI][0].shape[0], 1), float)-rhoFix
    return ABphie
def phieNonLinearEq(PD, OI, phie):
    ka2 = ka2_SumI0()
    nje = njeSet(phie[OI])
    Sum_nje = {i: Sum_nj_Set(nj=nje, order=i) for i in (1, 2)}
    LcTerm = LcTermSet(PD=PD, OI=OI)
    nuTerm = IPs['nu']*Sum_nje[1]**2 if ctrl['Sys']['m']['IL'] else 0.0
    rhoFix = rhoFixModify(nje=nje, OI=OI)
    ABphie = {}
    ABphie[OI] = PD[OI]['L2']-LcTerm+ka2*(nuTerm-Sum_nje[2])*PD[OI][0] #+CR term for CR pouous
    F = np.matmul(PD[OI]['L2']-LcTerm, phie[OI])+ka2*Sum_nje[1]+rhoFix
    ABphie['B'] = np.matmul(ABphie[OI], phie[OI])-F
    return ABphie
# =============================================================================
# AB combination
# =============================================================================
def phieABset(Eq, BCs, PD, OI, Names):
    ABsub = Eq(PD=PD, OI=OI)
    OthersAreZeros(ABsub=ABsub, Names=Names, PD=PD)
    BCs(ABsub=ABsub, Var=OI)
    return ABsub
# =============================================================================
# matrix method
# =============================================================================
def PreconditionerSet(A):
    T = np.zeros(A.shape)
    for i in range(A.shape[0]):
        if A[i, i]!=0: T[i, i] = 1.0/A[i, i] # Jacobi preconditioner
        else: T[i, i] = 1.0
    return T
def MatrixSolver(AB, Np):
    Names = AB.keys()
    Id, Nt = IdNtSet(AB)
    DataType = FC[ctrl['Sys']['m']['AC'] and ('O' not in Names)]
    A, B = np.empty((Nt, Nt), DataType), np.empty((Nt, Np), DataType)
    for var in Names:
        for DM in Names: A[Id[var], Id[DM]] = AB[var][DM]
        B[Id[var]] = AB[var]['B']
    # ABtest(A, B)
    # testZero(A)
    # ABsumTest(A, B)
    # print(np.log10(np.linalg.cond(A)))
    if ctrl['Do']['preconditioner']:
        T = PreconditionerSet(A)
        A, B = np.matmul(T, A), np.matmul(T, B)
    result = np.linalg.solve(A, B)
    return {i: result[Id[i]] for i in Names}
# =============================================================================
# iteration method
# =============================================================================
def IterationSolver(Vars, AB):
    Names = AB.keys()
    def VarsNewSolver(Vars):
        VarsNew = {}
        for var in Names:
            B = 0.0
            for DM in Names:
                if var==DM: B = B+AB[var]['B']
                else: B = B-np.matmul(AB[var][DM], Vars[DM])
            # print(var, np.log10(np.linalg.cond(AB[var][var])))
            VarsNew[var] = np.linalg.solve(AB[var][var], B)
        return VarsNew
    for nIter in range(ctrl['N']['Niter']):
        VarsNew = VarsNewSolver(Vars)
        error = max({MaxRavelAbs(VarsNew[i]-Vars[i]) for i in Names})
        if error <= ctrl['N']['tol']: break
        else: Vars = VarsNew
    ErrorTest(nIter=nIter, error=error, ctrlN=ctrl['N'])
    return VarsNew
# =============================================================================
# other function
# =============================================================================
def IdNtSet(AB):
    Id, Nt = {}, 0
    for DM in AB.keys():
        NtNext = Nt+AB[DM][DM].shape[0]
        Id[DM] = slice(Nt, NtNext)
        Nt = NtNext
    return Id, Nt
def OthersAreZeros(ABsub, Names, PD):
    Nrow = ABsub['B'].shape[0]
    for DM in KeyDelete(DictKeys=Names, delKeys=ABsub.keys()):
        Ncolumn = PD[DM[-1]][0].shape[1]
        ABsub[DM] = np.zeros((Nrow, Ncolumn))
# =============================================================================
# convergence or not
# =============================================================================
def ErrorTest(nIter, error, ctrlN):
    if nIter < ctrlN['Niter']-1 and not np.isnan(error):
        print('convergence with {0:2.0e}'.format(ctrlN['tol']))
    elif error < 1e-1:
        print('convergence with 1e{0:2d}'.format(int(np.log10(error))))
    else:
        print('maximum error = {}'.format(error))
# =============================================================================
# debug
# =============================================================================
def testZero(A):
    ND = len(A)
    for i in range(ND):
        allzero=True
        for j in range(ND):
            if abs(A[i,j])>1e-12:
                allzero=False
                break
        if allzero: print(i,'zeros')
def ABtest(A, B):
    with open('test.txt','w') as test:
        AiLen, AjLen = A.shape
        for i in range(AiLen):
            for j in range(AjLen):
                test.write('{0} {1} {2} {3}\n'.format(i, j, A[i, j], B[i, 0]))
def ABsumTest(A, B):
    for i in range(4):
        print(sum(np.ravel(A[IPs['ND']['O']*i:IPs['ND']['O']*(i+1)])))
        print(sum(np.ravel(B[IPs['ND']['O']*i:IPs['ND']['O']*(i+1)])))
    # Nt = 4*IPs['ND']['O']
    # for i in range(1):
    #     print(sum(np.ravel(A[Nt+IPs['ND']['I']*i:Nt+IPs['ND']['I']*(i+1)])))
    #     print(sum(np.ravel(B[Nt+IPs['ND']['I']*i:Nt+IPs['ND']['I']*(i+1)])))
    #     for site in ('ax', 'p', 's'):
    #         print(site, sum(abs(np.ravel(A[IPs['ND']['O']*i+OPs['At']['O'][site]]))))
    #         print(site, sum(abs(np.ravel(B[IPs['ND']['O']*i+OPs['At']['O'][site]]))))
    #         print(site, sum(np.ravel(A[IPs['ND']['O']*i+OPs['At_1']['O'][site]])))
    #         print(site, sum(np.ravel(B[IPs['ND']['O']*i+OPs['At_1']['O'][site]])))