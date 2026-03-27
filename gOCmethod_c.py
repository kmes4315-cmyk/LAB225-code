import numpy as np
from scipy.linalg import block_diag
from gOCmethod import OCxySet, xy2ns, IntMxySet, Dxy1D_HighSet, Dxy2Dset
from gOCmethod import PDbasic2D, sphericalPD_2D, SurfIndex, nAxIndex, delKeys
DWU = 'DWU'
# =============================================================================
# interface
# =============================================================================
def c_nsPDset(IPs, ctrl):
    def PDOset():
        #DxyUnit -> Dxy2D -> PD
        Dxy2D_O = Dxy2Dset(DxUnit=DxUnit['O'], DyUnit=DyUnit, \
                           Nx=IPs['ND']['nO'], Ny=IPs['ND']['s'])
        DxD, DyDq = cDiffFactors(r=rt['O'], Nx=IPs['ND']['nO'], varDWU=varDWU)
        PDO = cPDObasic(Dxy=Dxy2D_O, DxD=DxD, DyDq=DyDq) #(Nt, Nt)
        PDO['Int_s_surf'] = IntqM
        return PDO
    TwoR = 'I' in ctrl['Sys']['OI']
    xyOC = {'n'+OI: OCxySet(ND=IPs['ND']['n'+OI]) for OI in ctrl['Sys']['OI']} #Nxy x 1
    xyOC.update({'s'+i: OCxySet(ND=IPs['ND']['s'+i]) for i in DWU}) #Nxy x 1
    varDWU, IntqM = cVarDWUset(xyOC=xyOC, IPs=IPs)
    #-----points-----#
    #x -> r, y -> theta
    #outside
    theta = {'O': cThetaSet(qUnit=varDWU['q'], Nn=IPs['ND']['nO'])} #(Nt, 1)
    rt = {}
    rt['O'] = xy2ns(xyOC=np.tile(xyOC['nO'], (IPs['ND']['s'], 1)), a=1.0, \
               b=np.repeat(varDWU['ro'], IPs['ND']['nO'], axis=0))[0] #(Nt, 1)
    #inside
    if TwoR:
        theta['I'] = cThetaSet(qUnit=varDWU['q'], Nn=IPs['ND']['nI']) #(Nt, 1)
        rIunit, DxDrI = xy2ns(xyOC=xyOC['nI'], a=IPs['rc'], b=1.0) #(Nxy, 1),()
        rt['I'] = np.tile(rIunit, (IPs['ND']['s'], 1)) #(Nt, 1)
    #-----differential matrix-----#
    #Dxy1D -> DxyUnit
    DxUnit, DyUnit = cDxyUnitSet(ND=IPs['ND'], xyOC=xyOC, nMax=4) #(Nxy, Nxy)
    #DxyUnit -> PDbasic
    PD = {'O': PDOset()}
    if TwoR:
        PD['I'] = PDbasic2D(DxyUnit={'n': DxUnit['I'], 's': DyUnit}, \
                            DxyDns={'n': DxDrI, 's': varDWU['DyDq']}, \
                            Nxy={'n': IPs['ND']['nI'], 's': IPs['ND']['s']})
    #PDbasic -> PDoperators
    for OI in ctrl['Sys']['OI']:
        sphericalPD_2D(r=rt[OI], q=theta[OI], PD=PD[OI], ND=IPs['ND'], OI=OI, \
                       IL=ctrl['Sys']['m']['IL'])
        cPD_surf(q=theta[OI], PD=PD[OI], ND=IPs['ND'], OI=OI, ctrl=ctrl)
        delKeys(PD[OI])
    return rt, theta, PD
# =============================================================================
# points
# =============================================================================
# theta corresponding to corner
qCset = lambda Rw, L: np.arccos(L/np.sqrt(Rw**2+L**2))
# boundary of rO
def boundSet(ro0):
    qUW = qCset(Rw=ro0['W'], L=ro0['U'])
    qDW = qCset(Rw=ro0['W'], L=-ro0['D'])
    bound = {0: 0.0, 1: qUW, 2: qDW, 3: np.pi}
    return {'UWD'[i]: {'a': bound[i], 'b': bound[i+1]} for i in range(3)}
# some properties will be used
def cVarDWUset(xyOC, IPs):
    def thetaSurfIntM2():
        temp = tuple(IntMxySet(IPs['ND']['s'+i])/DyDqi[i] for i in DWU)
        IntM = np.concatenate(temp, axis=1)
        return IntM
    def cCombineDWU(ci):
        temp = tuple(ci[i]*np.ones((IPs['ND']['s'+i], 1)) for i in DWU)
        return np.concatenate(temp, axis=0)
    bound = boundSet(IPs['ro0'])
    qi, DyDqi = {}, {}
    for i in DWU:
        qi[i], DyDqi[i] = xy2ns(xyOC=xyOC['s'+i], **bound[i])
    varDWU = {}
    varDWU['q'] = np.concatenate(tuple(qi[i] for i in DWU), axis=0)
    varDWU['DyDq'] = cCombineDWU(DyDqi)
    temp = (np.cos(qi['D']), np.sin(qi['W']), np.cos(qi['U']))
    varDWU['fcs'] = np.concatenate(temp, axis=0)
    temp = (-np.sin(qi['D']), np.cos(qi['W']), -np.sin(qi['U']))
    varDWU['Dfcs'] = np.concatenate(temp, axis=0)
    temp = {i: IPs['ro0'][i] for i in DWU}
    temp['D'] = -temp['D']
    varDWU['ro0'] = cCombineDWU(temp)
    varDWU['ro'] = varDWU['ro0']/varDWU['fcs']
    return varDWU, thetaSurfIntM2()
# theta
def cThetaSet(qUnit, Nn): return np.repeat(qUnit, Nn, axis=0)
# =============================================================================
# differential matrix
# =============================================================================
# Dxy1D -> DxyUnit
def cDxyUnitSet(ND, xyOC, nMax):
    Dxy1D = Dxy1D_HighSet(ND=ND, xyOC=xyOC, nMax=nMax)
    DxUnit = {'O': Dxy1D['nO']}
    if 'nI' in Dxy1D.keys(): DxUnit['I'] = Dxy1D['nI']
    DyUnit = {j: block_diag(*(Dxy1D['s'+i][j] for i in DWU)) \
              for j in range(nMax+1)}
    return DxUnit, DyUnit
# Dxy -> Drq convertion factors
def cDiffFactors(r, Nx, varDWU):
    def DxDrq01234():
        def DxDq4ri():
            temp32 = (ro02*ro0)*fcs+ro02*(3.0-11.0*Dfcs2)
            temp10 = -ro0*fcs*(9.0+11.0*Dfcs2)+Dfcs2**2+18.0*Dfcs2+5.0
            return ro0two*(temp32+temp10)/ro0_fcs[5]
        DxDrq = {}
        fcs, Dfcs, ro0 = varDWU['fcs'], varDWU['Dfcs'], varDWU['ro0']
        Dfcs2, ro0two, ro02 = Dfcs**2, 2.0*ro0, ro0**2
        ro0_fcs = {1: ro0-fcs}
        for i in range(2, 6): ro0_fcs[i] = ro0_fcs[i-1]*ro0_fcs[1]
        DxDrq[0] = 2.0*fcs/ro0_fcs[1]
        DxDrq[1] = ro0two*Dfcs/ro0_fcs[2]
        DxDrq[2] = ro0two*(-ro0*fcs+Dfcs2+1.0)/ro0_fcs[3]
        DxDrq[3] = ro0two*Dfcs*(-ro02-4.0*ro0*fcs+Dfcs2+5.0)/ro0_fcs[4]
        DxDrq[4] = DxDq4ri()
        return DxDrq
    temp = DxDrq01234()
    DxDrq = {i: np.repeat(temp[i], Nx, axis=0) for i in range(5)}
    DxD = {i: (r-1.0)*DxDrq[i] for i in range(1, 5)}
    DxD[10], DxD[11], DxD[12] = DxDrq[0], DxDrq[1], DxDrq[2]
    DyDq = np.repeat(varDWU['DyDq'], Nx, axis=0)
    return DxD, DyDq
# Dxy2D -> PD
def cPDObasic(Dxy, DxD, DyDq):
    #Second order
    def D2qSet():
        Term2 = DxDq2*Dxy[20]+2.0*DxD[1]*DyDq_Dxyi1[1]+DyDq2*Dxy[2]
        return Term2+DxD[2]*Dxy[10]
    def D1rD1qSet():
        Term2 = DxD[1]*DxDr_Dxy20+DxD[10]*DyDq_Dxyi1[1]
        return Term2+DxD[11]*Dxy[10]
    #Third order
    def D3qSet():
        Term3003 = DxDq3*Dxy[30]+DyDq3*Dxy[3]
        Term2112 = 3.0*DxDq2*DyDq_Dxyi1[2]+3.0*DxD[1]*DyDq2_Dxyi2[1]
        Term2 = 3.0*DxD[2]*DxD[1]*Dxy[20]+3.0*DxD[2]*DyDq_Dxyi1[1]
        return Term3003+Term2112+Term2+DxD[3]*Dxy[10]
    def D2rD1qSet():
        Term3 = DxD[1]*DxDr2*Dxy[30]+DxDr2*DyDq_Dxyi1[2]
        return Term3+2.0*DxD[11]*DxDr_Dxy20
    def D1rD2qSet():
        Term3010 = DxDq2*DxD[10]*Dxy[30]
        Term20 = (2.0*DxDqr_DxDq1+DxD[2]*DxD[10])*Dxy[20]
        Term2112 = DxD[10]*(2.0*DxDq1_DyDq_Dxy21+DyDq2_Dxyi2[1])
        Term1110 = 2.0*DxD[11]*DyDq_Dxyi1[1]+DxD[12]*Dxy[10]
        return Term3010+Term20+Term2112+Term1110
    #Fourh order
    def D4qSet():
        Term3113 = 4.0*DxDq3*DyDq_Dxyi1[3]+4.0*DxD[1]*DyDq3*Dxy[13]
        Term2211 = 6.0*DxDq2*DyDq2_Dxyi2[2]+4.0*DxD[3]*DyDq_Dxyi1[1]
        Term2112 = 12.0*DxD[2]*DxDq1_DyDq_Dxy21+6.0*DxD[2]*DyDq2_Dxyi2[1]
        Term4030 = DxDq2*(DxDq2_Dxy40+6.0*DxD[2]*Dxy[30])
        Term20 = (4.0*DxD[3]*DxD[1]+3.0*DxD[2]**2)*Dxy[20]
        Term10 = DxD[4]*Dxy[10]
        Term04 = DyDq2**2*Dxy[4]
        return Term3113+Term2211+Term2112+Term4030+Term20+Term10+Term04
    def D2rD2qSet():
        Term4022 = DxDr2*(DxDq2_Dxy40+DyDq2_Dxyi2[2])
        Term31 = 2.0*DxD[1]*DxDr2*DyDq_Dxyi1[3]
        Term30 = (4.0*DxDqr_DxDq1*DxD[10]+DxD[2]*DxDr2)*Dxy[30]
        Term21 = 4.0*DxD[11]*DxD[10]*DyDq_Dxyi1[2]
        Term20 = 2.0*(DxD[11]**2+DxD[12]*DxD[10])*Dxy[20]
        return Term4022+Term31+Term30+Term21+Term20
    #some terms
    DxDq2, DxDr2, DyDq2 = DxD[1]**2, DxD[10]**2, DyDq**2
    DxDq3, DyDq3 = DxDq2*DxD[1], DyDq2*DyDq
    DyDq_Dxyi1 = {i: DyDq*Dxy[10*i+1] for i in (1, 2, 3)}
    DyDq2_Dxyi2 = {i: DyDq2*Dxy[10*i+2] for i in (1, 2)}
    DxDr_Dxy20 = DxD[10]*Dxy[20]
    DxDqr_DxDq1 = DxD[11]*DxD[1]
    DxDq2_Dxy40 = DxDq2*Dxy[40]
    DxDq1_DyDq_Dxy21 = DxD[1]*DyDq_Dxyi1[2]
    #PD build
    PD = {0: Dxy[0]}
    #d/dr
    for i in range(1, 5): PD[10*i] = DxD[10]**i*Dxy[10*i]
    #else
    PD[1] = DxD[1]*Dxy[10]+DyDq*Dxy[1]
    PD[2], PD[11] = D2qSet(), D1rD1qSet()
    PD[3], PD[21], PD[12] = D3qSet(), D2rD1qSet(), D1rD2qSet()
    PD[4], PD[22] = D4qSet(), D2rD2qSet()
    return PD
# PD only used at surface
def cPD_surf(q, PD, ND, OI, ctrl): #r = 1
    def shearStressSet():
        nAx = nAxIndex(Nt=len(iS), Nx=1)
        tau = PD[20][iS]-2.0*PD[10][iS]-PD[2][iS] #vr = 0 i.e. DpsiDq = 0 @ r = 1 for DL
        sin_1r_1Term = cosqS[nAx]/sinqS[nAx]*PD[1][iS][nAx] #vr = 0 i.e. DpsiDq = 0 # r = 1 for DL
        tau[nAx] = tau[nAx]+sin_1r_1Term
        return tau
    def sinq_Dr_E2set():
        noSinTerm = PD[12][iS]-2.0*PD[2][iS]
        SinTerm = cosqS*(-PD[11][iS]+2.0*PD[1][iS])
        return (PD[30][iS]+noSinTerm)*sinqS+SinTerm
    iS = SurfIndex(Nx=ND['n'+OI], Nt=ND[OI], sphere=True, outer=(OI=='I'))
    cosqS, sinqS = np.cos(q[iS]), np.sin(q[iS])
    sinq_Dn_E2 = sinq_Dr_E2set()
    PD['R3_Dn_E2_R2_surf'] = sinq_Dn_E2-2.0*sinqS*PD['E2'][iS]
    if ctrl['Sys']['p'] in 'DGPSM': PD['tau_ns_surf'] = shearStressSet()
# =============================================================================
# debug
# =============================================================================
def DerivationTest(PD):
    with open('test.txt','w') as test:
        for k in iter(PD.keys()):
            Nx, Ny = PD[k].shape
            for i in range(Nx):
                for j in range(Ny):
                    test.write('{0} {1} {2} {3}\n'.format(i,j,k,PD[k][i,j]))