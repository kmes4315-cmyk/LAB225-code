import numpy as np
from gOCmethod import psiPDS, psiSign
from gCalculator import visEffSet, WmpSet, l_m1m2Set, njeSet, Sum_nj_Set
from gCalculator import UpSet, EeffForSites, Dnjeff_zjnjSet
from scipy.special import jn_zeros
IPs, OPs, ctrl = {}, {}, {} #changed by main program
sites = {\
         'a': {'O': ('ro', 's'), 'I': ('sI', 's')}, \
         'b': {'O': ('ax', 'p', 's'), 'I': ('ax', 'sI', 's')}, \
         'c': {'O': ('ax', 'qwA', 'qwB', 'w', 'u', 'd', 's'), \
               'I': ('ax', 'qwA', 'qwB', 'sI', 's')} \
        }
gj2j = lambda gj: int(gj[-2])
# =============================================================================
# interface
# =============================================================================
def VarsBCs(ABsub, Var, Phie=None):
    # parameters
    global phie
    phie = Phie
    global var, OI, key
    var, OI, key = Var, Var[-1], Var[:-2]
    global bis
    bis = (ctrl['Sys']['major']+OI=='bO')
    if key:
        global Eeff, Up
        Up = UpSet()
        Eeff = EeffForSites()
        Vars = ctrl['Sys']['dVars']
    else:
        Vars = ctrl['Sys']['eVars']
    global At, PD
    At, PD = OPs['At'][OI], OPs['PD'][OI]
    # domain loop
    global DM
    giveZ0 = (ctrl['Sys']['major']=='c' and (key in ('phi', 'g')))
    for DM in (*Vars, 'B'):
        # Z0
        if giveZ0: ABsub[DM][At['Z0']] = Z0AllBC()
        # psi additional ones
        if key=='ps':
            for site in sites[ctrl['Sys']['major']][OI]:
                if site!='ro' or not ctrl['Do']['a']['psiEq3']:
                    ABsub[DM][OPs['At_1'][OI][site]] = psiAddBCf(site)
        # phi additional ones
        if ctrl['Sys']['m']['IL']:
            global Lc
            Lc = IPs['kaLc']/IPs['ka']
            if var[:-1] in ('phid', ''):
                for site in sites[ctrl['Sys']['major']][OI]:
                    ABsub[DM][OPs['At_1'][OI][site]] = phiAddBCf(site)
        #others
        for site in sites[ctrl['Sys']['major']][OI]:
#            if VarsBCf(site) is None: print(var, DM, site)
            ABsub[DM][At[site]] = VarsBCf(site)
# =============================================================================
# interface (Note: At['I']['s'] is the core/center)
# =============================================================================
def VarsBCf(site):
    if site=='ro': return RadiusoBCs()
    elif site=='s': return SurfaceBCs()
    elif site=='sI': return sAllBC_Cont(10)
    elif site=='ax': return axAllBC(0 if key=='ps' else 1)
    elif site=='p': return PlaneBCs()
    elif site=='qwA': return qwAllBC(1)
    elif site=='qwB': return qwAllBC(0)
    elif site=='w': return WallBCs()
    elif site in 'ud': return EndBCs()(site)
def psiAddBCf(site):
    if site=='ro': return RadiusoBCs_psiAdd()
    elif site=='s': return SurfaceBCs_psiAdd()
    elif site=='sI': return SurfaceIBCs_psiAdd()
    elif site=='ax': return axAllBC(1)
    elif site=='p': return PlaneBCs_psiAdd()
    elif site=='qwA': return qwAllBC(3)
    elif site=='qwB': return qwAllBC(2)
    elif site=='w': return wPsiBC_Add()
    elif site in 'ud': return EndBCs_psiAdd()(site)
def phiAddBCf(site):
    if site=='ro': return RadiusoBCs_phiAdd()
    elif site=='s': return SurfaceBCs_phiAdd()
    elif site=='sI': return sAllBC_Cont(30)
    elif site=='ax': return axAllBC('DR(L2)')
    elif site=='qwA': return qwAllBC(3)
    elif site=='qwB': return qwAllBC(2)
    elif site=='w': return wPhiBC_Lc0()
    elif site in 'ud': return EndBCs_phiAdd()(site)
#-----surface-----#
ballOIset = lambda: ctrl['Sys']['p']+OI
def SurfaceBCs():
    ballOI = ballOIset()
    if ballOI in ('PO', 'SO', 'MO'):
        return sAllBC_Cont(0)
    elif ballOI in ('PI', 'DI', 'GI'): # DI only for psi
        if ctrl['Sys']['major']=='b':
            return sAllBC_Center(0 if key=='ps' else 10)
        elif ctrl['Sys']['major'] in 'ac': #anti-symmetric system
            return sAllBC_Center(10 if key=='' else 0)
    elif ballOI in ('RO', 'DO', 'GO', 'SI', 'MI'):
        if key=='':
            if ctrl['Sys']['m']['CR']:
                return sPhieBC_CR()
            else:
                if ctrl['BC']['zeta as sigma']: return sPhieBC_sigma()
                else: return sPhieBC_zeta()
        elif key=='g':
            return sGjBC_NoFlux()
        elif key=='phi':
            if ctrl['BC']['conductive']['s']: return sPhidBC_Conductive()
            else: return sPhidBC_NonConductive()
        elif key=='ps':
            return sPsiBC_Close('s')
    # RI won't appear
def SurfaceBCs_psiAdd():
    ballOI = ballOIset()
    if ballOI in ('PO', 'SO', 'MO'):
        return sPsiBC_ContTau2region()
    elif ballOI in ('PI', 'DI', 'GI'): # DI only for psi
        return sAllBC_Center(10)
    elif ballOI in ('DO', 'GO'):
        if ctrl['Sys']['major']=='a': return sPsiBC_ContTau1region()
        elif ctrl['Sys']['major'] in 'bc': return sPsiBC_ContTau2region()
    elif ballOI in ('RO', 'SI'):
        return sPsiBC_NoSlip()
    elif ballOI=='MI':
        return sPsiBC_ContTau1region()
    # RI won't appear
def SurfaceIBCs_psiAdd():
    ballOI = ballOIset()
    if ballOI in ('PI', 'SI', 'MI'): return sPsiBC_ContGradPs()
    elif ballOI in ('DI', 'GI'): return sPsiBC_Close('sI')
    # RI won't appear
def SurfaceBCs_phiAdd():
    ballOI = ballOIset()
    if ballOI in ('PO', 'SO', 'MO'): return sAllBC_Cont(20)
    elif ballOI=='PI': return sAllBC_Center(20 if key=='' else 10)
    elif ballOI in ('RO', 'DO', 'GO', 'SI', 'MI'): return sPhiBC_Lc0()
    # RI, DI won't appear
#-----radiusO-----#
def RadiusoBCs():
    if key=='':
        if ctrl['Sys']['OB']['Cell']:
            return roPhieBC_Cell()
        else:
            if ctrl['Sys']['m']['IL']: return roPhieBC_SingleIL()
            else: return roPhieBC_Single()
    elif key=='g':
        return roGjBC()
    elif key=='ps':
        if ctrl['Do']['a']['psiEq3']:
            if ctrl['Sys']['OB']['Cell']: return roPsiBC_NoCurl()
            else: return roPsiBC_Single3()
        else:
            if ctrl['Sys']['OB']['Cell']: return roPsiBC_Cell()
            else: return roPsiBC_Single()
    elif key=='phi':
        if ctrl['Sys']['OB']['Cell']:
            if ctrl['BC']['SZ']['phid']: return roPhidBC_CellSZ()
            else: return roPhidBC_CellLN()
        else:
            return roPhidBC_Single()
def RadiusoBCs_psiAdd():
    if ctrl['Sys']['OB']['Cell']: return roPsiBC_NoCurl()
    else: return roPsiBC_SingleAdd()
def RadiusoBCs_phiAdd():
    if key=='':
        if ctrl['Sys']['OB']['Cell']: return roPhieBC_CellILadd()
        else: return roPhieBC_SingleILadd()
    elif key=='phi':
        if ctrl['Sys']['OB']['Cell']:
            if ctrl['BC']['SZ']['phid']: return roPhidBC_CellLN()
            else: return roPhidBC_CellSZ()
        else:
            return roPhidBC_SingleILadd()
#-----plane-----#
def PlaneBCs():
    if key=='':
        if ctrl['BC']['conductive']['OB']: return pAllBC(0)
        else: return pAllBC(10)
    elif key=='phi':
        return pAllBC(0)
        # if ctrl['BC']['conductive']['OB']: return pAllBC(0)
        # else: return pAllBC(10)
    elif key=='g':
        return pGjBC_NoFlux()
    elif key=='ps':
        return pAllBC(0)
def PlaneBCs_psiAdd():
    if ctrl['Sys']['OB']['A-W']: return pPsiBC_AW()
    else: return pAllBC(10)
#-----wall-----#
def WallBCs():
    if key=='':
        if ctrl['Sys']['OB']['WallCharged'] or ctrl['BC']['conductive']:
            return wPhieBC_zetaW()
        else:
            return wPhieBC_ZeroSigmaW()
    elif key in ('g', 'phi'):
        return wPhidGjBC()
    elif key=='ps':
        return wPsiBC()
#-----end-----#
def EndBCs():
    if key=='':
        if ctrl['Sys']['OB']['WallCharged']: return endPhieBC_Charged
        else: return endPhieBC_noCharged
    elif key=='g':
        if ctrl['BC']['SZ']['gj']: return endGjBC_SZ
        else: return endGjBC_LN
    elif key=='ps':
        return endPsiBC
    elif key=='phi':
        if ctrl['BC']['SZ']['phid']: return endPhidBC_SZ
        else: return endPhidBC_LN
def EndBCs_psiAdd():
    return endPsiBC_Add
def EndBCs_phiAdd():
    if key=='':
        return endPhieBC_ILadd
    elif key=='phi':
        if ctrl['BC']['SZ']['phid']: return endPhidBC_LN
        else: return endPhidBC_SZ
# =============================================================================
# particle surface: common
# =============================================================================
# continuous BC
def sAllBC_Cont(order):
    def bisRHS(order):
        iS = OPs['At']['O']['s']
        if order==0:
            DZ = OPs['Z']['O'][iS]
        elif order==10:
            DZ = OPs['gradZ']['O']['n'][iS]/OPs['h']['O']['n'][iS]
        # elif order==2: pass
        # elif order==3: pass
        if key=='g':
            Dnjeff_zjnj0 = Dnjeff_zjnjSet(j=gj2j(var), nj=IPs['nj0'])
            factor = Eeff['inf']-Dnjeff_zjnj0
        elif key=='phi':
            factor = -Eeff['inf']
        return -factor*DZ
    if DM==var[:-1]+'O':
        return psiPDS(bisp=(ctrl['Sys']['major']+key=='bps'), \
                      PD=OPs['PD']['O'], order=order, iS=OPs['At']['O']['s'])
    elif DM==var[:-1]+'I':
        if key=='phi' and order==10 and ctrl['Sys']['p'] not in 'PSM':
            Ep_Em = IPs['epsilon']
        else:
            Ep_Em = 1.0
        return -Ep_Em*OPs['PD']['I'][order][OPs['At']['I']['sI']]
    elif DM=='B':
        if ctrl['Sys']['major']=='b' and key in ('phi', 'g'):
            return bisRHS(order)
        else:
            return 0.0
    else:
        return 0.0
# center (only for inside region)
def sAllBC_Center(order):
    if DM==var: return PD[order][At['s']]
    elif DM=='B': return 0.0
    else: return 0.0
# =============================================================================
# particle surface and core: phie
# =============================================================================
# constant zeta-potenial
def sPhieBC_zeta():
    if DM==var: return PD[0][At['s']]
    elif DM=='B': return IPs['zeta']
    else: return 0.0
# constant surface charge
def sPhieBC_sigma():
    if DM==var:
        return OPs['grad'][var]['n'][At['s']]
    elif DM=='B':
        return -IPs['zeta']
    else:
        return 0.0
# CR, CR[0]->A CR[1]->C CR[2]->B
def Cn3e2(n3e):
    return IPs['CR'][1]*IPs['CR'][2]*n3e**2
def CRdown(n3e):
    return Cn3e2(n3e)+IPs['CR'][2]*n3e*IPs['nj0'][3]+IPs['nj0'][3]**2
def CRfactor(n3e):
    return (IPs['nj0'][3]**2-Cn3e2(n3e))/CRdown(n3e)
def sPhieBC_CR():
    def CR_Amatrix(phie):
        nje = njeSet(phie[At['s']])
        if ctrl['Sys']['m']['IL']:
            nuTerm = IPs['nu']*Sum_nj_Set(nj=nje, order=1)
        else:
            nuTerm = 0.0
        Dn3eDphie = nje[3]*(nuTerm-1.0)
        C = IPs['CR'][1]*IPs['CR'][2]
        TwoCn3e = 2.0*C*nje[3]
        down = CRdown(nje[3])
        term1 = -TwoCn3e/down
        term2 = -CRfactor(nje[3])*(TwoCn3e+IPs['CR'][2]*IPs['nj0'][3])/down
        D0term = (term1+term2)*Dn3eDphie*IPs['CR'][0]*PD[0][At['s']]
        return OPs['grad'][var]['n'][At['s']]-D0term
    global phie
    if DM==var:
        return CR_Amatrix(phie)
    elif DM=='B':
        temp = CRfactor(njeSet(phie[At['s']])[3])*IPs['CR'][0]
        F = np.matmul(OPs['grad'][var]['n'][At['s']], phie)-temp
        DF = CR_Amatrix(phie)
        return np.matmul(DF, phie)-F
    else:
        return 0.0
# =============================================================================
# particle surface and core: gj and phid
# =============================================================================
# impermeable surface
def sGjBC_NoFlux():
    def RHS():
        if bis:
            temp = Eeff['inf']-Dnjeff_zjnjSet(j=gj2j(var), nj=IPs['nj0'])
            return -temp*OPs['gradZ'][OI]['n'][At['s']]
        else:
            return 0.0
    if DM==var: return OPs['grad'][OI]['n'][At['s']]
    elif DM=='B': return RHS()
    else: return 0.0
# impermeable surface
def sPhidBC_NonConductive():
    def aPhidIfactor():
        hn = OPs['h'][OI]['n'][At['s']]
        return IPs['epsilon']*hn*PD[0][At['s']]/OPs['n'][OI][At['s']]
    if DM==var:
        if ctrl['Sys']['major']=='a' and not ctrl['BC']['Em>>Ep']:
            EpEmTerm = aPhidIfactor()
        else:
            EpEmTerm = 0.0
        return OPs['grad'][OI]['n'][At['s']]-EpEmTerm
    elif DM=='B':
        return (Eeff['inf']*OPs['gradZ'][OI]['n'][At['s']]) if bis else 0.0
    else:
        return 0.0
def sPhidBC_Conductive():
    if DM==var: return PD[0][At['s']]
    elif DM=='B': return (Eeff['inf']*OPs['Z'][OI][At['s']]) if bis else 0.0
    else: return 0.0
# =============================================================================
# particle surface and core: psi
# =============================================================================
# shear stress continuous BC (droplet)
sigma = lambda site: -OPs['grad(phie)'][OI]['n'][At[site]]
def sPsiBC_ContTau1region():
    if DM==var:
        r = OPs['n'][OI][At['s']]
        r2 = r**2
        term1 = -(3.0*visEffSet(r)+2.0)/r2*PD[10][At['s']]
        alda2 = 0.0
        if ctrl['BC'].get('tauDBB'):
            if ctrl['Sys']['m']['Gel']: alda2 = alda2-IPs['aldam']**2
            if ctrl['Sys']['p']=='G': alda2 = alda2+IPs['aldap']**2
        term0 = (2.0/r2+alda2*r)*PD[0][At['s']]
        return PD[20][At['s']]/r+term1+term0
    elif DM=='phidO' and ctrl['BC'].get('MWstress'):
        return -sigma('s')*OPs['grad'][OI]['s'][At['s']]
    elif DM=='B':
        vis3 = 3.0*visEffSet(OPs['n'][OI][At['s']])
        return vis3*Up if ctrl['BC']['infRef'] else 0.0
    else:
        return 0.0
def sPsiBC_ContTau2region():
    def psiTermSet(DMOI):
        if DMOI=='O':
            sign = 1.0
            site = OPs['At']['O']['s']
        elif DMOI=='I':
            sign = -1.0
            site = OPs['At']['I']['sI']
        if ctrl['Sys']['p'] in 'DG':
            if DMOI=='O': vis = 1.0
            elif DMOI=='I': vis = IPs['vis']
            taunsTerm = vis*OPs['PD'][DMOI]['tau_ns_surf']
        elif ctrl['Sys']['p'] in 'PSM':
            hn2 = OPs['h'][DMOI]['n'][site]**2
            PD0 = psiPDS(bisp=(ctrl['Sys']['major']+DMOI=='bO'), \
                         PD=OPs['PD'][DMOI], order=20, iS=site)
            taunsTerm = hn2*PD0
        if ctrl['BC'].get('tauDBB'):
            PD0 = psiPDS(bisp=(ctrl['Sys']['major']+DMOI=='bO'), \
                         PD=OPs['PD'][DMOI], order=0, iS=site)
            if DMOI=='O' and ctrl['Sys']['m']['Gel']:
                alda2 = IPs['aldam']**2
            elif DMOI=='I' and ctrl['Sys']['p'] in 'GPSM':
                alda2 = IPs['aldap']**2
            else:
                alda2 = 0.0
            aldaTerm = -alda2*PD0
        else:
            aldaTerm = 0.0
        return sign*(taunsTerm+aldaTerm)
    def RHSset():
        if ctrl['Sys']['major']+ctrl['Sys']['p'] in ('bD', 'bG'):
            if ctrl['BC'].get('MWstress'):
                esTerm = sigma('s')*OPs['gradZ'][OI]['s'][At['s']]
                return -Eeff['inf']*OPs['R'][OI][At['s']]*esTerm
            else:
                return 0.0
        else:
            if ctrl['BC'].get('tauDBB'):
                if ctrl['BC']['infRef'] and ctrl['Sys']['m']['Gel']:
                    alda2 = IPs['aldam']**2
                elif not ctrl['BC']['infRef'] and ctrl['Sys']['p'] in 'GPSM':
                    alda2 = IPs['aldap']**2
                else:
                    alda2 = 0.0
                return alda2*0.5*Up*OPs['R']['O'][At['s']]**2
            else:
                return 0.0
    if DM[:-1]=='psi':
        return psiTermSet(DM[-1])
    elif DM=='phidO' and ctrl['Sys']['p'] in 'DG':
        if ctrl['BC'].get('MWstress'):
            esTerm = sigma('s')*OPs['grad'][OI]['s'][At['s']]
            return -OPs['R'][OI][At['s']]*esTerm
        else:
            return 0.0
    elif DM=='B':
        return RHSset()
    else:
        return 0.0
# tangential pressure gradient continuous BC (porous and soft)
def sPsiBC_ContGradPs():
    def sinsSet(DMOI):
        if ctrl['Sys']['major']=='a':
            return 1.0
        elif ctrl['Sys']['major'] in 'bc':
            if DMOI in ('O', 'B'): s = OPs['s']['O'][OPs['At']['O']['s']]
            elif DMOI=='I': s = OPs['s']['I'][OPs['At']['I']['sI']]
            return np.sin(s)
    def psiTermSet(DMOI):
        if DMOI=='O':
            sign = 1.0
            alda2 = IPs['aldam']**2 if ctrl['Sys']['m']['Gel'] else 0.0
            site = OPs['At']['O']['s']
        elif DMOI=='I':
            sign = -1.0
            alda2 = IPs['aldap']**2 if ctrl['Sys']['p'] in 'GPSM' else 0.0
            site = OPs['At']['I']['sI']
        bisp = ctrl['Sys']['major']+DMOI=='bO'
        D3n = psiPDS(bisp=bisp, PD=OPs['PD'][DMOI], order=30, iS=site)
        if (DMOI=='O' and ctrl['Sys']['m']['Gel']) or DMOI=='I':
            sins = sinsSet(DMOI)
            Dn = psiPDS(bisp=bisp, PD=OPs['PD'][DMOI], order=10, iS=site)
            aldaTerm = -alda2*sins*Dn
        else:
            aldaTerm = 0.0
        return sign*(D3n+aldaTerm)
    def RHSset():
        if ctrl['BC']['infRef'] or ctrl['Sys']['m']['Gel']:
            if ctrl['BC']['infRef']: alda2 = IPs['aldap']**2
            elif ctrl['Sys']['m']['Gel']: alda2 = IPs['aldam']**2
            hn = OPs['h']['O']['n'][OPs['At']['O']['s']]
            R = OPs['R']['O'][OPs['At']['O']['s']]
            isiZ = OPs['gradZ']['O']['s'][OPs['At']['O']['s']]
            sins = sinsSet('B')
            return alda2*Up/hn*R*isiZ*sins
        else:
            return 0.0
    if DM[:-1]=='psi': return psiTermSet(DM[-1])
    elif DM=='B': return psiSign[ctrl['Sys']['major']=='b']*RHSset()
    else: return 0.0
# closed particle surface (rigid and droplet)
def sPsiBC_Close(site):
    if DM==var:
        return psiPDS(bisp=bis, PD=PD, order=0, iS=At[site])
    elif DM=='B':
        if ctrl['BC']['infRef']:
            return -0.5*Up*OPs['R'][OI][At[site]]**2
        else:
            return 0.0
    else:
        return 0.0
# non-slip BC (rigid)
def sPsiBC_NoSlip():
    if DM==var:
        Dn = psiPDS(bisp=bis, PD=PD, order=10, iS=At['s'])
        return OPs['h'][OI]['n'][At['s']]*Dn
    elif DM=='B':
        if ctrl['BC']['infRef']:
            if bis: DRDn = OPs['gradZ'][OI]['s'][At['s']]
            else: DRDn = -OPs['gradZ'][OI]['s'][At['s']]
            return -OPs['R'][OI][At['s']]*Up*DRDn
        else:
            return 0.0
    else:
        return 0.0
# =============================================================================
# virtual outer surface (only for outside region)
# =============================================================================
#-----phie-----#
def roPhieBC_Single():
    if DM=='O':
        ka_l_ro = IPs['ka']+1.0/OPs['n']['O'][At['ro']]
        return PD[10][At['ro']]+ka_l_ro*PD[0][At['ro']]
    elif DM=='B':
        return 0.0
    else:
        return 0.0
def roPhieBC_Cell():
    if DM=='O': return PD[10][At['ro']]
    elif DM=='B': return 0.0
    else: return 0.0
#-----gj-----#
def roGjBC():
    j = gj2j(var)
    if DM in (var, 'phidO'):
        return PD[0][At['ro']]
    elif DM=='B':
        nje = {j: OPs['nje']['O'][j][At['ro']] for j in OPs['nje']['O'].keys()}
        return -Dnjeff_zjnjSet(j=j, nj=nje)*OPs['n']['O'][At['ro']]
    else:
        return 0.0
#-----psi-----#
def roPsiBC_Single():
    if DM=='psiO':
        Wm = WmpSet(False)
        ro = OPs['n']['O'][At['ro']]
        PD = {i: OPs['PD']['O'][i][At['ro']] for i in (0, 10, 20)}
        return PD[20]+(Wm+1.0/ro)*PD[10]+(Wm/ro-1.0/ro**2)*PD[0]
    elif DM=='B':
        if ctrl['BC']['infRef']: return 0.0
        else: return 1.5*(WmpSet(False)*OPs['n']['O'][At['ro']]+1.0)*Up
    else:
        return 0.0
def roPsiBC_Cell():
    if DM=='psiO':
        return PD[0][At['ro']]
    elif DM=='B':
        if ctrl['BC']['infRef']: return 0.0
        else: return 0.5*Up*OPs['n']['O'][At['ro']]**2
    else:
        return 0.0
def roPsiBC_SingleAdd():
    if DM=='psiO':
        ro2 = OPs['n']['O'][At['ro']]**2
        ro3 = ro2*OPs['n']['O'][At['ro']]
        Wm = WmpSet(False)
        term32 = PD[30][At['ro']]+Wm*PD[20][At['ro']]
        term1 = -3.0/ro2*PD[10][At['ro']]
        term0 = (3.0/ro3-2.0*Wm/ro2)*PD[0][At['ro']]
        return term32+term1+term0
    elif DM=='B':
        if ctrl['BC']['infRef']: return 0.0
        else: return -1.5/OPs['n']['O'][At['ro']]*Up
    else:
        return 0.0
def roPsiBC_Single3():
    if DM=='psiO':
        ro = OPs['n']['O'][At['ro']]
        ro2 = ro**2
        Wmro = WmpSet(False)*ro
        WmFactor = Wmro+1.0/(Wmro+1.0)
        term32 = PD[30][At['ro']]+PD[20][At['ro']]*WmFactor/ro
        term1 = -2.0/ro2*PD[10][At['ro']]
        term0 = 2.0/(ro*ro2)*(2.0-WmFactor)*PD[0][At['ro']]
        return term32+term1+term0
    elif DM=='B':
        return 0.0
    else:
        return 0.0
def roPsiBC_NoCurl():
    if DM=='psiO': return OPs['PD']['O']['E2'][OPs['At']['O']['ro']]
    elif DM=='B': return 0.0
    else: return 0.0
#-----phid-----#
def roPhidBC_CellSZ():
    if DM=='phidO': return PD[0][At['ro']]
    elif DM=='B': return -Eeff['ro']*OPs['n']['O'][At['ro']]
    else: return 0.0
def roPhidBC_CellLN():
    if DM=='phidO': return PD[10][At['ro']]
    elif DM=='B': return -Eeff['ro']
    else: return 0.0
def roPhidBC_Single():
    if DM=='phidO':
        l_ro = 1.0/OPs['n']['O'][At['ro']]
        if ctrl['Sys']['m']['IL']:
            LcTerm = Lc*PD[20][At['ro']]+3.0*Lc*l_ro*PD[10][At['ro']]
        else:
            LcTerm = 0.0
        return PD[10][At['ro']]+2.0*l_ro*PD[0][At['ro']]+LcTerm
    elif DM=='B':
        if ctrl['Sys']['m']['IL']: LcTerm = Lc/OPs['n']['O'][At['ro']]
        else: LcTerm = 0.0
        return -3.0*(1.0+LcTerm)*Eeff['inf']
    else:
        return 0.0
# =============================================================================
# plane (only for outside region)
# =============================================================================
def pAllBC(order):
    if DM==var: return PD[order][At['p']]
    elif DM=='B': return 0.0
    else: return 0.0
def pGjBC_NoFlux():
    if DM in (var, 'phidO'): return PD[0][At['p']]
    elif DM=='B': return 0.0
    else: return 0.0
def pPsiBC_AW():
    if DM=='psiO':
        return PD['tau_ns_plane']
    elif DM=='phidO':
        esTerm = sigma('p')*OPs['grad'][OI]['s'][At['p']]
        gradphie_s = OPs['grad(phie)'][OI]['s'][At['p']]
        seTerm = -gradphie_s*OPs['grad'][OI]['n'][At['p']]
        return -OPs['R'][OI][At['p']]*(esTerm+seTerm)
    elif DM=='B':
        esTerm = sigma('p')*OPs['gradZ'][OI]['s'][At['p']]
        gradphie_s = OPs['grad(phie)'][OI]['s'][At['p']]
        seTerm = -gradphie_s*OPs['gradZ'][OI]['n'][At['p']]
        return -Eeff['inf']*OPs['R'][OI][At['p']]*(esTerm+seTerm)
    else:
        return 0.0
# =============================================================================
# wall (only for outside region)
# =============================================================================
#-----phie-----#
def wPhieBC_zetaW():
    if DM=='O': return PD[0][At['w']]
    elif DM=='B': return IPs['zetaW']
    else: return 0.0
def wPhieBC_ZeroSigmaW():
    if DM=='O': return PD['D1R'][At['w']]
    elif DM=='B': return 0.0
    else: return 0.0
#-----phid and gj-----#
def wPhidGjBC():
    if DM==var:
        if ctrl['BC']['conductive']['OB']: return PD[0][At['w']]
        else: return PD['D1R'][At['w']]
    elif DM=='B':
        return 0.0
    else:
        return 0.0
#-----psi-----#
def wPsiBC():
    def RHS():
        if ctrl['BC']['infRef']: Uterm = 0.0
        else: Uterm = 0.5*Up*OPs['R']['O'][At['w']]**2
        if ctrl['Sys']['OB']['WallCharged']:
            EOFterm = OPs['psioo']['u'][0]*Eeff['u'][-1]
        else:
            EOFterm = 0.0
        return Uterm+EOFterm
    if DM==var: return PD[0][At['w']]
    elif DM=='B': return RHS()
    else: return 0.0
def wPsiBC_Add():
    if DM==var:
        return PD['D1R'][At['w']]
    elif DM=='B':
        if ctrl['BC']['infRef']: return 0.0
        else: return (Up*OPs['R']['O'][At['w']])
    else:
        return 0.0
# =============================================================================
# cylinder end (only for outside region)
# =============================================================================
#-----phie-----#
def endPhieBC_noCharged(UD):
    if DM=='O':
        sign = np.sign(np.pi/2.0-OPs['s']['O'][At[UD]])
        D0tem = sign*jn_zeros(1, 1)/IPs['ro0']['W']*PD[0][At[UD]]
        return PD['D1Z'][At[UD]]+D0tem
    elif DM=='B':
        return 0.0
    else:
        return 0.0
def endPhieBC_Charged(UD):
    if DM=='O': return PD[0][At[UD]]
    elif DM=='B': return OPs['phieoo'][UD]
    else: return 0.0
#-----gj-----#
def endGjBC_SZ(UD):
    j = gj2j(var)
    if DM==var or DM=='phidO':
        return PD[0][At[UD]]
    elif DM=='B':
        nje = {j: OPs['nje']['O'][j][At[UD]] for j in OPs['nje']['O'].keys()}
        Dnjeff_zjnj = Dnjeff_zjnjSet(j=j, nj=nje)
        return -Dnjeff_zjnj*OPs['Z']['O'][At[UD]]
    else:
        return 0.0
def endGjBC_LN(UD):
    j = gj2j(var)
    if DM==var or DM=='phidO':
        DZ = PD['D1Z'][At[UD]]
        DphieDZ = np.matmul(DZ, OPs['phie']['O'])
        return -IPs['zj'][j]*DphieDZ*PD[0][At[UD]]+DZ
    elif DM=='B':
        nje = {j: OPs['nje']['O'][j][At[UD]] for j in OPs['nje']['O'].keys()}
        Dnjeff_zjnj = Dnjeff_zjnjSet(j=j, nj=nje)
        return -Dnjeff_zjnj
    else:
        return 0.0
#-----psi-----#
def endPsiBC(UD):
    if DM=='psiO':
        return PD[0][At[UD]]
    elif DM=='B':
        if ctrl['BC']['infRef']: Uterm = 0.0
        else: Uterm = 0.5*Up*OPs['Rend'][UD]**2
        if ctrl['Sys']['OB']['WallCharged']:
            EOFterm = OPs['psioo'][UD]*Eeff[UD]
        else:
            EOFterm = 0.0
        return Uterm+EOFterm
    else:
        return 0.0
def endPsiBC_Add(UD):
    if DM==var: return PD['D1Z'][At[UD]]
    elif DM=='B': return 0.0
    else: return 0.0
#-----phid-----#
def endPhidBC_SZ(UD):
    if DM==var: return PD[0][At[UD]]
    elif DM=='B': return -Eeff[UD]*OPs['Z']['O'][At[UD]]
    else: return 0.0
def endPhidBC_LN(UD):
    if DM==var: return PD['D1Z'][At[UD]]
    elif DM=='B': return -Eeff[UD]
    else: return 0.0
# =============================================================================
# symmetric axis (same form for both region)
# =============================================================================
def axAllBC(order):
    if DM==var: return PD[order][At['ax']]
    elif DM=='B': return 0.0
    else: return 0.0
# =============================================================================
# Z = 0 (theta = pi/2) (same form for both region)
# =============================================================================
def Z0AllBC():
    if DM==var and key in ('g', 'phi'): return PD[0][At['Z0']]
    elif DM=='B': return 0.0
    else: return 0.0
# =============================================================================
# thetaW (same form for both region)
# =============================================================================
def qwAllBC(order):
    if DM==var: return PD[order][At['qwA']]-PD[order][At['qwB']]
    elif DM=='B': return 0.0
    else: return 0.0
# =============================================================================
# ionic liquid
# =============================================================================
#-----surface-----#
# negligible Lc
def sPhiBC_Lc0():
    if ctrl['Sys']['major']=='a' and key=='': DrL2 = 'Dr(L2_r)'
    else: DrL2 = 'Dr(L2)'
    if DM==var:
        if ctrl['BC']['L3=L2']: return Lc*PD[DrL2][At['s']]-PD['L2'][At['s']]
        else: return PD[DrL2][At['s']]
    elif DM=='B':
        return 0.0
    else:
        return 0.0
#-----radiusO-----#
# phie
def roPhieBC_SingleIL():
    site = OPs['At']['O']['ro']
    if DM=='O':
        PDO = {i: OPs['PD']['O'][i][site] for i in (0, 10, 20)}
        l_ro = 1.0/OPs['n']['O'][site]
        l_m1, m2 = l_m1m2Set()
        term0 = ((1.0+m2*l_m1)*l_ro+m2)*PDO[0]
        return np.real(l_m1*PDO[20]+(2.0*l_ro*l_m1+1.0+m2*l_m1)*PDO[10]+term0)
    elif DM=='B':
        return 0.0
    else:
        return 0.0
def roPhieBC_SingleILadd():
    if DM=='O':
        l_m1, m2 = l_m1m2Set()
        l_m1ro = l_m1/OPs['n']['O'][At['ro']]
        m22 = m2**2
        term3 = l_m1*PD[30][At['ro']]
        term2 = (3.0*l_m1ro+1.0)*PD[20][At['ro']]
        term1 = (2.0/OPs['n']['O'][At['ro']]-m22*l_m1)*PD[10][At['ro']]
        term0 = -(l_m1ro+1.0)*m22*PD[0][At['ro']]
        return np.real(term3+term2+term1+term0)
    elif DM=='B':
        return 0.0
    else:
        return 0.0
def roPhieBC_CellILadd():
    if DM=='O':
        l_ro = 1.0/OPs['n']['O'][At['ro']]
        term32 = PD[30][At['ro']]+2.0*l_ro*PD[20][At['ro']]
        term1 = -2.0*l_ro**2*PD[10][At['ro']]
        return (term32+term1)
    elif DM=='B':
        return 0.0
    else:
        return 0.0
# phid
def roPhidBC_SingleILadd():
    if DM=='phidO':
        Lc_ro = Lc/OPs['n']['O'][At['ro']]
        term3 = Lc*PD[30][At['ro']]
        term2 = (3.0*Lc_ro+1.0)*PD[20][At['ro']]
        term1 = (2.0-3.0*Lc_ro)/OPs['n']['O'][At['ro']]*PD[10][At['ro']]
        term0 = -2.0/OPs['n']['O'][At['ro']]**2*PD[0][At['ro']]
        return term3+term2+term1+term0
    elif DM=='B':
        return 3.0*Lc/OPs['n']['O'][At['ro']]**2*Eeff['inf']
    else:
        return 0.0
#-----wall-----#
# negligible Lc
def wPhiBC_Lc0():
    if DM==var:
        if ctrl['BC']['L3=L2']:
            return Lc*PD['DR(L2)'][At['w']]-PD['L2'][At['w']]
        else:
            return PD['DR(L2)'][At['w']]
    elif DM=='B':
        return 0.0
    else:
        return 0.0
#-----end-----#
def endPhieBC_ILadd(UD):
    if DM=='O': return PD['D1Z'][At[UD]]
    elif DM=='B': return 0.0
    else: return 0.0