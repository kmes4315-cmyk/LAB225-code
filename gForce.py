import numpy as np
from gOCmethod import SurfIndex, h2c, psiSign, xieta2X
from gCalculator import rhoSet, EeffSet, rhodScaleTerm, WmpSet, njdSet
from gDisturbance import x0mu_x1, dSolver
IPs, OPs, ctrl = {}, {}, {} #changed by main program
# =============================================================================
# force
# =============================================================================
def operate(order, var, i):
    return np.matmul(OPs['PD']['O'][order][i], var)
def FZset_1D(phid, psi):
    def FDZset_1D():
        psiS = psi['O'][iS]
        DpsiS = operate(order=10, var=psi['O'], i=iS)
        R2_Dn_E2psi_R2 = operate(order='R2_Dn_E2_R2', var=psi['O'], i=iS)
        rhoe = rhoSet({j: OPs['nje']['O'][j][iS] \
                       for j in OPs['nje']['O'].keys()})
        if ctrl['Sys']['m']['AC']: wTerm = -1.0j*IPs['w']*IPs['Re']*DpsiS
        else: wTerm = 0.0
        # if ctrl['Sys']['m']['AC']: wTerm = -2.0j*IPs['w']*IPs['Re']*DpsiS #AC old program
        # else: wTerm = 0.0
        if ctrl['Sys']['m']['Gel'] and ctrl['BC'].get('tauDBB'):
            aldaTerm = -IPs['aldam']**2*(DpsiS-2.0*psiS)
        else:
            aldaTerm = 0.0
        FDZ_pi = wTerm+aldaTerm+rhoe*phidS+R2_Dn_E2psi_R2
        return FDZ_pi*piFactor
    def FEZset_1D():
        DphiDne = operate(order=10, var=OPs['phie']['O'], i=iS)
        DphiDnd = operate(order=10, var=phid['O'], i=iS)
        FEZ_pi = DphiDne*(DphiDnd+2.0*phidS)
        return FEZ_pi*piFactor
    iS = SurfIndex(Nx=IPs['ND']['nO'], Nt=IPs['ND']['O'], sphere=True)
    phidS = phid['O'][iS]
    piFactor = 4.0/3.0*np.pi
    # print(FDZset_1D(), FEZset_1D())
    return FDZset_1D()+FEZset_1D()
def FZset_2D(phid, psi, njd):
    def DphidDnsSet(order):
        if order==1: ns='s'
        elif order==10: ns='n'
        DphidDns = operate(order=order, var=phid['O'], i=iS)
        if bis:
            DZDns = OPs['gradZ']['O'][ns][iS]/OPs['h']['O'][ns][iS]
            return DphidDns-EeffSet(IPs['nj0'])*DZDns
        else:
            return DphidDns
    def dFDZ_2Dset():
        # parameters
        rhoe = rhoSet({j: OPs['nje']['O'][j][iS] \
                       for j in OPs['nje']['O'].keys()})
        rhod = rhoSet({j: njd['O'][j][iS] \
                       for j in njd['O'].keys()})
        rhod = rhod+(rhodScaleTerm('O')[iS] if bis else 0.0)
        sign = psiSign[bis]
        DpsiS = operate(order='1_X' if bis else 1, var=psi['O'], i=iS)
        psiS = psi['O'][iS]
        if ctrl['Sys']['m']['AC']: wTerm = -1.0j*IPs['w']*IPs['Re']*R*DpsiS
        else: wTerm = 0.0
        if ctrl['Sys']['m']['Gel'] and ctrl['BC'].get('tauDBB'):
            if bis: DRDn = -OPs['gradZ']['O']['s'][iS]/OPs['hn']['O'][iS]
            else: DRDn = sin_s
            aldaTerm = -IPs['aldam']**2*(R*DpsiS-2.0*DRDn*psiS)
        else:
            aldaTerm = 0.0
        rhoTerm = -R**2/sign*(rhoe*DphidDs+rhod*DphieDs)
        E2term = np.matmul(OPs['PD']['O']['R3_Dn_E2_R2_surf'], psi['O'])
#        print(np.matmul(OPs['PD']['O']['Int_s_surf'], E2term)) #debug
#        print(np.matmul(OPs['PD']['O']['Int_s_surf'], rhoTerm)) #debug
        dFDZ_pi = wTerm+aldaTerm+rhoTerm+E2term
        return sign*dFDZ_pi*np.pi
    def dFEZ_2Dset():
        DphieDn = operate(order=10, var=OPs['phie']['O'], i=iS)
        DphidDn = DphidDnsSet(10)
        phiephid = {'nn-ss': DphieDn*DphidDn-DphieDs*DphidDs, \
                    'sn+ns': DphieDs*DphidDn+DphieDn*DphidDs}
        if ctrl['Sys']['major']=='b':
            # cosh(eta[iS]) = h, sinh(eta[iS]) = c
            Coefficient = {'nn-ss': (IPs['h']*cos_s-1.0)/c, 'sn+ns': sin_s}
        elif ctrl['Sys']['major']=='c':
            Coefficient = {'nn-ss': cos_s, 'sn+ns': -sin_s}
        dFEZ_pi = R*sum(Coefficient[i]*phiephid[i] for i in ('nn-ss', 'sn+ns'))
        return dFEZ_pi*2.0*np.pi
    bis = ctrl['Sys']['major']=='b'
    iS = SurfIndex(Nx=IPs['ND']['nO'], Nt=IPs['ND']['O'], sphere=not bis)
    R = OPs['R']['O'][iS]
    cos_s, sin_s = (cs(OPs['s']['O'][iS]) for cs in (np.cos, np.sin))
    if ctrl['Sys']['major']=='b': c = h2c(IPs['h'])
    DphieDs = operate(order=1, var=OPs['phie']['O'], i=iS)
    DphidDs = DphidDnsSet(1)
    # print(np.matmul(OPs['PD']['O']['Int_s_surf'], dFDZ_2Dset())) #debug
    # print(np.matmul(OPs['PD']['O']['Int_s_surf'], dFEZ_2Dset())) #debug
    return np.matmul(OPs['PD']['O']['Int_s_surf'], dFDZ_2Dset()+dFEZ_2Dset())
# =============================================================================
# mobility
# =============================================================================
def FZset():
    if ctrl['Sys']['major']=='a':
        if ctrl['Do']['a']['psiEq3']: return np.array([0.0, 0.0])
        else: return FZset_1D(phid=OPs['phid'], psi=OPs['psi'])
    else:
        return FZset_2D(phid=OPs['phid'], psi=OPs['psi'], njd=OPs['njd'])
def muSet():
    if ctrl['Sys']['major']=='a':
        if ctrl['Do']['a']['psiEq3']: return FlowFieldMethod()
        else: return subProblemMethod()
    else:
        return subProblemMethod()
def accelerationTermSet():
    if ctrl['Sys']['m']['AC']:
        return -4.0/3.0*np.pi*1.0j*IPs['w']*IPs['Re']*IPs['density']
        #return -4.0/3.0*np.pi*1.0j*IPs['w']*IPs['Re']*(IPs['density']-1.0) #AC old program
    else:
        return 0.0
def subProblemMethod():
    return -OPs['FZ'][0, 1]/(OPs['FZ'][0, 0]+accelerationTermSet())
def FlowFieldMethod():
    iO = SurfIndex(Nx=IPs['ND']['nO'], Nt=IPs['ND']['O'], \
                   sphere=True, outer=True)
    ro = OPs['n']['O'][iO]
    if ctrl['Sys']['OB']['Cell']:
        LHS = 2.0/ro**2*OPs['PD']['O'][0][iO]
    else:
        PD = {i: OPs['PD']['O'][i][iO] for i in (0, 10, 20)}
        Wmro_1 = WmpSet(False)*ro+1.0
        term1 = Wmro_1/ro*PD[10]
        term0 = (Wmro_1-2.0)/ro**2*PD[0]
        LHS = (PD[20]+term1+term0)/1.5/Wmro_1
    return np.matmul(LHS, OPs['psi']['O'][:, 1]).item()
# =============================================================================
# dipole coefficient
# =============================================================================
def KcmSet():
    if ctrl['Sys']['major']=='a':
        iO = SurfIndex(Nx=IPs['ND']['nO'], Nt=IPs['ND']['O'], \
                       sphere=True, outer=True)
        ro = OPs['n']['O'][iO]
        phidO = x0mu_x1(OPs['phid']['O'][iO])
        CMfactor = (phidO+ro)*ro**2
    elif ctrl['Sys']['major']=='b': #(real work?)
        iO = [-2]
        eta, xi = OPs['n']['O'][iO], OPs['s']['O'][iO]
        phidO = x0mu_x1(OPs['phid']['O'][iO])
        sqrtX = np.sqrt(xieta2X(eta=eta, xi=xi))
        sqrt_cosheta_cosxi = np.sqrt(np.cosh(eta)+np.cos(xi))
        r = h2c(IPs['h'])*sqrt_cosheta_cosxi/sqrtX
        cosq = np.sinh(eta)/sqrt_cosheta_cosxi/sqrtX
        if ctrl['BC']['conductive']['OB']: CMfactor = 0.5*phidO*r**2/cosq
        else: CMfactor = phidO*r**3/6.0/IPs['h']/cosq**2
    return complex(CMfactor)
# =============================================================================
# DEP mobility (real work?)
# =============================================================================
def muDEPset():
    wSave = IPs['w']
    IPs['w'] = 0.0
    gj, psi, phid = dSolver()
    njd = njdSet(phid=phid, gj=gj)
    if ctrl['Sys']['major']=='a': FZDC = FZset_1D(phid=phid, psi=psi)
    else: FZDC = FZset_2D(phid=phid, psi=psi, njd=njd)
    IPs['w'] = wSave
    return -2.0*np.pi*np.real(OPs['Kcm'])/np.real(FZDC[0, 0])