import numpy as np
from functools import partial
from gOCmethod import xieta2X, VecAoVecB, VecAxVecB
from gEquilibrium import LcTermSet, OthersAreZeros, FC
from gEquilibrium import MatrixSolver, IterationSolver
from gCalculator import ka2_SumI0, Sum_nj_Set, rhoSet, nuTermSet
from gCalculator import WmpSet, UpSet, EeffSet, Dnjeff_zjnjSet
from gCalculator import rhodScaleTerm, njdSet
from gBCs import VarsBCs, gj2j
IPs, OPs, ctrl = {}, {}, {} #changed by main program
bis = {'O': False, 'I': False}
# =============================================================================
# interface
# =============================================================================
def dSolver():
    Names = ctrl['Sys']['dVars']
    #parameters
    global ka2, Eeff, lj, Up
    ka2 = ka2_SumI0()
    Up = UpSet()
    Eeff = EeffSet(IPs['nj0'])
    lj = nuTermSet()
    if ctrl['Sys']['major']=='b':
        global Dnjeff_zjnj0, bis
        bis['O'] = True
        Dnjeff_zjnj0 = {j: Dnjeff_zjnjSet(j=j, nj=IPs['nj0']) \
                       for j in IPs['nj0'].keys()}
    AB = {var: dVarsABset(var) for var in Names}
    if ctrl['Do']['dIter']:
        Initial = {var: np.ones(OPs['phie'][var[-1]].shape, \
                                FC[ctrl['Sys']['m']['AC']]) for var in Names}
        result = IterationSolver(Vars=Initial, AB=AB)
    else:
        result = MatrixSolver(AB=AB, Np=2)
    gjpsiphid = dPostTreatment(result)
    return gjpsiphid['gj'], gjpsiphid['psi'], gjpsiphid['phid']
# =============================================================================
# AB combination
# =============================================================================
def dVarsABset(var):
    # governing equation
    OI = var[-1]
    key = var[:-2]
    if key=='g':
        ABsub = gjEq(OI=OI, j=gj2j(var))
    elif key=='ps':
        if ctrl['Sys']['major']=='a':
            if ctrl['Do']['a']['psiEq3'] and OI=='O': ABsub = psiEq_3()
            else: ABsub = psiEq(OI)
        else:
            ABsub = psiEq(OI)
    elif key=='phi':
        ABsub = phidEq(OI)
    OthersAreZeros(ABsub=ABsub, Names=ctrl['Sys']['dVars'], PD=OPs['PD'])
    # boundary condition
    VarsBCs(ABsub=ABsub, Var=var)
    return ABsub
# =============================================================================
# post-treatment
# =============================================================================
def dPostTreatment(result):
    gjpsid = {'gj': {OI: {j: None for j in IPs['zj'].keys()} \
              for OI in ctrl['Sys']['OI']}}
    gjpsid.update({psid: {OI: None for OI in ctrl['Sys']['OI']} \
                   for psid in ('psi', 'phid')})
    resultVars = result.keys()
    for key, value in gjpsid.items():
        for OI, xOI in value.items():
            if isinstance(xOI, dict): #gj
                for j, gj in xOI.items():
                    gjOI = 'g'+str(j)+OI
                    if gjOI in resultVars: gjpsid['gj'][OI][j] = result[gjOI]
                    else: gjpsid['gj'][OI][j] = np.zeros((IPs['ND'][OI], 2))
            else: # psi phid
                psidOI = key+OI
                if psidOI in resultVars: gjpsid[key][OI] = result[psidOI]
                else: gjpsid[key][OI] = np.zeros((IPs['ND'][OI], 2))
    return gjpsid
# after calculation of mobility
def dModification():
    #gj
    for j in OPs['gj']['O'].keys():
        temp = Eeff-Dnjeff_zjnj0[j]
        OPs['gj']['O'][j] = OPs['gj']['O'][j]+temp*OPs['Z']['O']
    #psi
    X = xieta2X(eta=OPs['n']['O'], xi=OPs['s']['O'])
    X[-1] = ctrl['N']['tol']
    OPs['psi']['O'] = OPs['psi']['O']/X #+0.5*Up*OPs['R']['O']**2
    # if 'I' in OPs['psi'].keys():
    #     OPs['psi']['I'] = OPs['psi']['I']+0.5*Up*OPs['R']['I']**2
    #phid
    OPs['phid']['O'] = OPs['phid']['O']-Eeff*OPs['Z']['O']
    OPs['njd'] = njdSet(**{i: OPs[i] for i in ('phid', 'gj')})
# =============================================================================
# subproblem -> physical value
# =============================================================================
# (subproblem 1)*mu+(subproblem 2)
def x0mu_x1(x): return np.expand_dims(x[:, 0]*OPs['mu']+x[:, 1], axis=1)
def combination12():
    for key in ('gj', 'psi', 'phid', 'njd'):
        for OI, varOI in OPs[key].items():
            if isinstance(varOI, dict): # gj, njd
                for j, varOIj in varOI.items():
                    OPs[key][OI][j] = x0mu_x1(varOIj)
            else:
                OPs[key][OI] = x0mu_x1(varOI)
# =============================================================================
# gj Equation
# =============================================================================
def gjEq(OI, j):
    def gjACtermSet():
        if ctrl['Sys']['m']['AC']:
            ACterm = {0: lj[OI][j], j: 0.0}
            if ctrl['Sys']['m']['IL']:
                ACterm.update({i: -nu_zj*IPs['zj'][i]*OPs['nje'][OI][i] \
                               for i in IPs['zj'].keys()})
            ACterm[j] = ACterm[j]+1.0
            return {i: -iwPej*ACi*OPs['PD'][OI][0] \
                    for i, ACi in ACterm.items()}
        else:
            return {i: np.zeros(OPs['PD'][OI][0].shape, FC[False]) \
                    for i in (0, j)}
    def GradPhie_x_grad_R():
        if ctrl['Sys']['major']=='a':
            grad = {'n': 0.0, 's': 2.0*OPs['h'][OI]['s']*OPs['PD'][OI][0]}
        elif ctrl['Sys']['major'] in 'bc':
            if bis[OI]:
                grad = {'n': OPs['h'][OI]['n']*OPs['PD'][OI]['10_X'], \
                        's': OPs['h'][OI]['s']*OPs['PD'][OI]['1_X']}
            else:
                grad = OPs['grad'][OI]
        R = OPs['R'][OI].copy()
        R[abs(R)<ctrl['N']['tol']] = ctrl['N']['tol']
        return VecAxVecB(vecs=(OPs['grad(phie)'][OI], grad), plane=bis[OI])/R
    def gj_gjPart():
        GradPhie_o_grad = VecAoVecB(OPs['grad(phie)'][OI], OPs['grad'][OI])
        gradTerm = -IPs['zj'][j]*lj[OI][j]*GradPhie_o_grad
        return OPs['PD'][OI]['L2']+gradTerm+ACterm[j]
    def gj_Bpart():
        def AC_ZtermSet():
            if ctrl['Sys']['m']['IL']:
                nuTerm = nu_zj*sum(OPs['nje'][OI][i]*Dnjeff_zjnj0[i] \
                                   for i in IPs['zj'].keys())
            else:
                nuTerm = 0.0
            return -iwPej*(-Dnjeff_zjnj0[j]+nuTerm)*OPs['Z'][OI]
        if ctrl['BC']['infRef']:
            DZ_o_GradPhie = VecAoVecB(OPs['gradZ'][OI], OPs['grad(phie)'][OI])
            Bterm = 0.0
            if ctrl['BC']['infRef']: Bterm = -IPs['Pec'][j]*Up
            else: Bterm = 0.0
            if bis[OI] and ctrl['Sys']['m']['AC']: AC_RHS = AC_ZtermSet()
            else: AC_RHS = 0.0
            if bis[OI]: Bterm = Bterm+IPs['zj'][j]*(Eeff-Dnjeff_zjnj0[j])
            return Bterm*lj[OI][j]*DZ_o_GradPhie+AC_RHS
        else:
            return np.zeros((IPs['ND'][OI], 2), FC[ctrl['Sys']['m']['AC']])
    #-----parameters-----#
    if ctrl['Sys']['m']['AC']:
        iwPej = 1.0j*IPs['w']*IPs['Pec'][j]
        if ctrl['Sys']['m']['IL']: nu_zj = IPs['nu']/IPs['zj'][j]
    ACterm = gjACtermSet()
    gj = 'g'+str(j)+OI
    #-----gj equation-----#
    ABgj = {}
    ABgj[gj] = gj_gjPart()
    for i in set(ACterm.keys())-{0, j}: ABgj['g'+str(i)+OI] = ACterm[i]
    ABgj['psi'+OI] = IPs['Pec'][j]*lj[OI][j]*GradPhie_x_grad_R()
    ABgj['phid'+OI] = ACterm[0]
    ABgj['B'] = gj_Bpart()
    return ABgj
# =============================================================================
# psi Eq
# =============================================================================
def psiEq(OI):
    def psi_psiPart():
        # Note: E2 & E4 for plane are in fact E2_X & E4_X
        # calculated psi needs to /X
        if OI=='O': DBB = ctrl['Sys']['m']['Gel']
        elif OI=='I': DBB = (ctrl['Sys']['p'] in 'GPSM')##########GPSM or PSM
        if DBB or ctrl['Sys']['m']['AC']:
            E2term = WmpSet(OI=='I')**2*OPs['PD'][OI]['E2']
        else:
            E2term = 0.0
        if ctrl['Sys']['p']+OI in ('DI', 'GI'): vis = IPs['vis']
        else: vis = 1.0
        return vis*(OPs['PD'][OI]['E4']-E2term)
    def psi_Bset():
        if bis[OI]:
            SumI = Sum_nj_Set(nj=OPs['nje'][OI], order=2)
            if ctrl['Sys']['m']['IL']:
                SumR = Sum_nj_Set(nj=OPs['nje'][OI], order=1)
                nuTerm = IPs['nu']*SumR**2*Eeff
            else:
                nuTerm = 0.0
            if ctrl['Sys']['m']['Diffu']:
                temp = {i: Dnjeff_zjnj0[i]*lj['O'][i]*nje \
                        for i, nje in OPs['nje']['O'].items()}
                SumDnjeff = Sum_nj_Set(nj=temp, order=2)
            else:
                SumDnjeff = 0.0
            xTerm = VecAxVecB_bis((OPs['grad(phie)'][OI], OPs['gradZ'][OI]))
            return Rka2*((SumI-nuTerm)*Eeff-SumDnjeff)*xTerm
        else:
            return np.zeros((IPs['ND'][OI], 2), FC[ctrl['Sys']['m']['AC']])
    VecAxVecB_bis = partial(VecAxVecB, plane=bis[OI])
    #-----parameters-----#
    Rka2 = ka2*OPs['R'][OI]
    #-----psi equation-----#
    ABpsi = {}
    if OI=='O' or ctrl['Sys']['p'] in 'PSM':
        xTerm = Rka2*VecAxVecB_bis((OPs['grad(phie)'][OI], OPs['grad'][OI]))
        for i, zi in IPs['zj'].items():
            ABpsi['g'+str(i)+OI] = -zi**2*OPs['nje'][OI][i]*lj[OI][i]*xTerm
    ABpsi['psi'+OI] = psi_psiPart()
    ABpsi['B'] = psi_Bset()
    return ABpsi
def psiEq_3():
    def psi_phidPart():
        Dr_2_r_D0 = OPs['PD']['O'][10]+Two_r*OPs['PD']['O'][0]
        if ctrl['Sys']['m']['IL']:
            temp = OPs['PD']['O']['Dr(L2)']+Two_r*OPs['PD']['O']['L2']
            DphieTerm = OPs['grad(phie)']['O']['n']*temp
            DrL2phie = np.matmul(OPs['PD']['O']['Dr(L2_r)'], OPs['phie']['O'])
            L2phie = np.matmul(OPs['PD']['O']['L2_r'], OPs['phie']['O'])
            L2phieTerm = DrL2phie*Dr_2_r_D0-L2phie*OPs['PD']['O']['L2']
            LcTerm = -(IPs['kaLc']/IPs['ka'])**2*(DphieTerm+L2phieTerm)
        else:
            LcTerm = 0.0
        rhoeTerm = rhoSet(OPs['nje']['O'])*OPs['PD']['O'][0]
        return OPs['grad(phie)']['O']['n']*Dr_2_r_D0+rhoeTerm+LcTerm
    #[only vaild for 1D DC 1 region Newtonian system]
    Two_r = 2.0/OPs['n']['O']
    if ctrl['Sys']['m']['Gel']:
        Dr_2_r_D0 = OPs['PD']['O'][10]-Two_r*OPs['PD']['O'][0]
        aldaTerm = -IPs['aldam']**2*Dr_2_r_D0
    else:
        aldaTerm = 0.0
    ABpsi = {}
    ABpsi['psiO'] = OPs['PD']['O']['R2_Dn_E2_R2']+aldaTerm
    ABpsi['phidO'] = psi_phidPart()
    ABpsi['B'] = np.zeros((IPs['ND']['O'], 2), FC[False])
    return ABpsi
# =============================================================================
# phid Eq
# =============================================================================
def phidEq(OI):
    def phid_gjPart(j):
        nuTerm = IPs['nu']*IPs['zj'][j]*SumR if ctrl['Sys']['m']['IL'] else 0.0
        return -ka2*(IPs['zj'][j]**2-nuTerm)*OPs['nje'][OI][j]*OPs['PD'][OI][0]
    def phid_phidPart():
        if ctrl['Sys']['m']['IL']:
            LcTerm = LcTermSet(PD=OPs['PD'], OI=OI)
            nuTerm = ka2*IPs['nu']*SumR**2*OPs['PD'][OI][0]
        else:
            LcTerm, nuTerm = 0.0, 0.0
        SumI = Sum_nj_Set(nj=OPs['nje'][OI], order=2)
        return OPs['PD'][OI]['L2']-LcTerm-ka2*SumI*OPs['PD'][OI][0]+nuTerm
    def phid_Bpart():
        if bis[OI] and ctrl['Sys']['m']['Diffu']: return -rhodScaleTerm(OI)
        else: return np.zeros((IPs['ND'][OI], 2), FC[ctrl['Sys']['m']['AC']])
    if ctrl['Sys']['m']['IL']: SumR = Sum_nj_Set(nj=OPs['nje'][OI], order=1)
    ABphid = {}
    for j in IPs['zj'].keys(): ABphid['g'+str(j)+OI] = phid_gjPart(j)
    ABphid['phid'+OI] = phid_phidPart()
    ABphid['B'] = phid_Bpart()
    return ABphid

