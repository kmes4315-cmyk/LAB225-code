import numpy as np
from gOCmethod import OCxySet, xy2ns, Dxy1D_HighSet
from gEquilibrium import phieSolver
from gCalculator import njeSet, rhoSet, EeffSet
from scipy.interpolate import splev, splrep
R2rq = lambda R, Rend, y: splev(x=Rend, tck=splrep(x=R[::-1], y=y[::-1]))
wall, axis = (0, slice(None)), (-1, slice(None))
wall_1, axis_1 = (1, slice(None)), (-2, slice(None))
nAx = (slice(0, -1), slice(None))
# =============================================================================
# interface
# =============================================================================
def EOFsolver(IPs, OPs, ctrl):
    R, PDR = RPDR(NR=IPs['NR'], Rw=IPs['ro0']['W'], IL=ctrl['Sys']['m']['IL'])
    phieoo = phieooSolver(IPs=IPs, ctrl=ctrl, PDR=PDR)
    vZoo = vZooSolver(IPs=IPs, phieoo=phieoo, ctrlSys=ctrl['Sys'], PDR=PDR)
    psioo = psiooSolver(vZoo=vZoo, R=R, PDR=PDR)
    return tuple({UD: R2rq(R=R, Rend=OPs['Rend'][UD], y=yi) \
                 for UD in OPs['Rend'].keys()} for yi in (phieoo, vZoo, psioo))
# =============================================================================
# R & PDR
# =============================================================================
def RPDR(NR, Rw, IL):
    def LaplacianSet():
        L2 = PDR[20].copy()
        L2[nAx] = L2[nAx]+PDR[10][nAx]/R[nAx]
        return L2
    def DrL2wallSet():
        return PDR[30][wall]+PDR[20][wall]/R[wall]-PDR[10][wall]/R[wall]**2
    def L4Set():
        L4 = PDR[40].copy()
        temp = 2.0*PDR[30][nAx]-PDR[20][nAx]/R[nAx]+PDR[10][nAx]/R[nAx]**2
        L4[nAx] = L4[nAx]+temp/R[nAx]
        return L4
    nMax = 4 if IL else 2
    xOC = OCxySet(ND=NR)
    R, DxDR = xy2ns(xyOC=xOC, a=0.0, b=Rw)
    DR = Dxy1D_HighSet(ND={'R': NR}, xyOC={'R': xOC}, nMax=nMax)
    PDR = {10*i: DR['R'][i]*DxDR**i for i in range(1, nMax+1)}
    PDR[0] = DR['R'][0]
    PDR['L2'] = LaplacianSet()
    if IL:
        PDR['DR(L2)_wall'] = DrL2wallSet()
        PDR['L4'] = L4Set()
    # PDR['Int_R'] = IntMxySet(NR)/DxDR*R[:,0]
    return R, PDR
# =============================================================================
# electric potential
# =============================================================================
def phieooSolver(IPs, ctrl, PDR):
    def phieooBCs(ABsub, Var, Phie=None):
        def phieooWallBC(DM):
            # phieoo (R = Rw) = zetaW
            if DM=='O': return PDR[0][wall]
            elif DM=='B': return IPs['zetaW']
        def phieooAxisBC(DM):
            # DphieooDR (R = 0) = 0
            if DM=='O': return PDR[10][axis]
            elif DM=='B': return 0.0
        def phieooAddWallBC(DM):
            if DM=='O':
                if ctrl['BC']['L3=L2']:
                    Lc2 = (IPs['kaLc']/IPs['ka'])**2
                    return Lc2*PDR['DR(L2)_wall']-PDR['L2']
                else:
                    return PDR['DR(L2)_wall']
            elif DM=='B':
                return 0.0
        def phieooAddAxisBC(DM):
            if DM=='O': return PDR[30][axis]
            elif DM=='B': return 0.0
        for DM in 'OB':
            ABsub[DM][wall] = phieooWallBC(DM)
            ABsub[DM][axis] = phieooAxisBC(DM)
            if ctrl['Sys']['m']['IL']:
                ABsub[DM][wall_1] = phieooAddWallBC(DM)
                ABsub[DM][axis_1] = phieooAddAxisBC(DM)
    phieoo = phieSolver(PD={'O': PDR}, BCf=phieooBCs, Names='O')['O']
    return phieoo
# =============================================================================
# flow field
# =============================================================================
def vZooSolver(IPs, phieoo, ctrlSys, PDR):
    def Aset():
        if ctrlSys['m']['Gel']: GelTerm = -IPs['aldam']**2*PDR[0]
        else: GelTerm = 0.0
        if ctrlSys['m']['AC']: ACterm = -1.0j*IPs['w']*IPs['Re']*PDR[0]
        else: ACterm = 0.0
        return PDR['L2']+GelTerm+ACterm
    def Bset():
        njeoo = njeSet(phieoo)
        Eeff = np.reshape(EeffSet(njeoo)[:, 1], phieoo.shape)
        return -rhoSet(njeoo)*Eeff
    def vZooBCs():
        nonlocal A, B
        A[wall] = PDR[0][wall] # R = Rw
        B[wall] = 0.0
        A[axis] = PDR[10][axis] # R = 0
        B[axis] = 0.0
    A, B = Aset(), Bset()
    vZooBCs()
    vZoo = np.linalg.solve(A, B)
    return vZoo
def psiooSolver(vZoo, R, PDR):
    A = PDR[10]
    B = -vZoo*R
    A[axis] = PDR[0][axis] # R = 0
    B[axis] = 0.0
    psioo = np.linalg.solve(A, B)
    return psioo





















