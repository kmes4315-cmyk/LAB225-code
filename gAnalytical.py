import numpy as np
import mpmath as mpm
from scipy.integrate import simps
from gCalculator import WmpSet, betaSet, l_m1m2Set, visEffSet
IPs, ctrl, tol = {}, {}, {} #changed by main program
Ngrid = 500
# =============================================================================
# vectorized functions
# =============================================================================
Float = np.vectorize(float)
Exp = np.vectorize(mpm.exp)
Real = np.vectorize(mpm.re)
RealFloat = lambda x: Float(Real(x))
# =============================================================================
# interface
# =============================================================================
def LowZetaPhi(r): #low electric potential
    if ctrl['Sys']['m']['IL'] and abs(IPs['kaLc']/IPs['ka'])>tol:
        if ctrl['Sys']['OB']['Cell']: return DebyeHuckelPhi_CellIL(r)
        else: return DebyeHuckelPhi_SingleIL(r)
    else:
        return DebyeHuckelPhi_Basic(r)
def HighKaPhi(r):
    # zeta, ka
    aTanh, Tanh = np.vectorize(mpm.atanh), np.vectorize(mpm.exp)
    tanh_phi_4 = Tanh(IPs['zeta']/4.0)*Exp(IPs['ka']*(1.0-r))
    return RealFloat(4.0*aTanh(tanh_phi_4))
def LowZetaMu(): #low electric potential
    if ctrl['Sys']['m']['Diffu'] and ctrl['Sys']['p'] in 'RDG':
        return OhshimaTmYDL_LowZeta()
    else:
        if ctrl['Sys']['m']['IL'] and abs(IPs['kaLc']/IPs['ka'])>tol:
            if ctrl['Sys']['OB']['Cell']: return StoutKhairTmY_Cell()
            else: return StoutKhairTmY_Single()
        else:
            if ctrl['Sys']['p'] in 'DG': return OhshimaTmYDL_LowZeta()
            elif ctrl['Sys']['p']=='P': return HermansFujita()
            else: return Henry()
def HighKaMu(r, nje): #thin double layer
    if ctrl['Sys']['m']['Diffu']:
        if ctrl['Sys']['p'] in 'RDG': return PrieveAndersonTmY()
        else: return 0.0
    else:
        if ctrl['Sys']['m']['IL']:
            SZ = ctrl['BC'].get('SZ')
            if SZ: SZ = SZ['gj']
            return SquiresKhairTmY(r=r, nje=nje, SZ=SZ)
        else:
            if ctrl['Sys']['p']=='D': return OhshimaDL_HighKa(1.0)
            else: return IPs['zeta'] if IPs['zeta'] else 0.0
# =============================================================================
# electric potential analytical solution
# =============================================================================
def DebyeHuckelPhi_Basic(r):
    # zeta, ka, ro, Cell
    r_1 = r-1.0
    SingleTerm = Exp(IPs['ka']*(-r_1))
    if ctrl['Sys']['OB']['Cell']:
        ka_ro = IPs['ka']*IPs['ro']
        Acell = Exp(2.0*IPs['ka']*(1.0-IPs['ro']))*(ka_ro+1.0)/(ka_ro-1.0)
        CellTerm = Acell*Exp(IPs['ka']*r_1)
    else:
        Acell, CellTerm = 0.0, 0.0
    return RealFloat(IPs['zeta']/r*(SingleTerm+CellTerm)/(1.0+Acell))
def DebyeHuckelPhi_SingleIL(r):
    # zeta, ka, Lc
    r_1 = r-1.0
    l_m1, m2 = l_m1m2Set()
    temp = m2**2*l_m1**2*(1.0+m2)/(1.0+1.0/l_m1)
    exp1, exp2 = Exp(-m2*r_1), Exp(-r_1/l_m1)
    return RealFloat(IPs['zeta']/(1.0-temp)/r*(exp1-temp*exp2))
def DebyeHuckelPhi_CellIL(r):
    # zeta, ka, Lc, ro
    l_m1, m2 = l_m1m2Set()
    r_1 = r-1.0
    AA0, AA3, AA4 = AA_set(m1=1.0/l_m1, m2=m2)
    expr1, expr2 = Exp(r_1/l_m1), Exp(m2*r_1)
    return RealFloat(IPs['zeta']/AA0/r*(-AA4+AA3*expr2+AA3/expr2-AA4/expr1))
# =============================================================================
# mobility analytical solution (low zeta)
# =============================================================================
def Henry():
    #zeta, ka
    #from: Masliyah, J.H. and S. Bhattacharjee, Electrokinetic and colloid transport phenomena. (2006) ch9
    #condition: Single HS, DC, zeta->0
    return IPs['zeta']*(1.0-1.0/3.0/(1.0+0.072*IPs['ka'])**1.13)
def Booth():
    # zeta, ka, vis
    # The cataphoresis of spherical fluid droplets in electrolytes (1951)
    def F1(ka):
        ka2 = ka**2
        ka3, ka4 = ka2*ka, ka2**2
        polynominalTerm = ka2/8.0-5.0/24.0*ka3-ka4/48.0+ka2*ka3/48.0
        expTerm = ka4/4.0*np.exp(ka)*En(1, ka)*(1.0-ka2/12.0)
        return polynominalTerm+expTerm
    def F2(ka):
        ka2 = ka**2
        ka4 = ka2**2
        polynominalTerm = 0.5+ka/2.0-ka2/4.0+ka2*ka/4.0
        expTerm = -ka4*np.exp(ka)/4.0*En(1, ka)
        return polynominalTerm+expTerm
    En = np.vectorize(mpm.expint)
    condRatio = -1.0 if ctrl['BC']['conductive'].get('s') else 0.5
    if ctrl['Sys']['p']=='R':
        DLterm = 0.0
        down = 3.0
    elif ctrl['Sys']['p'] in 'DG':
        visEff = visEffSet(1.0)
        DLterm = 2.0/visEff*(1.0-condRatio*F2(IPs['ka']))
        down = 3.0+2.0/visEff
    HSterm = 3.0*(1.0+condRatio*F1(IPs['ka']))
    return float(2.0/3.0*IPs['zeta']/down*(HSterm+DLterm))
# def OhshimaDL_LowZeta():
#     #zeta, ka, vis
#     #from: A Simple Expression for the Electrophoretic Mobility of Charged Mercury Drops (1997)
#     #condition: Single DL, DC, zeta->0
#     vis3_2 = visEffSet(1.0)*3.0+2.0
#     temp = 0.5/(1.0+1.86/IPs['ka'])**3
#     return 2.0/3.0*IPs['zeta']*(1.0+temp)*(IPs['ka']+vis3_2+1.0)/vis3_2
# def OhshimaDL_LowZeta():
#     #zeta, ka, vis
#     # from: Electrokinetic phenomena in a dilute suspension of charged mercury drops (1984)
#     #condition: Single DL, DC, zeta->0
#     En = np.vectorize(mpm.expint)
#     visEff = visEffSet(1.0)
#     vis3_2 = 3.0*visEff+2.0
#     expkaTerm = 2.0*vis3_2*En(5, IPs['ka'])-15.0*visEff*En(7, IPs['ka'])
#     expka = np.exp(IPs['ka'])
#     return float(IPs['zeta']/vis3_2*(IPs['ka']+vis3_2-1.0+expka*expkaTerm))
def OhshimaTmYDL_LowZeta():
    # zeta, ka, vis
    # from: Electrokinetic phenomena in a dilute suspension of charged mercury drops (1984)
    # condition: Single HS or conductive DL, DC, zeta->0
    def AnSet(n, ka):
        ka_5 = -ka/5.0
        n_5, ka2 = n-5, ka*2
        s = 0.0
        for k in range(1, 6-n): s = s+ka_5**(-n_5-k)*En(k, ka2)
        E6_n2ka = En(6-n, ka2)/5.0
        E1term = 0.16*np.exp(10)*ka*ka_5**(4-n)*En(1, ka2+10.0)
        return E6_n2ka+0.16*ka*s-E1term
    def Wn(n, ka):
        l_ka = 1.0/ka
        En2ka = {i: En(i-n, 2.0*ka) for i in (3, 4, 5, 6, 7)}
        En2kaTerm = En2ka[3]+2.0*l_ka*En2ka[4]+l_ka**2*En2ka[5]
        Enka = {i: En(i-n, ka) for i in (4, 5)}
        EnkaTerm = (0.5*En(5, ka)+En(-1, ka))*(ka*Enka[4]+Enka[5])
        An = AnSet(n=n, ka=ka)
        return -An+En2kaTerm-EnkaTerm
    def muEset(beta):
        Enka = {i: En(i, IPs['ka']) for i in (-1, 0, 3, 5)}
        muHSE = 6.0*(Enka[-1]-Enka[0])+1.5*(Enka[3]-Enka[5])
        if DL: muDLE = (6.0*Enka[-1]-4.0*Enka[0]+Enka[3])/visEff
        else: muDLE = 0.0
        return beta*(muHSE+muDLE)
    def muDset():
        En2ka = {i: En(i, 2.0*IPs['ka']) for i in (0, 1, 4, 6)}
        Wnka = {i: Wn(n=i, ka=IPs['ka']) for i in (0, 2, 3)}
        temp = 2.0*Wnka[3]+Wnka[0]-3.0*Wnka[2]
        muHSD = 3.0*(En2ka[0]-En2ka[1])+0.75*(En2ka[4]-En2ka[6])+temp
        if DL:
            temp = 2.0*(Wnka[3]-Wnka[2])
            muDLD = (3.0*En2ka[0]-2.0*En2ka[1]+0.5*En2ka[4]+temp)/visEff
        else:
            muDLD = 0.0
        return zeta_expka*(muHSD+muDLD)
    def phidSset(beta):
        def aleph(ka):
            ka2 = 2.0*ka
            En2ka = {i: En(i, ka2) for i in (-1, 0, 1, 2, 3)}
            term123 = 2.0/ka*En2ka[1]+(ka/2+1.0/ka**2)*En2ka[2]+En2ka[3]/2.0
            return (ka*En2ka[-1]+2.0*En2ka[0]+term123)*np.exp(ka)
        def phidS1set():
            ka2 = IPs['ka']**2
            A3 = AnSet(n=3, ka=IPs['ka'])
            bet = En(5, IPs['ka'])/2.0+En(-1, IPs['ka'])
            integralTerm = A3*np.exp(IPs['ka'])-aleph(IPs['ka'])+bet
            return zeta_expka*ka2/(ka2+2.0*IPs['ka']+2.0)*integralTerm
        if ctrl['BC']['conductive'].get('s'):
            return 0.0
        else:
            phidS0 = -1.5*beta
            if ctrl['Sys']['m']['Diffu']: phidS1 = phidS1set()
            else: phidS1 = 0.0
            return phidS0+phidS1
    def muPhidSet(beta):
        if ctrl['BC']['conductive'].get('s') or not DL:
            return 0.0
        else:
            mu0 = 2.0/3.0*(IPs['ka']+1.0)*IPs['zeta']/(3.0*visEff+2.0)
            return mu0*phidSset(beta)
    En = np.vectorize(mpm.expint)
    zeta_expka = IPs['zeta']*np.exp(IPs['ka'])
    DL = ctrl['Sys']['p'] in 'DG'
    if DL:
        visEff = visEffSet(1.0)
        down = 9.0+6.0/visEff
    else:
        down = 9.0
    if ctrl['Sys']['m']['Diffu']: beta, muD = betaSet(), muDset()
    else: beta, muD = 1.0, 0.0
    muE = muEset(beta)
    muPhid = muPhidSet(beta)
    return float(IPs['ka']**2*zeta_expka/down*(muE+muD)+muPhid)
def HermansFujita():
    #rhoFix, ka, aldap
    #from: Sedimentation and Electrophoresis of Porous Spheres (1955)
    #condition: Single Porous, DC, rhoFix->0
    Tx = lambda x: 1.0-np.tanh(x)/x
    v = IPs['aldap']*np.sqrt(2.0/3.0)
    v2, ka2 = v**2, IPs['ka']**2
    Tka = Tx(IPs['ka'])
    temp = 1.0/IPs['ka']-(IPs['ka']+1.0)/(ka2-v2)*(1.0/Tka-v2/ka2/Tx(v))
    mu0 = IPs['rhoFix']/IPs['aldap']**2
    return mu0*(1.0-temp*v2*Tka*np.exp(-IPs['ka'])*np.cosh(IPs['ka']))
def StoutKhairTmY_Single():
    #zeta, ka, vis, Lc, DL
    #from: Continuum Approach to Predicting Electrophoretic Mobility Reversals (2014)
    #condition: DC, zeta->0, IL
    l_m1, m2 = l_m1m2Set()
    m1 = 1.0/l_m1
    if abs(IPs['kaLc']-0.5)>tol:
        Expint = np.vectorize(mpm.expint)
        E5m1, E5m2 = Expint(5, m1), Expint(5, m2)
        E3m1, E3m2 = Expint(3, m1), Expint(3, m2)
        temp1,temp2 = m1**2*(m1+1.0), m2**2*(m2+1.0)
        kaTerm1 = 1.0/m1+Exp(m1)/4.0*(E5m1-E3m1)
        kaTerm2 = 1.0/m2+Exp(m2)/4.0*(E5m2-E3m2)
        AAA = temp2/(temp2-temp1)
        kaTerm = AAA*kaTerm1+(1.0-AAA)*kaTerm2
        nokaTerm = 1.0+AAA*(m1-m2)+m2
        if ctrl['Sys']['p']=='D':
            DLkaTerm = AAA*mpm.exp(m1)*E5m1+(1.0-AAA)*Exp(m2)*E5m2
            DLterm = (2.0*nokaTerm+IPs['ka']**2*DLkaTerm)/(9.0*IPs['vis']+6.0)
        else:
            DLterm = 0.0
        RigidTerm = 2.0/3.0*(nokaTerm-IPs['ka']**2*kaTerm)
        return float(IPs['zeta']*np.real(RigidTerm+DLterm))
    else:
        return 0.0
def StoutKhairTmY_Cell():
    #zeta, ka, Lc, vis, ro, DL
    def AlephE(r):
        B1, B2, B3, B4 = PhidCoefficients()
        #aleph_E
        Lc2 = Lc**2
        l_r, Lc_r2, Lc2_r3 = 1.0/r, 2.0*Lc/r2, 2.0*Lc/r3
        expr = Exp(r/Lc)
        term1, term2 = 2.0*B1/r3, -B2
        term3 = B3*(-l_r+2.0*Lc_r2-2.0*Lc2_r3)*expr
        term4 = B4*(l_r+2.0*Lc_r2+2.0*Lc2_r3)/expr
        AlephEr = RealFloat(term1+term2+term3+term4)
        term1, term2 = -B1/r3, -B2
        term3, term4 = B3*(-Lc_r2+Lc2_r3)*expr, -B4*(Lc/r2+Lc2/r3)/expr
        AlephEtheta = RealFloat(term1+term2+term3+term4)
        return AlephEr, AlephEtheta
    def AlephV(r):
        C1, C2, C3, C4 = PsiCoefficients()
        #aleph_v
        AlephVr = -2.0*C1/r3-2.0*C2/r-2.0*C3-2.0*C4*r2
        AlephVtheta = C1/r3-C2/r-2.0*C3-4.0*C4*r2
        return AlephVr, AlephVtheta, C2
    def Dphie0():
        l_m1, m2 = l_m1m2Set()
        m1 = 1.0/l_m1
        AA0, AA3, AA4 = AA_set(m1=m1, m2=m2)
        term1 = -AA4*(m1-1.0)
        term2 = AA3*(m2-1.0)
        term3 = AA3*(-m2-1.0)
        term4 = -AA4*(-m1-1.0)
        return RealFloat(IPs['zeta']/AA0*(term1+term2+term3+term4))
    Lc = IPs['kaLc']/IPs['ka']
    r = np.linspace(1.0, IPs['ro'], Ngrid)
    r2 = r**2
    r3 = r2*r
    phieRef = DebyeHuckelPhi_CellIL(r)
    AlephEr, AlephEtheta = AlephE(r)
    AlephVr, AlephVtheta, C2 = AlephV(r)
    AlephTerm = 0.5*AlephEr*AlephVr+AlephEtheta*AlephVtheta
    FFF = IPs['ka']**2/3.0*simps(phieRef*AlephTerm*r2,r)
    qsTerm = 0.5*Dphie0()
    return (FFF+qsTerm)/C2
# =============================================================================
# mobility analytical solution (high ka)
# =============================================================================
def PrieveAndersonTmY():
    #beta, zeta, ka, vis, DL
    #from: Motion of a particle generated by chemical gradients. Part 2. Electrolytes, Perieve & Anderson (1984)
    #condition: Single HS, diffu, z1=z2=z, ka->oo
    if ctrl['Sys']['m']['Diffu']:
        beta = betaSet()
        DiffuTerm = 4.0*np.log(np.cosh(IPs['zeta']/4.0))
    else:
        beta = 1.0
        DiffuTerm = 0.0
    if ctrl['Sys']['p'] in 'DG':
        if ctrl['BC']['conductive']['s']:
            sinhzeta = np.sinh(IPs['zeta']/2.0)
            DLterm = 2.0*IPs['ka']/(visEffSet(1.0)*3.0+2.0)*beta*sinhzeta
        else:
            DLterm = 0.0
    else:
        DLterm = 0.0
    return beta*IPs['zeta']+DiffuTerm+DLterm
def OhshimaDL_HighKa(z):
    #zeta, ka, vis, Pec
    #from: Theory of colloid and interfacial electric phenomena (2006) P196
    #condition: Single DL, DC, z1=z2=z, ka->oo
    zeta_2 = IPs['zeta']/2.0
    exp_zeta_2 = np.exp(IPs['zeta']/2.0)
    l_exp_zeta_2_2 = (1.0-exp_zeta_2)**2
    DD = IPs['Pec'][2]*l_exp_zeta_2_2+IPs['Pec'][1]*(1.0-1.0/exp_zeta_2)**2
    temp = -3.0*IPs['Pec'][2]*l_exp_zeta_2_2*np.log((1.0+exp_zeta_2)/2.0)
    down = z*(IPs['vis']+2.0/3.0+DD)
    ka_sinh = IPs['ka']*np.sinh(zeta_2)
    vis_zeta = 1.5*IPs['vis']*IPs['zeta']
    return 2.0/3.0*np.sign(IPs['zeta'])/down*(ka_sinh+temp+vis_zeta)
def YarivBubble():
    #zeta, Pec
    #from: Electrophoresis of bubbles (2014)
    #condition: Single bubble, DC, Pec1=Pec2=Pec, ka->oo
    Pec = (IPs['Pec'][1]+IPs['Pec'][2])/2.0
    zeta_2 = IPs['zeta']/2.0
    coshzeta_2, sinhzeta_2 = np.cosh(zeta_2), np.sinh(zeta_2)
    sinh2zeta_4 = np.sinh(zeta_2/2.0)**2
    up = 4.0*((1.0+2.0*Pec)*sinhzeta_2-Pec*IPs['zeta']*coshzeta_2)*sinh2zeta_4
    down = coshzeta_2-8.0*Pec*sinh2zeta_4**2
    if abs(down)<tol: return 0.0
    else: return up/down
def Stone(phid):
    # from: Diffusiophoresis of a charged drop. Journal of Fluid Mechanics (2018)
    # condition: diffu, ka->oo
    tanhz_4 = np.tanh(IPs['zeta']/4.0)
    l_tanh2z_4 = 1.0-tanhz_4**2
    beta = betaSet()
    HSterm = -2.0*np.log(l_tanh2z_4)+beta*IPs['zeta']
    if ctrl['Sys']['p'] in 'DG':
        visEff = visEffSet(1.0)
        temp = 6.0*tanhz_4*(tanhz_4+beta)+4.0*tanhz_4*phid/l_tanh2z_4
        DLterm = 2.0/3.0/(3.0*visEff+2.0)*temp
    else:
        DLterm = 0.0
    return float(HSterm-DLterm)
def SquiresKhairTmY(r, nje, SZ):
    #from: Ion steric eﬀects on electrophoresis of a colloidal particle (2009)
    #condition: DC, ka->oo, IL
    ND = len(r)
    jIter = IPs['nj0'].keys()
    if ctrl['Sys']['OB']['Cell']:
        if SZ: temp = 1.0
        else: temp = 0.5
        ro_3 = temp/r[0,0]**3
    else:
        ro_3=0.0
    yy = IPs['ka']*(r[::-1, 0]-1.0)
    zhejk = np.empty((2, 3))
    # integral terms
    nje0 = {j: nje[j][::-1,0]-IPs['nj0'][j] for j in jIter}
    nje0Int = {j: simps(nje0[j], yy) for j in jIter}
    nje0yInt = {j: simps(yy*nje0[j], yy) for j in jIter}
    # double integral terms
    nje0yInt_0_i = {j: np.array([simps(yy[0:i+1]*nje0[j][0:i+1],yy[0:i+1]) \
                                 for i in range(ND)]) for j in jIter}
    nje0Int_i_inf = {j: np.array([simps(nje0[j][i:ND],yy[i:ND]) \
                                  for i in range(ND)]) for j in jIter}
    zhejk = {(j, 0): -nje0Int[j]/IPs['nj0'][j]/IPs['ka'] for j in jIter}
    c0 = sum(abs(np.array([i for i in IPs['zj'].values()])))
    if ctrl['Sys']['p']=='D':
        DLterm = {j: nje0Int[j]*IPs['ka']/(3.0*IPs['vis']+2.0) for j in jIter}
    else:
        DLterm = {j: 0.0 for j in jIter}
    for j in jIter:
        for k in (1, 2):
            nje0Int2 = simps(nje0[j]*nje0yInt_0_i[k], yy)
            njey0Int2 = simps(nje0[j]*yy*nje0Int_i_inf[k], yy)
            temp = IPs['Pec'][j]/IPs['nj0'][j]/c0/IPs['ka']
            zhejk[(j, k)] = temp*(-nje0Int[k]*DLterm[j]-nje0Int2-njey0Int2)
    ff1 = zhejk[(1, 0)]+zhejk[(1, 1)]
    ff2 = zhejk[(2, 0)]+zhejk[(2, 2)]
    gg1 = zhejk[(1, 2)]
    gg2 = zhejk[(2, 1)]
    alpha = -IPs['zj'][2]/IPs['zj'][1]
    temp1 = -0.5-ff1+alpha*gg1
    temp2 = 0.5*alpha+alpha*ff2-gg2
    roTemp1 = 1.0-ro_3
    roTemp2 = 1.0+0.5*ro_3
    down = roTemp2**2-(ff1+ff2)*roTemp1*roTemp2+(ff1*ff2-gg1*gg2)*roTemp1**2
    #Aj1
    Aj1 = {}
    Aj1[1] = (temp1*(roTemp2-ff2*roTemp1)+temp2*roTemp1*gg1)/down
    Aj1[2] = (temp2*(roTemp2-ff1*roTemp1)+temp1*roTemp1*gg2)/down
    #mu
    muTerm = {j: (-IPs['zj'][j]+(1.0-ro_3)*Aj1[j])*(DLterm[j]+nje0yInt[j]) \
              for j in jIter}
    return 2.0/3.0/(1.0+alpha)*(muTerm[1]+muTerm[2])
# =============================================================================
# mobility analytical solution (low ka)
# =============================================================================
def HuckelBoothTmY():
    if ctrl['Sys']['p'] in 'DG':
        if ctrl['BC']['conductive']['s']: c = 1.0
        else: c = -0.5
        DLterm = c/(visEffSet(1.0)*3.0+2.0)
    else:
        DLterm = 0.0
        c = 0.0
    return 2.0/3.0*IPs['zeta']*(1.0+DLterm)
# =============================================================================
# other function
# =============================================================================
def AA_set(m1, m2):
    def exp_ro_mr_Set():
        l_ro = 1.0/IPs['ro']
        ro_1 = IPs['ro']-1.0
        m1r, m2r = (m1+l_ro)/(m1-l_ro), (m2+l_ro)/(m2-l_ro)
        exp_ro1, exp_ro2 = Exp(-2.0*m1*ro_1), mpm.exp(-2.0*m2*ro_1)
        return exp_ro1*m1r, exp_ro2*m2r
    m12, m22 = m1**2, m2**2
    m13, m23 = m1**3, m2**3
    m13_m12, m23_m22 = m13-m12, m23-m22
    expro1m1r, expro2m2r = exp_ro_mr_Set()
    AA3 = (expro1m1r*(m13_m12)-(m13+m12))*expro2m2r
    AA4 = (expro2m2r*(m23_m22)-(m23+m22))*expro1m1r
    AA0 = (AA4+2.0*m23)/(m23_m22)*AA3-(AA3+2.0*m13)/(m13_m12)*AA4
    return AA0, AA3, AA4
def PhidCoefficients():
    Lc = IPs['kaLc']/IPs['ka']
    if ctrl['Sys']['OB']['Cell'] and abs(Lc)>tol:
        #bet
        ro2, Lc2 = IPs['ro']**2, Lc**2
        Lc_ro, Lc2_ro2 = Lc/IPs['ro'], Lc2/ro2
        expro = mpm.exp((IPs['ro']-1.0)/Lc)
        LcRatio = (1.0-2.0*Lc+2.0*Lc2)/(1.0+2.0*Lc+2.0*Lc2)
        term1 = -1.0/3.0+Lc_ro-Lc2_ro2
        term2 = 1.0/3.0+Lc_ro+Lc2_ro2
        bet1 = term1*expro+LcRatio*term2/expro
        bet2 = -(expro-LcRatio/expro)/6.0/(ro2*IPs['ro'])
        #B
        term0 = bet1+bet2
        expLc = mpm.exp(1.0/Lc)
        B1 = float(-0.5*bet1/term0)
        B2 = float(bet2/term0-1.0)
        B3 = float(0.5/ro2/expLc/term0)
        B4 = float(0.5/ro2*LcRatio*expLc/term0)
    else:
        B1, B2, B3, B4=-0.5, -1.0, 0.0, 0.0
    return B1, B2, B3, B4
def PsiCoefficients():
    #vis, ro, DL, Cell
    if ctrl['Sys']['OB']['Cell']:
        ro3, ro5, ro6  =  IPs['ro']**3, IPs['ro']**5, IPs['ro']**6
        HSterm0 = 4.0-20.0*ro3+36.0*ro5-20.0*ro6
        HSterm1 = 2.0*ro3-5.0*ro6
        HSterm2 = 15.0*ro6
        HSterm3 = -2.0+5.0*ro3-18.0*ro5
        HSterm4 = 3.0*ro3
        if ctrl['Sys']['p']=='D':
            term0 = IPs['vis']*HSterm0-4.0+24.0*ro5-20.0*ro6
            C1 = (IPs['vis']*HSterm1-2.0*ro3)/term0
            C2 = (IPs['vis']*HSterm2+10.0*ro6)/term0
            C3 = (IPs['vis']*HSterm3+2.0-12.0*ro5)/term0
            C4 = (IPs['vis']*HSterm4+2.0*ro3)/term0
        else:
            C1 = HSterm1/HSterm0
            C2 = HSterm2/HSterm0
            C3 = HSterm3/HSterm0
            C4 = HSterm4/HSterm0
    else:
        C1, C2, C3, C4=0.25, -0.75, 0.0, 0.0
    return C1, C2, C3, C4
# =============================================================================
# LiLiCoCo
# =============================================================================
def AnalyticalPhid(r):
    #ro, Cell
    Lc = IPs['kaLc']/IPs['ka']
    r2 = r**2
    if abs(Lc)>tol or ctrl['Sys']['OB']['Cell']:
        Lc2 = Lc**2
        B1, B2, B3, B4 = PhidCoefficients()
        expr = Exp(r/Lc)
        temp = B1/r2+B2*r+B3*(Lc/r-Lc2/r2)*expr+B4*(Lc/r+Lc2/r2)/expr
        return RealFloat(temp)
    else:
        Phid=B1/r2+B2*r
    return Phid
def AnalyticalPsi(r, U):
    C1, C2, C3, C4 = PsiCoefficients()
    Psi = (C1/r+C2*r+C3*r**2+C4*r**4)*U
    return Psi
def DL_psi_vRZ_Inside(r, q, DpsiS, Up):
    cosq, sinq = np.cos(q), np.sin(q)
    sinq2, r2 = sinq**2, r**2
    if ctrl['Sys']['p'] in 'GPSM':
        Wp = WmpSet(True)
        Wp2, Wpr = Wp**2, Wp*r
        sinhWp, coshWp = np.sinh(Wp), np.cosh(Wp)
        sinhWpr, coshWpr = np.sinh(Wpr), np.cosh(Wpr)
        Wcs = Wp*coshWp-sinhWp
        Wp2sinhWp = Wp2*sinhWp
        down = Wp2sinhWp-3.0*Wcs
        A1 = 0.5/down*(DpsiS+Up)
        A3 = 0.5/down*(-2.0*Wcs*DpsiS-(Wp2sinhWp-Wcs)*Up)
        psiI_1D = 2.0*A1*(Wp*coshWpr-sinhWpr/r)+A3*r2
        DpsiI_1D = 2.0*A1*(Wp2*sinhWpr-Wp*coshWpr/r+sinhWpr/r2)+2.0*A3*r
        vqI = sinq/r*DpsiI_1D
    else:
        psiI_1D = 0.5*r2*((DpsiS+Up)*(r2-1.0)-Up)
        vqI = ((DpsiS+Up)*(2.0*r2-1.0)-Up)*sinq
    vrI = -2.0*cosq/r**2*psiI_1D
    vRI, vZI = vrI*sinq+vqI*cosq, vrI*cosq-vqI*sinq
    return np.real(psiI_1D*sinq2), np.real(vRI), np.real(vZI)
def phid_Inside(r, q, phidS):
    return phidS*r*np.cos(q)
def LowZetaCurrentDensityInt(IPs, U):
    En = {i: float(mpm.expint(i, IPs['ka'])) for i in (0, 1, 3)}
    PeTerm = (En[0]+0.5*En[3])/IPs['Pec'][1]
    muTerm = (-0.75*En[1]+En[0]-0.25*En[3])*U
    temp = IPs['ka']**2*IPs['zeta']*np.exp(IPs['ka'])
    return 2.0*np.pi*temp*(PeTerm+muTerm)


