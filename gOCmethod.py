import numpy as np
from functools import partial
tol, large = 1e-12, 1000 #changed by main program
# =============================================================================
# points
# =============================================================================
# d (n or s) / d (x or y)
DxyDvarSet = lambda a, b: 2.0/(b-a)
# OC points of xy (-1 ~ 1)
def OCxySet(ND):
    return np.reshape(np.cos(np.arange(ND)*np.pi/float(ND-1)), (ND, 1))
# convert (x or y) into (n or s)
def xy2ns(xyOC, a, b):
    DxyDvar = DxyDvarSet(a=a, b=b)
    return a+(xyOC+1.0)/DxyDvar, DxyDvar
# integral matrix of (x or y) i.e domain is -1 ~ 1
def IntMxySet(Nxy):
    N=Nxy-1
    whole = range(Nxy)
    Ci = {i: 1.0 for i in whole}
    Ci[0], Ci[N] = 2.0, 2.0
    cosik = {(i, k): np.cos(np.pi*float(i*k)/float(N)) \
             for i in whole for k in whole}
    Intk = {k: (k%2-1)*2.0/(k**2-1.0) for k in range(2, Nxy)}
    Intk[0], Intk[1] = 2.0, 0.0
    SumTerm = {i: sum([cosik[(i,k)]*Intk[k] for k in whole]) for i in whole}
    IntMy = np.array([(SumTerm[i]-1.0)*2.0/N/Ci[i] for i in whole])
    return np.reshape(IntMy, (1, Nxy))
# =============================================================================
# xy differential matrix (used in 1D and 2D)
# =============================================================================
# 1st order differential matrix for (x or y)
def Dxy1D_1Set(Nxy, xyOC):
    N = Nxy-1
    Dxy1D = np.empty((Nxy, Nxy))
    C = {i: 1.0 for i in range(Nxy)}
    C[0], C[N] = 2.0, 2.0
    for i in range(Nxy):
        if i==0: Dxy1D[i, i] = (2.0*N**2+1.0)/6.0
        elif i==N: Dxy1D[i, i] = -(2.0*N**2+1.0)/6.0
        else: Dxy1D[i, i] = 0.5*xyOC[i]/(xyOC[i]**2-1.0)
        for k in range(i+1, Nxy):
            temp = (-1.0)**((i+k)%2)/(xyOC[i]-xyOC[k])
            Dxy1D[i, k] = C[i]/C[k]*temp
            Dxy1D[k, i] = -C[k]/C[i]*temp
    return Dxy1D
# higher order differential matrix for (x or y)
def Dxy1D_HighSet(ND, xyOC, nMax):
    names = xyOC.keys()
    Dxy1D = {i: {0: np.identity(ND[i]), \
                 1: Dxy1D_1Set(Nxy=ND[i], xyOC=xyOC[i])} for i in names}
    for i in names:
        for j in range(2, nMax+1):
            Dxy1D[i][j] = np.matmul(Dxy1D[i][j-1], Dxy1D[i][1])
    return Dxy1D
# =============================================================================
# xy differential matrix (used only in 2D)
# =============================================================================
# convert Dx1D into Dx2D
DxDxDx = lambda Dx, Ny: np.tile(Dx, (Ny, Ny))
# convert Dy1D into Dy2D
DyDyDy = lambda Dy, Nx: np.repeat(np.repeat(Dy, Nx, axis=0), Nx, axis=1)
# combine Dx1D and Dy1D into Dxy2D
def Dxy2Dset(DxUnit, DyUnit, Nx, Ny):
    Dx2D = {i: DxDxDx(Dx=Dxi, Ny=Ny) for i, Dxi in DxUnit.items()}
    Dy2D = {i: DyDyDy(Dy=Dyi, Nx=Nx) for i, Dyi in DyUnit.items()}
    return {10*i+j: Dxi*Dyj for i, Dxi in Dx2D.items() \
            for j, Dyj in Dy2D.items() if i+j<=4}
# convert Dxy into Dns
def PDbasic2D(DxyUnit, DxyDns, Nxy):
    # DxUnit & DyUnit -> DnsUnit #Nxy x Nxy
    DnsUnit = {ns: {i: Dxyi*DxyDns[ns]**i \
                    for (i, Dxyi) in DxyUnit[ns].items()} for ns in 'ns'}
    # DnsUnit -> PD #Nt x Nt
    return Dxy2Dset(DxUnit=DnsUnit['n'], DyUnit=DnsUnit['s'], \
                    Nx=Nxy['n'], Ny=Nxy['s'])
# =============================================================================
# indexes
# =============================================================================
def AxisIndex(Nt, Nx):
    return np.concatenate((np.arange(0, Nx), np.arange(Nt-Nx, Nt)))
def nAxIndex(Nt, Nx):
    return np.delete(np.arange(Nt), AxisIndex(Nt=Nt, Nx=Nx))
def SurfIndex(Nt, Nx, sphere, outer=False):
    if sphere!=outer: return np.arange(Nx-1, Nt, Nx) #spherical inner or bispherical outer
    else: return np.arange(0, Nt, Nx) #spherical outer or bispherical inner
def NcSet(ND, OI):
    nOI = 'n'+OI
    return {'D': ND[nOI]*ND['sD'], 'U': ND[OI]-ND[nOI]*ND['sU']}
def EndIndexUD(Nc, Nt, Nx):
    return np.arange(Nc['U'], Nt, Nx), np.arange(0, Nc['D'], Nx)
def Z0index(NDW, NW, Nx):
    start = NDW+int((NW-1)/2)*Nx
    return np.arange(start, start+Nx)
def LHospital(nAx, good, sin_1=0.0):
    operator = good.copy()
    operator[nAx] += sin_1 #assume d/d(theta) = 0 @ theta = 0 & theta = pi
    return operator
# =============================================================================
# operators for spherical coordinate
# =============================================================================
def sphericalPD_2D(r, q, PD, ND, OI, IL):
    def E4L4set():
        def L4set():
            Term11 = -Cos_Sin_r2**2*PD[2][nAx]
            return Hospital(good=Common4+Common3good, \
                            sin_1=Common3nAx+Term11+Common1)
        def E4set():
            Term11 = 4.0*Cos_Sin_r2/r[nAx]*PD[11][nAx]
            Term02 = (5.0+3.0/sinq2nAx)/r4[nAx]*PD[2][nAx]
            return Hospital(good=Common4-Common3good, \
                            sin_1=-Common3nAx+Term11+Term02-3.0*Common1)
        r4 = r2*r2
        Common4 = PD[40]+2.0/r2*PD[22]+PD[4]/r4
        Common3good = 4.0/r3*PD[12]
        Common3nAx = 2.0*Cos_Sin_r2*(PD[21][nAx]+PD[3][nAx]/r2[nAx])
        Common1 = (2.0+1.0/sinq2nAx)/r2[nAx]*Cos_Sin_r2_D1q
        E4 = E4set()
        L4 = L4set() if IL else None
        return E4, L4
    def DrL2set():
        goodTerm = PD[30]+(PD[12]-2.0*PD[10])/r2+2.0/r*PD[20]-2.0/r3*PD[2]
        nAxTerm = Cos_Sin_r2*PD[11][nAx]-2.0/r[nAx]*Cos_Sin_r2_D1q
        return Hospital(good=goodTerm, sin_1=nAxTerm)
    def DRL2set():
        goodTermCos = cosq/r*(PD[21]+PD[3]/r2+3.0/r*PD[11])
        goodTermSin = sinq*(PD[30]+PD[12]/r2+2.0/r*PD[20]-2.0/r2*PD[10])
        nAxTerm2 = (1.0/sinq[nAx]-3.0*sinq[nAx])/r3[nAx]*PD[2][nAx]
        nAxTerm1 = -cosq[nAx]/r3[nAx]*(2.0+1.0/sinq[nAx]**2)*PD[1][nAx]
        return Hospital(good=goodTermCos+goodTermSin, sin_1=nAxTerm1+nAxTerm2)
    nAx = nAxIndex(Nt=ND[OI], Nx=ND['n'+OI])
    Hospital = partial(LHospital, nAx=nAx)
    r2 = r**2
    r3 = r2*r
    cosq, sinq = np.cos(q), np.sin(q)
    Cos_Sin_r2 = cosq[nAx]/r2[nAx]/sinq[nAx]
    Cos_Sin_r2_D1q = Cos_Sin_r2*PD[1][nAx]
    sinq2nAx = sinq[nAx]**2
    D2q_r2 = PD[2]/r2
    D1q_r = PD[1]/r
    PD['L2'] = Hospital(good=PD[20]+D2q_r2+2.0*PD[10]/r, sin_1=Cos_Sin_r2_D1q)
    PD['E2'] = Hospital(good=PD[20]+D2q_r2, sin_1=-Cos_Sin_r2_D1q)
    PD['E4'], PD['L4'] = E4L4set()
    PD['D1R'] = sinq*PD[10]+cosq*D1q_r
    PD['D1Z'] = cosq*PD[10]-sinq*D1q_r
    if IL: PD['Dr(L2)'], PD['DR(L2)'] = DrL2set(), DRL2set()
    else: del PD['L4']
# =============================================================================
# boundary condition position
# =============================================================================
def IndexSet(ND, ctrlSys):
    At = AtSet(ND=ND, ctrlSys=ctrlSys)
    At_1 = At_1Set(At=At, ND=ND, ctrlSys=ctrlSys)
    return At, At_1
def AtSet(ND, ctrlSys):
    At = {OI: {} for OI in ctrlSys['OI']}
    for OI in ctrlSys['OI']:
        nOI = 'n'+OI
        iSset = partial(SurfIndex, sphere=ctrlSys['major']+OI!='bO')
        # particle surface (and core surface)
        At[OI]['s'] = iSset(Nx=ND[nOI], Nt=ND[OI], outer=False)
        if ctrlSys['major']!='a':
            # symmetric axis
            At[OI]['ax'] = AxisIndex(Nt=ND[OI], Nx=ND[nOI])
        if ctrlSys['major']=='c':
            Nc = NcSet(ND=ND, OI=OI)
            # corner
            cA = tuple(np.arange(Nc[DU]-ND[nOI], Nc[DU]) for DU in 'DU')
            At[OI]['qwA'] = np.concatenate(cA)
            At[OI]['qwB'] = At[OI]['qwA']+ND[nOI]
            # Z = 0 (theta = pi/2)
            At[OI]['Z0'] = Z0index(NDW=Nc['D'], NW=ND['sW'], Nx=ND[nOI])
        if OI=='O':
            if ctrlSys['major']=='a':
                # outer virtual surface
                At['O']['ro'] = iSset(Nx=ND['nO'], Nt=ND['O'], outer=True)
            elif ctrlSys['major']=='b':
                # plane surface
                At['O']['p'] = iSset(Nx=ND['nO'], Nt=ND['O'], outer=True)
            elif ctrlSys['major']=='c':
                # wall
                At['O']['w'] = np.arange(Nc['D'], Nc['U'], ND['nO'])
                # cylinder end
                At['O']['u'], At['O']['d'] = \
                    EndIndexUD(Nc=Nc, Nt=ND['O'], Nx=ND['nO'])
        # particle inner surface
        elif OI=='I':
            At[OI]['sI'] = iSset(Nx=ND['nI'], Nt=ND['I'], outer=True)
    return At
l_bis = {True: -1, False: 1}
def At_1Set(At, ND, ctrlSys):
    At_1 = {OI: {} for OI in At.keys()}
    for OI in At.keys():
        l = l_bis[ctrlSys['major']+OI=='bO']
        Nx = ND['n'+OI]
        At_1[OI]['s'] = At[OI]['s']-l #inner boundary
        for site in At[OI].keys():
            if site in ('ro', 'p', 'w', 'u', 'd', 'sI'): #outer boundary
                At_1[OI][site] = At[OI][site]+l
            elif site=='qwA':
                At_1[OI]['qwA'] = At[OI]['qwA']-Nx
            elif site=='qwB':
                At_1[OI]['qwB'] = At[OI]['qwB']+Nx
            elif site=='ax':
                llll = Nx*np.ones(Nx, dtype=int)
                At_1[OI]['ax'] = At[OI]['ax']+np.concatenate((llll, -llll))
    return At_1
# =============================================================================
# scale factors
# =============================================================================
def addFactors(n, s, majorSys, IPs):
    def b_hns_gradZns(eta, xi):
        X = xieta2X(eta=eta, xi=xi)
        X[-1] = tol
        X_c = X/h2c(IPs['h'])
        gradZn = -(np.cosh(eta)*np.cos(xi)-1.0)/X
        gradZs = -np.sinh(eta)*np.sin(xi)/X
        return X_c, X_c, gradZn, gradZs
    hns, R, Z, gradZ = {}, {}, {}, {}
    for OI in n.keys():
        if majorSys+OI=='bO':
            R['O'], Z['O'] = ns2RZ(n=n['O'], s=s['O'], bis=True, h=IPs['h'])
            hn, hs, gradZn, gradZs = b_hns_gradZns(eta=n['O'], xi=s['O'])
            hns['O'] = {'n': hn, 's': hs}
            gradZ['O'] = {'n': gradZn, 's': gradZs}
        else:
            hns[OI] = {'n': np.ones(n[OI].shape), 's': 1.0/n[OI]}
            if majorSys=='a':
                R[OI], Z[OI] = n[OI], n[OI]
                gradZ[OI] = {'n': np.ones(n[OI].shape), \
                             's': -np.ones(n[OI].shape)}
            elif majorSys in 'bc':
                h = IPs['h'] if majorSys=='b' else 0.0
                R[OI], Z[OI] = ns2RZ(n=n[OI], s=s[OI], bis=False, h=h)
                gradZ[OI] = {'n': np.cos(s[OI]), 's': -np.sin(s[OI])}
                if majorSys+OI=='bI':
                    sI = SurfIndex(Nt=IPs['ND']['I'], Nx=IPs['ND']['nI'], \
                                   sphere=True, outer=True)
                    eta, xi = rq2etaxi(r=n['I'][sI], q=s['I'][sI], h=IPs['h'])
                    hn, hs, gradZn, gradZs = b_hns_gradZns(eta=eta, xi=xi)
                    hns['I']['n'][sI], hns['I']['s'][sI] = hn, hs
                    gradZ['I']['n'][sI], gradZ['I']['s'][sI] = gradZn, gradZs
    return hns, R, Z, gradZ
# =============================================================================
# vector operation
# =============================================================================
ns12 = {True: {2: 'n', 1: 's'}, False: {1: 'n', 2: 's'}}
ns101 = {'n': 10, 's': 1}
VecAoVecB = lambda vecA, vecB: sum(vecA[ns]*vecB[ns] for ns in vecA.keys())
def VecAxVecB(vecs, plane):
    one, two = ns12[plane][1], ns12[plane][2]
    return vecs[0][one]*vecs[1][two]-vecs[0][two]*vecs[1][one]
def gradSet(PD, h, majorSys):
    if majorSys=='a':
        return {OI: {'n': h[OI]['n']*PD[OI][10], \
                     's': -h[OI]['s']*PD[OI][0]} for OI in PD.keys()}
    elif majorSys in 'bc':
        return {OI: {ns: h[OI][ns]*PD[OI][ns101[ns]] for ns in 'ns'} \
                     for OI in PD.keys()}
# =============================================================================
# conversion
# =============================================================================
def h2eta0(h): return np.arccosh(h)
def eta02c(eta0): return np.sinh(eta0)
def h2c(h): return np.sqrt(h**2-1.0)
def eta02h(eta0): return np.cosh(eta0)
def xieta2X(eta, xi): return np.cosh(eta)-np.cos(xi)
def ns2RZ(n, s, bis, h):
    if bis:
        X = xieta2X(eta=n, xi=s)
        iInf = abs(X)<tol
        fin = np.logical_not(iInf)
        c_X = h2c(h)/X[fin]
        RZ = {'R': np.sin(s), 'Z': np.sinh(n)}
        for i in 'RZ':
            RZ[i][fin] = RZ[i][fin]*c_X
            RZ[i][iInf] = large
    else:
        RZ = {'R': n*np.sin(s), 'Z': n*np.cos(s)+h}
    return RZ['R'], RZ['Z']
def rq2etaxi(r, q, h):
    c = h2c(h)
    Z = r*np.cos(q)+h
    TwocZ = 2.0*c*Z
    c2, Z2 = c**2, Z**2
    X2Y2Z2 = (r*np.sin(q))**2+Z2
    down = np.sqrt((X2Y2Z2+c2)**2-TwocZ**2)
    eta = np.arcsinh(TwocZ/down)
    temp = (X2Y2Z2-c2)/down
    temp[abs(temp)>1] = 1.0
    xi = np.arccos(temp)
    return eta, xi
# =============================================================================
# PD type select for abc case
# =============================================================================
psiSign = {False: 1.0, True: -1.0}
def psiPDS(bisp, PD, order, iS):
    return PD[str(order)+'_X_surf'] if bisp else PD[order][iS]
# =============================================================================
# other function
# =============================================================================
def delKeys(PD):
    AllKeys = tuple(PD.keys())
    UselessKeys = (4, 12, 13, 21, 22, 31, 40, )
    for i in AllKeys:
        if i in UselessKeys:
            del PD[i]