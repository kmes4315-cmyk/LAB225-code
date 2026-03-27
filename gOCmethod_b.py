import numpy as np
from functools import partial
from gOCmethod import OCxySet, xy2ns, Dxy1D_HighSet, IntMxySet, Dxy2Dset
from gOCmethod import SurfIndex, nAxIndex, LHospital
from gOCmethod import PDbasic2D, sphericalPD_2D, delKeys
from gOCmethod import h2eta0, eta02h, h2c, xieta2X, rq2etaxi, psiPDS
# =============================================================================
# interface
# =============================================================================
def b_nsPDset(IPs, ctrl):
    #-----common-----#
    global c
    c = h2c(IPs['h'])
    TwoR = 'I' in ctrl['Sys']['OI']
    xyOC = {'n'+OI: OCxySet(ND=IPs['ND']['n'+OI]) for OI in ctrl['Sys']['OI']} #Nxy x 1
    xyOC['s'] = OCxySet(ND=IPs['ND']['s'])
    #-----points-----#
    # outside: x -> eta, y-> xi
    # inside: x -> r, y-> theta
    bound = {'nO': {'a': 0.0, 'b': h2eta0(IPs['h'])}, \
             's': {'a': 0.0, 'b': np.pi}}
    if TwoR: bound.update({'nI': {'a': IPs['rc'], 'b': 1.0}})
    DxDn, sUnit, n, s = {}, {}, {}, {}
    sUnit['O'], DyDxi = xy2ns(xyOC=xyOC['s'], **bound['s'])
    if TwoR: sUnit['I'] = bThetaSet(yOC=xyOC['s'], h=IPs['h'])
    for OI in ctrl['Sys']['OI']:
        nUnit, DxDn[OI] = xy2ns(xyOC=xyOC['n'+OI], **bound['n'+OI])
        n[OI] = np.tile(nUnit, (IPs['ND']['s'], 1))
        s[OI] = np.repeat(sUnit[OI], IPs['ND']['n'+OI], axis=0)
    #-----differential matrix-----#
    #Dxy1D -> DxyUnit
    DxyUnit = Dxy1D_HighSet(ND=IPs['ND'], xyOC=xyOC, nMax=4) #Nxy x Nxy
    #DxyUnit -> PD
    #outside, bispherical coordinate
    PD = {'O': PDbasic2D(DxyUnit={'n': DxyUnit['nO'], 's': DxyUnit['s']}, \
                         DxyDns={'n': DxDn['O'], 's': DyDxi}, \
                         Nxy={'n': IPs['ND']['nO'], 's': IPs['ND']['s']})}
    PD['O']['Int_s_surf'] = IntMxySet(Nxy=IPs['ND']['s'])/DyDxi
    bisphericalPD(xi=s['O'], eta=n['O'], PD=PD['O'], ND=IPs['ND'])
    bPD_surf(eta=n['O'], xi=s['O'], PD=PD['O'], ND=IPs['ND'], \
             OI='O', ctrl=ctrl)
    # PDprint(Nn=IPs['ND']['nO'], Ns=IPs['ND']['s'], n=n['O'], s=s['O'], PD=PD['O']['E4']) #debug
    # PDtest(PD=PD['O'], n=n['O'], s=s['O']) #debug
    #inside, spherical coordinate
    if TwoR:
        PD['I'] = bPDIbasic(DxyUnit=DxyUnit, IPs=IPs, DxDr=DxDn['I'], \
                            DyDq = bI_DiffFactors(q=s['I'], h=IPs['h']))
        sphericalPD_2D(r=n['I'], q=s['I'], PD=PD['I'], ND=IPs['ND'], OI='I', \
                       IL=ctrl['Sys']['m']['IL'])
        # PDtest(PD=PD['I'], n=n['I'], s=s['I']) #debug
        eta, xi = rq2etaxi(r=n['I'], q=s['I'], h=IPs['h'])
        bInsideModify(PDI=PD['I'], ND=IPs['ND'], h=IPs['h'], xi=xi)
        bPD_surf(eta=eta, xi=xi, PD=PD['I'], ND=IPs['ND'], OI='I', ctrl=ctrl)
    for OI in ctrl['Sys']['OI']: delKeys(PD)
    return n, s, PD
# =============================================================================
# inner points
# =============================================================================
def bThetaSet(yOC, h):
    cosy = np.cos(0.5*(yOC+1.0)*np.pi)
    return np.arccos((h*cosy-1.0)/(h-cosy))
# =============================================================================
# innner differential matrix
# =============================================================================
# Dxy -> Drq convertion factors
def bI_DiffFactors(q, h):
    c_pi = 2.0/np.pi*c
    cosq, sinq = np.cos(q), np.sin(q)
    h_cosq = h+cosq
    h_cosq2 = h_cosq**2
    sinq2 = sinq**2
    DyDq = {}
    DyDq[1] = c_pi/h_cosq
    DyDq[2] = c_pi*sinq/h_cosq2
    DyDq[3] = c_pi*(h*cosq+sinq2+1.0)/(h_cosq*h_cosq2)
    DyDq[4] = c_pi*(-h**2+4.0*h*cosq+5.0+sinq2)*sinq/h_cosq2**2
    return DyDq
# DxyUnit -> PD
def bPDIbasic(DxyUnit, IPs, DxDr, DyDq):
    def D4qSet():
        term4 = DyDq12**2*Dxy[4]
        term3 = 6.0*DyDq12*DyDq[2]*Dxy[3]
        term2 = (3.0*DyDq[2]**2+4.0*DyDq[1]*DyDq[3])*Dxy[2]
        term1 = DyDq[4]*Dxy[1]
        return term4+term3+term2+term1
    DxDr2 = DxDr**2
    DyDq12 = DyDq[1]**2
    Dxy = Dxy2Dset(DxUnit=DxyUnit['nI'], DyUnit=DxyUnit['s'],
                   Nx=IPs['ND']['nI'], Ny=IPs['ND']['s'])
    PD = {0: Dxy[0]}
    for i in range(1, 5): PD[10*i] = DxDr**i*Dxy[10*i]
    #first order
    PD[1] = DyDq[1]*Dxy[1]
    #second order
    PD[11] = DxDr*DyDq[1]*Dxy[11]
    PD[2] = DyDq12*Dxy[2]+DyDq[2]*Dxy[1]
    #third order
    PD[21] = DxDr2*DyDq[1]*Dxy[21]
    PD[12] = DxDr*(DyDq12*Dxy[12]+DyDq[2]*Dxy[11])
    PD[3] = (DyDq[1]*DyDq12)*Dxy[3]+3.0*DyDq[1]*DyDq[2]*Dxy[2]+DyDq[3]*Dxy[1]
    #fourth order
    PD[22] = DxDr2*(DyDq12*Dxy[22]+DyDq[2]*Dxy[21])
    PD[4] = D4qSet()
    return PD
# convert the particle surface (r, theta) into (xi, eta)
def bInsideModify(PDI, ND, h, xi):
    def DrqDetaxiSet():
        cosxiS, sinxiS = np.cos(xi[sI]), np.sin(xi[sI])
        XS = h-cosxiS
        c_XS = c/XS
        c_XS2, c2_XS2 = c_XS/XS, c_XS**2
        c_XS2sinxiS = c_XS2*sinxiS
        DrD = {10: -c_XS, 20: c2_XS2, \
               30: -3.0*c2_XS2*c_XS+(2.0*h+cosxiS)*c_XS2}
        DqD = {20: c_XS2sinxiS, 1: c_XS, 2: -c_XS2sinxiS}
        return DrD, DqD
    sI = SurfIndex(Nt=ND['I'], Nx=ND['nI'], sphere=True, outer=True)
    DrD, DqD = DrqDetaxiSet()
    PDIsI = {i: PDI[i][sI] for i in (1, 2, 11, 10, 20, 30)}
    PDI[10][sI] = DrD[10]*PDIsI[10] # D1r is converted into D1eta
    PDI[20][sI] = DrD[10]**2*PDIsI[20]+DrD[20]*PDIsI[10]+DqD[20]*PDIsI[1] # D2r is converted into D2eta
    temp = 3.0*(DrD[20]*DrD[10]*PDIsI[20]+DrD[10]*DqD[20]*PDIsI[11])
    PDI[30][sI] = DrD[10]**3*PDIsI[30]+temp+DrD[30]*PDIsI[10] # D3r is converted into D3eta
    PDI[1][sI] = DqD[1]*PDIsI[1] # D1q is converted into D1xi
    PDI[2][sI] = DqD[1]**2*PDIsI[2]+DqD[2]*PDIsI[1] #D2q is converted into D2xi
# =============================================================================
# outer differential matrix (operators for bispherical coordinate)
# =============================================================================
def bisphericalPD(xi, eta, PD, ND):
    def Dxieta_Xset(is_xi):
        if is_xi: order, sinxieta = 1, sinxi
        else: order, sinxieta = 10, sinheta
        D_X = X*PD[order]-sinxieta*PD[0]
        D_X[:-1] = D_X[:-1]/X[:-1]**2
        D_X[-1] = 0.0
        return D_X
    def L2E2set():
        goodTermCommon = X*(PD[2]+PD[20])-sinheta*PD[10]
        nAxTermCommon = chc_1[nAx]/sinxi[nAx]*PD[1][nAx]
        c2L2 = Hospital(good=X*goodTermCommon, sin_1=X[nAx]*nAxTermCommon)
        c2E2_X = Hospital(good=goodTermCommon+cosxi*PD[0], \
                          sin_1=-nAxTermCommon-2.0*sinxi[nAx]*PD[1][nAx])
        return c2L2/c2, c2E2_X/c2
    def E4_Xset():
        def Term3():
            goodTerm = 2.0*X*sinheta*(PD[12]+PD[30])
            nAxTerm = -2.0*chc_1[nAx]*X_sinxi_nAx*(PD[3][nAx]+PD[21][nAx])
            return Hospital(good=goodTerm, sin_1=nAxTerm)
        def Term2():
            X2_sinxi2 = X2-sinxi2
            goodTerm = X2_sinxi2*(PD[2]-PD[20])-2.0*shs*PD[11]
            nAxTerm02 = 3.0*X2[nAx]/sinxi2[nAx]*PD[2][nAx]
            nAxTerm11 = -2.0*sinheta[nAx]*cosxi[nAx]*X_sinxi_nAx*PD[11][nAx]
            return Hospital(good=goodTerm, sin_1=nAxTerm02+nAxTerm11)
        def Term1():
            goodTerm = -2.0*X*sinheta*PD[10]
            temp = 2.0*chc_1[nAx]+3.0*X[nAx]*cosxi[nAx]/sinxi2[nAx]
            nAxTerm = -X_sinxi_nAx*temp*PD[1][nAx]
            return Hospital(good=goodTerm, sin_1=nAxTerm)
        sinxi2 = sinxi**2
        X_sinxi_nAx = X[nAx]/sinxi[nAx]
        Term4 = X2*(PD[4]+2.0*PD[22]+PD[40])
        Term0 = -sinxi2*PD[0]
        return X/c2**2*(Term4+Term3()+Term2()+Term1()+Term0)
    cosheta, sinheta = np.cosh(eta), np.sinh(eta)
    cosxi, sinxi = np.cos(xi), np.sin(xi)
    X = xieta2X(eta=eta, xi=xi)
    chc_1 = cosheta*cosxi-1.0
    shs = sinheta*sinxi
    global c
    c2, X2 = c**2, X**2
    nAx = nAxIndex(Nt=ND['O'], Nx=ND['nO'])
    Hospital = partial(LHospital, nAx=nAx)
    PD['L2'], PD['E2'] = L2E2set() # in fact, 'E2' is E2(f/X) instead of E2(f)
    PD['E4'] = E4_Xset() # in fact 'E4' is E4(f/X) instead of E4(f)
    PD['D1R'] = (-shs*PD[10]+chc_1*PD[1])/c
    PD['D1Z'] = (-chc_1*PD[10]-shs*PD[1])/c
    PD['1_X'] = Dxieta_Xset(True)
    PD['10_X'] = Dxieta_Xset(False)
# =============================================================================
# surface differential matrix
# =============================================================================
def bPD_surf(eta, xi, PD, ND, OI, ctrl):
    def outsidePD_X():
        def ordersSet():
            orders = [0, '1_X', '10_X']
            if ctrl['Sys']['p'] in 'DGPSM': orders.extend([1, 2, 10, 20, 30])
            return orders
        PDS = {i: PD[i][iS] for i in ordersSet()}
        PD_X_surf = PD_Xset(PDS=PDS, etaS=eta[iS], xiS=xi[iS])
        return {str(i)+'_X_surf': PDi for i, PDi in PD_X_surf.items()}
    def AirWaterTauSet():
        iS_O = SurfIndex(Nx=ND['nO'], Nt=ND['O'], sphere=False, outer=True)
        PDS = {i: PD[i][iS_O] for i in (0, '1_X', '10_X', 1, 2, 10, 20)}
        PD_X_surf = PD_Xset(PDS=PDS, etaS=eta[iS_O], xiS=xi[iS_O])
        return shearStressSet(PDS=PD_X_surf, etaS=eta[iS_O], xiS=xi[iS_O])
    def DLtauSet():
        PDS = {i: psiPDS(bisp=not inside, PD=PD, order=i, iS=iS) \
               for i in (1, 2, 10, 20)}
        return shearStressSet(PDS=PDS, etaS=eta[iS], xiS=xi[iS])
    def sinxi_Deta_E2_surfSet():
        goodTerm3 = XS2*(PD[12][iS]+PD[30][iS])
        goodTerm2 = XS*c*(2.0*PD[2][iS]+3.0*PD[20][iS])
        goodTerm1 = (c**2+XS*h)*PD[10][iS]
        sin_1Term = -XS*chc_1*PD[11][iS]-(c*chc_1+XS*c*cosxiS)*PD[1][iS]
        return ((goodTerm3+goodTerm2+goodTerm1)*sinxiS+sin_1Term)/c2
    def sinxi_Deta_E2_XsurfSet():
        goodTerm3 = XS*(PD[12][iS]+PD[30][iS])
        goodTerm21 = c*PD[2][iS]-2.0*sinxiS*PD[11][iS]-XS*PD[10][iS]
        sin_1Term = -chc_1*PD[11][iS]-cosxiS*c*PD[1][iS]
        return ((goodTerm3+goodTerm21)*sinxiS+sin_1Term)/c2
    def R3_Deta_E2_R2_XsurfSet():
        return c/XS*sins_Dn_E2_X+2.0*c2/XS2*PD['E2'][iS]*sinxiS
    global c
    inside = OI=='I'
    iS = SurfIndex(Nx=ND['n'+OI], Nt=ND[OI], sphere=inside, outer=inside)
    cosxiS, sinxiS = np.cos(xi[iS]), np.sin(xi[iS])
    h = eta02h(eta[iS][0])
    XS = xieta2X(eta=eta[iS], xi=xi[iS])
    chc_1 = h*cosxiS-1.0
    c2, XS2 = c**2, XS**2
    PD_Xset = partial(PD_X_surfSet, tol=ctrl['N']['tol'])
    if not inside:
        sins_Dn_E2_X = sinxi_Deta_E2_XsurfSet()
        PD['R3_Dn_E2_R2_surf'] = R3_Deta_E2_R2_XsurfSet()
        PD.update(outsidePD_X())
        if ctrl['Sys']['OB']['A-W']: PD['tau_ns_plane'] = AirWaterTauSet()
    if ctrl['Sys']['p'] in 'DGPSM': PD['tau_ns_surf'] = DLtauSet()
def PD_X_surfSet(PDS, etaS, xiS, tol):
    def D0_Xset():
        D0_X = np.zeros(PDS[0].shape)
        D0_X[fin] = PDS[0][fin]/XS
        return D0_X
    def D2xieta_Xset(is_xi):
        if is_xi:
            order = {1: 1, 2: 2}
            sinxieta, cosxieta = sinxiS, cosxiS
        else:
            order = {1: 10, 2: 20}
            sinxieta, cosxieta = sinhetaS, coshetaS
        D2_X = np.zeros(PDS[0].shape)
        term21 = PDS[order[2]][fin]/XS-2.0*sinxieta/XS2*PDS[order[1]][fin]
        term0 = (-cosxieta+2.0*sinxieta**2/XS)/XS2*PDS[0][fin]
        D2_X[fin] = term21+term0
        return D2_X
    def D3eta_Xset():
        sinhetaS2 = sinhetaS**2
        D3eta_X = np.zeros(PDS[0].shape)
        term32 = PDS[30][fin]/XS-3.0*sinhetaS/XS2*PDS[20][fin]
        term1 = 3.0/XS2*(-coshetaS+2.0*sinhetaS2/XS)*PDS[10][fin]
        temp = -1.0+6.0*coshetaS/XS-6.0*sinhetaS2/XS2
        term0 = sinhetaS/XS2*temp*PDS[0][fin]
        D3eta_X[fin] = term32+term1+term0
        return D3eta_X
    XS = xieta2X(eta=etaS, xi=xiS)
    fin = np.arange(XS.shape[0])[np.ravel(XS>tol)]
    XS = XS[fin]
    coshetaS, sinhetaS = np.cosh(etaS[fin]), np.sinh(etaS[fin])
    cosxiS, sinxiS = np.cos(xiS[fin]), np.sin(xiS[fin])
    XS2 = XS**2
    orders = set(PDS.keys()) # 0, '1_X', '10_X' must be included
    PD_X_surf = {0: D0_Xset(), 1: PDS['1_X'].copy(), 10: PDS['10_X'].copy()}
    if {2, 1}.issubset(orders): PD_X_surf[2] = D2xieta_Xset(True)
    if {20, 10}.issubset(orders): PD_X_surf[20] = D2xieta_Xset(False)
    if {30, 20, 10}.issubset(orders): PD_X_surf[30] = D3eta_Xset()
    return PD_X_surf
def shearStressSet(PDS, etaS, xiS):
    coshetaS, cosxiS = np.cosh(etaS), np.cos(xiS)
    sinxiS = np.sin(xiS)
    XS = xieta2X(eta=etaS, xi=xiS)
    XS_c2 = XS/c**2
    goodTerm = XS*(PDS[2]-PDS[20])-3.0*np.sinh(etaS)*PDS[10]
    sin_1Term = (2.0*sinxiS**2-coshetaS*cosxiS+1.0)*PDS[1]
    nAx = nAxIndex(Nt=len(etaS), Nx=1)
    return XS_c2*LHospital(nAx=nAx, good=goodTerm, \
                           sin_1=sin_1Term[nAx]/sinxiS[nAx])
# =============================================================================
# debug
# =============================================================================
def NnNs2NsNn(Nn, Ns):
    return np.array([j*Nn+i for i in np.arange(Nn) for j in np.arange(Ns)])
def PDprint(Nn, Ns, n, s, PD):
    NsNn = NnNs2NsNn(Nn=Nn, Ns=Ns)
    with open('test.txt', 'w') as x:
        for i in NsNn:
            for j in NsNn:
                values = (i, j, n[i, 0], s[i, 0], PD[i, j])
                x.write('{} {} {} {} {}\n'.format(*values))
def PDtest(PD, n, s):
    for i in (0, 1, 2, 3, 4):
        for j in (0, 1, 2, 3, 4):
            if i+j<=4 and 10*i+j not in (13, 31):
                value = np.matmul(PD[10*i+j], n**i*s**j)
                print(i, j, tuple(mm(value) for mm in (max, min)))