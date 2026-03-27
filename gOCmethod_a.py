import numpy as np
from gOCmethod import OCxySet, xy2ns, Dxy1D_HighSet, SurfIndex
NCOI = {'O': (slice(None), slice(None)), 'I': (slice(1, None), slice(None))}
# =============================================================================
# interface
# =============================================================================
def a_nsPDset(IPs, ctrl):
    if ctrl['Do']['a']['expGrid']: ratio=-1.5
    #point
    xOC = {'n'+OI: OCxySet(ND=IPs['ND']['n'+OI]) for OI in ctrl['Sys']['OI']}
    bound = {'nO': {'a': 1.0, 'b': IPs['ro']}}
    if 'I' in ctrl['Sys']['OI']:
        bound['nI'] = {'a': IPs['rc'], 'b': 1.0}
    r, theta, DxDr = {}, {}, {}
    for OI in ctrl['Sys']['OI']:
        nOI = 'n'+OI
        if ctrl['Do']['a']['expGrid'] and OI=='O':
            r[OI] = aExpGrid(xOC=xOC[nOI], ratio=ratio, **bound[nOI])
        else:
            r[OI], DxDr[OI] = xy2ns(xyOC=xOC[nOI], **bound[nOI])

        theta[OI] = np.reshape(np.linspace(0, np.pi, IPs['ND']['s']), \
                               (IPs['ND']['s'], 1))
    #differential matrix
    Dx = Dxy1D_HighSet(ND=IPs['ND'], xyOC=xOC, nMax=4)
    PD = {}
    for OI in ctrl['Sys']['OI']:
        nOI = 'n'+OI
        NnOI = IPs['ND'][nOI]
        if ctrl['Do']['a']['expGrid'] and OI=='O':
            PD[OI] = aPDbasicExpGrid(r=r[OI], Dx=Dx[nOI], Nn=NnOI, ratio=ratio)
        else:
            PD[OI] = aPDbasicSimple(Dx=Dx[nOI], Nn=NnOI, DxDr=DxDr[OI])
        aPDoperator(r=r[OI], PD=PD[OI], Nn=NnOI, ctrl=ctrl, OI=OI)
    return r, theta, PD
def aExpGrid(xOC, ratio, a, b):
    expRatio = np.exp(2.0*ratio)
    return a+(b-a)*(np.exp(ratio*(1.0-xOC))-expRatio)/(1.0-expRatio)
def aPDbasicExpGrid(r, Dx, Nn, ratio):
    expRatio = np.exp(2.0*ratio)
    c0 = (1.0-expRatio)/((r-1.0)*(1.0-expRatio)+(r[0]-1.0)*expRatio)
    temp = {1: -1.0, 2: 1.0, 3: -2.0, 4: 6.0}
    cc = {i: tempi/ratio*c0**i for i, tempi in temp.items()}
    cc12 = cc[1]**2
    PD = {0: np.identity(Nn)}
    PD[10] = cc[1]*Dx[1]
    PD[20] = cc12*Dx[2]+cc[2]*Dx[1]
    PD[30] = (cc12*cc[1])*Dx[3]+3.0*cc[2]*cc[1]*Dx[2]+cc[3]*Dx[1]
    temp = (4.0*cc[3]*cc[1]+3.0*cc[2]**2)*Dx[2]
    PD[40] = cc12**2*Dx[4]+6.0*cc[2]*cc12*Dx[3]+temp+cc[4]*Dx[1]
    return PD
def aPDbasicSimple(Dx, Nn, DxDr):
    PD = {0: np.identity(Nn)}
    PD.update({10*i: Dx[i]*DxDr**i for i in range(1, 5)})
    return PD
def aPDoperator(r, PD, Nn, ctrl, OI):
    def IL_operatorSet():
        PD['L4_r'] = PD[40]+4.0*PD[30]/r
        PD['Dr(L2_r)'] = PD[30]+Dr2_2r-Dr_2r2
        PD['Dr(L2)'] = PD['Dr(L2_r)']-Dr_2r2+4.0/r3*PD[0]
        PD['L4'] = PD['L4_r']-4.0*PD[20]/r2
    r2 = r**2
    r3, r4 = r2*r, r2**2
    D0_2r2 = 2.0/r2*PD[0]
    Dr_2r2 = 2.0/r2*PD[10]
    Dr2_2r = 2.0/r*PD[20]
    # Laplacian
    PD['L2_r'] = PD[20]+2.0/r*PD[10]
    # L2
    PD['L2'] = PD['L2_r']-D0_2r2
    # D2
    PD['E2'] = PD[20]-D0_2r2
    # D4
    PD['E4'] = PD[40]-4.0/r2*PD[20]+8.0/r3*PD[10]-8.0/r4*PD[0]
    # R2_Dn_E2_R2
    PD['R2_Dn_E2_R2'] = PD[30]-Dr2_2r-Dr_2r2+8.0/r3*PD[0]
    if ctrl['Sys']['m']['IL']: IL_operatorSet()
    return PD