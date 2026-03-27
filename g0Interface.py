import numpy as np
from winsound import Beep
from time import time
from copy import deepcopy
from gMain import version, MainProgram
from gBegin import PrintBlock, SkipCheck, TimeMessageSet
from gFigure import createFile, writeFile
from itertools import product  
# from gFigure import createFile, writeFile, packingFile

ctrl = {} # used in all module
ctrlL = {} #used in loop control
PrintBlock(' Program  Start (version %s) '%version)
# =============================================================================
# system choose
# =============================================================================
ctrl['Sys'] = \
    {\
     'major': {'2D': True, 'Bispherical': False}, \
     'p': {'DL': True, 'Porous': True, 'Core': False}, \
     'm': {'Diffu': False, 'AC': False, 'Gel': False, \
           'IL': False, 'CR': False}, \
     'OB': {'Cell': False, 'A-W': False, 'WallCharged': False} \
    }
ctrl['BC'] = {'conductive': {'s': False, 'OB': False}, 'SPB': False}
# 'major' for chosing 1D, plane, cylinder systems
    # '2D': True=2D systems, False: 1D system
    # Bispherical: True=plane system, False=cylinder system
# 'p' for particle
    # 'DL': True=two region with closed surface (droplet, DBB droplet)
    #       False=one region or open surface
    # 'Porous': True=DBB inside the particle
    #           False=Newtonian inside the particle
    # 'Core': [only valid for Porous=True]
    #         True=soft particle, False=porous particle
    #         if DL=True and 2D=False: droplet as core
# In short, (DL, Porous, Core)
    # Rigid particle: (F, F, T or F) -> R (R for Rigid)
    # Newtonian Droplet: (T, F, T or F) -> D (D for Droplet)
    # DBB Droplet: (T, T, T or F) -> G (G for Gel)
    # Porous particle: (F, T, F) -> P (P for Porous)
    # Soft particle: (F, T, T) -> S (S for Soft)
    # Soft particle with slip core: (T, T, T) -> M (M for Micelle)
# 'm' for modification or media -1.2
    # 'Diffu': True=diffusiophoresis, False=electrophoresis
    # 'AC': [only vaild for Diffu=False] True=AC, False=DC
    # 'Gel': True=DBB fluid outside the particle, False=Newtonian fluid
    # 'CR': True=charge regulation (constant surface charge is included),
    #       False=constant surface potential
# 'OB' for outer boundary, only vaild in a given specific system
# 'Cell': True=suspension, False=single
# 'A-W': True=air-water interface, False=solid plane

# 'WallCharged':
    # True=charged cylinder (i.e. need Osmotic flow calculation)
    # False=uncharged cylinder
ctrl['BC'].update({\
                   'SZ': {'phid': True}, # default: True
                   'L3=L2': False, # default: False
                   'zeta as sigma': False, # default: False
                   'Em>>Ep': True, # default: True
                   'infRef': False, # default: False
                   'tauDBB': False, # default: False
                   'MWstress': True # default: True
                   })
# 'SZ': True=SZ type, False=LN type
    # [only vaild for a-Cell and c systems]
    # 'gj' will be inserted at BC_OverWrite
    # 'gj'=True for electrophoresis
    # 'gj'=False for diffusiophoresis
# 'conductive': mobile surface charge or immobile surface charge
    # 's': particle surface [only vaild for rigid or droplet]
        #True-> phid=0 (conductive), False->d phid/d qn = 0 (dielectric)
    # 'OB': outer boundary [only vaild for cylinder and solid plane]
        # plane:
            #True->phie=0, False->d phie/d qn = 0
            # default: True
        # cylinder:
            # if WallCharged:
                #phie=zetaW, True->phid=0, False->d phid/d qn = 0
                # default: False
            # else:
                # True->phie=0 & phid=0
                # False->d phie/d qn = 0 & d phid/d qn = 0
                # default: False
# 'L3=L2': only vaild for IL, Bazant 2011 or 2019 BC
    # True=use Bazant 2019 BC, False=use Bazant 2011 BC
# 'zeta as sigma':
    # True=surface charge is zeta, False=surface potential is zeta
# 'Ep>>Em':
    # [only vaild for 1D non-conductive rigid/droplet]
    # True=neglect phid inside contribution, False=consider the contribution
# 'intRef': where the velocity is given  or particle surface
    # True=velocity is given at particle surface
    # False=velocity is given at infinite far
    # for plane system, velocity is always given at surface,
    # if infRef=False, psi will add 0.5*Up*R**2
# 'SPB': [only valid for soft particle]
    # i.e. spherical polyelectrolyte brushes
    # True=rhoFix with 1/r distribution, False=uniform distrubution
# 'tauDBB': [only vaild for Gel=True or Porous=True]
    # True=consider tauDBB False=not consider tauDBB
# =============================================================================
# parameter data points
# =============================================================================
ctrlData = \
    {\
    'ND': [{'nO': 60, 'nI': 25, 'sU': 15, 'sW': 21, 'sD': 15}], \
    # 'ka': np.logspace(-2, 4, 60+1), \
    'ka': [0.01, 0.1, 1, 10], \
    'Pec': [{1: Pe, 2: Pe} for Pe in (0.26, )], \
    # 'Pec': [{1: 0.39, 2: 0.55}],\
    # 'zeta': np.linspace(2.03, 2.03, 1).tolist(), \
    'zeta': [0.1, 1, 2, 3, 4], \
    'vis': [1], \
    # 'vis': [1], \
    # 'aldam': [1.0], \
    # 'aldap': [0, 1, 3, 10 ,100 ,1000 ], \
    'aldap': [0, 1, 3, 10, 100, 1000], \
    # 'aldap': np.logspace(-1, 3, 40+1), \
    'rhoFix': [30.0], \
    'rc': [1e-6], \
    'n30': [1e-12], \
    'CR': [{0: 100.0, 2: 100.0, 1: 0.0}], \
    'w': np.logspace(5, -3, 80+1).tolist(), \
    'NR': [50], \
    'H': [1e-3, 1e-2, 1e-1, 0.4], \
    'h': [1.1], \
    # 'ro0': [{'U': 3.0*Rw, 'W': Rw, 'D': 3.0*Rw} for Rw in (1.2, 1.5, 1.8, 2, 3, 5) ], \
    'ro0': [{'U': 3.0*Rw, 'W': Rw, 'D': 3.0*Rw} for Rw in np.linspace(1.1, 50, 50+1).tolist()], \
# 1.1, 1.3, 1.5, 1.7, 1.9, 2.1, 2.3, 2.5, 2.7, 2.9, 3.1, 3.3, 3.5, 3.7, 3.9, 4.1, 4.3, 4.5, 4.7, 4.9, 5.1, 5.3, 5.5, 5.7, 5.9, 6.1, 6.3, 6.5, 6.7, 6.9, 7.1, 7.3, 7.5, 7.7, 7.9, 8.1, 8.3, 8.5, 8.7, 8.9, 9.1, 9.3, 9.5, 9.7, 9.9, 10.1, 10.3, 10.5, 10.7, 10.9, 11.1, 11.3, 11.5, 11.7, 11.9, 12.1, 12.3, 12.5, 12.7, 12.9, 13.1, 13.3, 13.5, 13.7, 13.9, 14.1, 14.3, 14.5, 14.7, 14.9, 15.1, 15.3, 15.5, 15.7, 15.9, 16.1, 16.3, 16.5, 16.7, 16.9, 17.1, 17.3, 17.5, 17.7, 17.9, 18.1, 18.3, 18.5, 18.7, 18.9, 19.1, 19.3, 19.5, 19.7, 19.9, 20.0
    'zetaW': np.linspace(-3, 3, 2+1).tolist(), \
    'kaLc': np.linspace(1e-6, 1e-6, 0+1).tolist(), \
    'nu': np.linspace(1e-6, 1e-6, 0+1), \
    }
# 'ND': the number of grid 
    # 'n': normal direction, 's': tangential direction
    # 'nO': outer region, 'nI': inner region
    # for cylinder, 'sU': up region, 'sW': wall region, 'sD': down region
    # for plane, 's'='sU'+'sW'+'sD'
    # for single, 's'='sU'+'sW'+'sD', only used in contour plot
    # typical values
        # single 'nO'=100~300, usually 150
        # plane 'nO'=30~100, 's'=30~50, usually (30, 30),
        # cylinder, 'nO'=30~50, 'sU'='sD'=10~30, 'sW'=30~50
        # 'nI'<'nO'
# 'ka': dimensionless reciprocal of Debye length (kappa a)
# 'Pec': Peclet number of each species of ion
    # Some example of Pec
    # H2CO3[0.056, 0.442], HCl[0.056, 0.26], NaH2PO4[0.39, 0.55]
    # KCl[0.26, 0.26], NaCl[0.39, 0.26], KOH[0.26, 0.099], NaOH[0.39, 0.099]
# 'zeta':
    # [only vaild for CR=False]
    # dimensionless zeta-potential of the particle
# 'vis':
    # [only vaild for DL=True]
    # viscosity ratio = viscosity of particle/viscosity of media
# 'aldam
    # [only vaild for Gel=True]
    # dimensionless drag coefficient of DBB fluid outside the particle
# 'aldap
    # [only vaild for Porous=True]
    # dimensionless drag coefficient of DBB fluid inside the particle
# 'rhoFix':
    # [only vaild for porous and soft particle]
    # dimensionless fixed charge density inside the porous
# 'rc':
    # [only vaild for porous and soft particle]
    # shoould > 0
    # dimensionless core radius
# 'n30': fraction of H+ or OH- [only vaild for CR=True]
# 'CR':
    # [only vaild for CR=True]
    # 0=total number of functional groups*ka2_SumI0
    # 1=n30/Ka1, 2=n30/Ka2
    # Ka1: (H2A+) -> (H+) + (HA)
    # Ka2: (HA) -> (H+) + (A-)
    # if {0: kaNf, 1: 0.0, 2: 0.0}: constant surface charge, = -kaNf
    # A: CR[0], B: CR[2], C: CR[1]*CR[2]
# 'w':
    # [only vaild for AC=True]
    # dimensionless frequency, w=1 means (1e-9/a^2) Hz,
    # should < (1e6/(1e-9/a^2)) = 1e3 for a=1e-6 meter
    # convertion between old expression is 1e-3*w = w_old
# 'ND': number of grid points
    # 'n': normal direction
    # 's': tangential direction
    # for 1D system:
        # only r-direction (n->r)
        # 'sU', 'sW', 'sD'
    # for plane system:
        # outside: n->eta, s->xi
        # inside: n->r, s->theta
        # 's'='sU'+'sW'+'SD'/
    # for cylinder system:
        # n->r, s->theta
        # ND['sW'] needs to be odd s.t. Z = 0 points will exist
        # 'U': thetaW~0, 'W': pi-thetaW~thetaW, 'D': pi-thetaW~pi
        # 'U' for up, 'W' for wall, 'D' for down
# 'H':
    # [only vaild for 1D system]
    # the volume density of particles i.e. ro = H^(-1/3)
# 'h':
    # [only vaild for plane system]
    # dimensionless distance from particle center to the plane, =cosh(eta0)
# 'NR':
    # [only vaild for cylinder system]
    # number of grid points in R-direction
# 'ro0':
    # [only vaild for cylinder system]
    # 'U': dimensionless length of the cylinder open-end side
    # 'W': dimensionless distance of cylinder wall to the axis (Rw)
    # 'D': dimensionless length of the cylinder open/dead-end side
# 'zetaW':
    # [only vaild for cylinder system]
    # dimensionless wall zeta-potential
# 'kaLc':
    # [only vaild for IL=True]
    # correction length of ionic liquid/Debye length
# 'nu':
    # [only vaild for IL=True]
    # correction factor of ion volume
# =============================================================================
# linkage of parameters
# =============================================================================
def IPsModify(IPs):
    def NnOmodify(IPs):
        IPs['ND']['nO'] = int(30+round(-np.log10(IPs['H']+1e-3)*35))
        IPs['ND']['O'] = IPs['ND']['nO']
        print('  ND: ', IPs['ND'])
    def NDmodify():
        IPs['ND'].update({'nI': 20*int(IPs['zeta'])+int(IPs['ka'])})
        IPs['ND'].update({'I': IPs['ND']['nI']})
        print('  ND: ', IPs['ND'])
    def CRmodify():
        if IPs['ka']==0.1: IPs['CR'][1] = 7.964/IPs['CR'][2]
        elif IPs['ka']==1.0: IPs['CR'][1] = 10.0/IPs['CR'][2]
        elif IPs['ka']==10.0: IPs['CR'][1] = 32.21/IPs['CR'][2]
        print('  CR: ', IPs['CR'])
    def kaLcModify():
        IPs['kaLc'] = 0.00275*IPs['ka']
    def ro0modify():
        factor = 1.0+4.0/(IPs['ka']+1.0)
        for ud in 'UD': IPs['ro0'][ud] = IPs['ro0']['W']*factor
        print('  ro0: ', IPs['ro0'])
        # IPs['ND']['nO'] = int(40*IPs['ro0']['W'])
        # IPs['ND']['O'] = IPs['ND']['nO']*IPs['ND']['s']
        # print('  ND: ', IPs['ND'])
    # ro0modify()
    # CRmodify()
    pass
def roSet(IPs, ctrl):
    if ctrl['Sys']['major']=='a':
        if ctrl['Sys']['OB']['Cell']: IPs['ro'] = IPs['H']**(-1.0/3.0)
        else: IPs['ro'] = 10.0+20.0/(IPs['ka']+0.1)
        print('  ro: ', IPs['ro'])
ctrlL['IPs(x)'] = IPsModify
# ctrlL['ro(ka)'] = roSet
# =============================================================================
# numerical conditions & methods choose
# =============================================================================
ctrl['N'] = {'tol': 1e-12, 'Niter': 20, 'large': 1000}
# 'tol': tolerance i.e. x can be seen as zero once abs(x)<tolerance
# 'Niter': iteration times
ctrl['Do'] = {\
              'e': {'old->': False, '->NL': True}, \
              'dIter': False, 'preconditioner': True, \
              'a': {'psiEq3': True, 'expGrid': True, 'analytical': False} \
              }
# 'e':
    # 'old->':
        # True=use phie calculated in previous loop as initial guess
        # False=use linear approximation as initial guess
    # '->NL':
        # [only vaild for 'old->'=False]
        # True=Iteration solution, False=linear approximation in eSolver
# 'dIter': True=Iteration method, False=Matrux method in dSolver
# 'preconditioner': True=use preconditioner, False=not use
# 'a':
    # [only vaild for 1D system]
    # 'psiEq3':
        # [only vaild for 1D DC 1 region Newtonian system]
        # True=Reduction of psi Eq order (4 -> 3), False=Normal order (4)
    # 'expGrid':
        # default: False
        # True=grid is modified by exp function, False=grid is set as xOC
# =============================================================================
# structure control
# =============================================================================
ctrlL['Seq'] = ('ND', 'NR', 'rc', 'Pec', 'H', 'n30', \
                'kaLc', 'rhoFix', 'CR', 'h', 'zetaW', \
                'aldam', 'zeta', 'nu', 'w', 'vis', 'ka', 'aldap', 'ro0')
ctrlSkip = 0
# 5: all skip
# 4: until OC
# 3: until EOF
# 2: until equilibrium
# 1: until disturbance
# 0: until mu (disturbance variables are still in subproblem forms)
# -1: no skip (disturbance variables of plane are converted into real forms)
# -2: no skip (disturbance variables are combine into physical forms)
# =============================================================================
# figures
# =============================================================================
ctrlFig = {0: {'DIY': True, 'mu':  False}, \
           1: {'DIY': False, 'EOF': False, \
               'phie': False, 'debug': False, 'real': False}, \
           2: {'DIY': False, 'mesh': False, \
               'phie': False, 'debug': False, 'real': False}}
# '0D': one loop = one point (0D)
# '1D': one loop = one line (1D)
# '2D': one loop = one figure (2D)
# =============================================================================
# format of figure
# =============================================================================
# file['ZoneName'] = tuple() # name of parameters shown in zone (in tuple form)
# file['ZoneValues'] = tuple() # value of parameters shown in zone (in tuple form)
# file['VarsName'] = tuple() # name of variables (in tuple form)
# file['VarsValues'] = np.array([[]]) # value of variables (in array form)
    # e.g. a, b, c are 3x1 array
    # if want to write
        # a[0, 0] b[0, 0] c[0, 0]
        # a[1, 0] b[1, 0] c[1, 0]
        # a[2, 0] b[2, 0] c[2, 0]
    # then the format should be
    # file['VarsValues'] = np.concatenate((a, b, c), axis=1)
# writeFile(file) # write data
# =============================================================================
# some nomenclature
# =============================================================================
# OPs['n'] or OPs['s'] -> normal and tangential location variables i.e. qn and qs
    # for spherical coordinate, (n, s) means (r, theta)
    # for bispherical coordinate, (n, s) means (eta, xi)
# OPs['phie'], OPs['phid'], OPs['gj'], OPs['psi'] -> variables
    # may be physical value or subproblem values
    # physical value: N*1, subproblem value: N*2
# OPs['nje'] and OPs['njd'] -> equilibrium and disturbance concentration
# OPs['FZ'] -> Z-direction force (1*2, subproblem values)
# OPs['mu'] -> mobility
# OPs['At'] -> location index
    # 's': particle surface (and core surface) i.e. r=1+ or rc
    # 'ro': outer virtual surface i.e. r=ro (for a system)
    # 'p': plane surface i.e. Z=0 (for b system)
    # 'w': cylinder wall i.e. R=Rw (for c system)
    # 'u' / 'd': up/down cylinder end i.e. Z=L / -L (for c system)
    # 'qWA' & 'qwB': two sides of corner lines (i.e. patch lines) of cylinder i.e. theta=thetaW and pi-thetaW (for c system)
    # 'Z0': Z = 0 (i.e. theta=pi/2) (for c system)
    # 'sI': particle inner surface i.e. r=1-(for 2 region system)
# OPs['PD'] -> differential matrix
    # 0: for value i.e. f(x)
    # 10, 20, 30, 40: for n-direction derivative i.e. df/dqn
    # 1, 2, 3, 4: for s-direction derivative i.e. df/dqs
# 'O' or 'I' -> outer region or inner region
# e.g. equilibrium surface charge at particle surface = [-dphie/dr](r=1+)
    # sigma = -np.matmul(OPs['PD']['O'][10][OPs['At']['O']['s']], OPs['phie']['O'])
# =============================================================================
# 0D_DIY figure: one loop = one point
# =============================================================================
# analytical
def Dim0_DIY(file, IPs, OPs, ctrl):
    from gAnalytical import OhshimaTmYDL_LowZeta, HuckelBoothTmY, YarivBubble, Stone, Booth, LowZetaCurrentDensityInt, StoutKhairTmY_Cell
    from gFigure import integralJalongZ0_1D
    file['ZoneName'] = ('`z^*', '`ka', '`la' ) # name of parameters shown in zone (in tuple form)
    file['ZoneValues'] = (IPs['zeta'], IPs['ka'], IPs['aldap'] ) # value of parameters shown in zone (in tuple form)
    # muAnalytical = HuckelBoothTmY()
    # muAnalytical = YarivBubble()
    muAnalytical = OhshimaTmYDL_LowZeta()
    # muAnalytical = StoutKhairTmY_Cell()
    # muAnalytical = Stone(float(OPs['phid']['O'][OPs['At']['O']['s']]))
    # muAnalytical = Booth()
    file['VarsName'] = ('R_w^*', '`m^* ') # name of variables (in tuple form)
    # JZ = integralJalongZ0_1D(IPs=IPs, OPs=OPs, relative=False)
    # JZanalytical = LowZetaCurrentDensityInt(IPs=IPs, U=OPs['mu'])
    file['VarsValues'] = np.array([[IPs['ro0']['W'], OPs['mu']]]) # value of variables (in array form)
    writeFile(file) # write data

## differential
# def Dim0_DIY(file, IPs, OPs, ctrl):
#     from gAnalytical import OhshimaTmYDL_LowZeta
#     file['ZoneName'] = ('`z^*', '`h_f_r', ) # name of parameters shown in zone (in tuple form)
#     file['ZoneValues'] = (IPs['zeta'], IPs['vis']) # value of parameters shown in zone (in tuple form)
#     file['VarsName'] = ('`ka', '`m^*', '`m^*/`z^*', '"`m^* analytical"', '`t^N^*_r_`q', '`t^M^*_r_`q', '"`t^N^*_r_`q+`t^M^*_r_`q"', \
#                         'd^2`Y^*', '`d`F^*', 'd`f_e^*/dr^*~4`d`F^*', 'v_`q^*') # name of variables (in tuple form)
#     DphieS = float(np.matmul(OPs['PD']['O'][10][OPs['At']['O']['s']], OPs['phie']['O']))
#     D2psiS = float(np.matmul(OPs['PD']['O'][20][OPs['At']['O']['s']], OPs['psi']['O']))
#     phidS = float(np.matmul(OPs['PD']['O'][0][OPs['At']['O']['s']], OPs['phid']['O']))
#     DpsiS = float(np.matmul(OPs['PD']['O'][10][OPs['At']['O']['s']], OPs['psi']['O']))
#     tauN = D2psiS-(3.0*IPs['vis']+2.0)*DpsiS
#     tauM = -DphieS*phidS
#     muAnalytical = OhshimaTmYDL_LowZeta()
#     file['VarsValues'] = np.array([[IPs['ka'], OPs['mu'], OPs['mu']/IPs['zeta'], muAnalytical, \
#                                     tauN, tauM, tauN+tauM, D2psiS, phidS, -tauM, DpsiS]]) # value of variables (in array form)
#     writeFile(file) # write data

## HermansFujita
# def Dim0_DIY(file, IPs, OPs, ctrl):
#     from gAnalytical import HermansFujita
#     file['ZoneName'] = ('`la_p', '`r^*_f_i_x') # name of parameters shown in zone (in tuple form)
#     file['ZoneValues'] = (IPs['aldap'], IPs['rhoFix']) # value of parameters shown in zone (in tuple form)
#     file['VarsName'] = ('`ka', '`m^*', '`m^*/`m^*_H_F') # name of variables (in tuple form)
#     muHF = HermansFujita()
#     file['VarsValues'] = np.array([[IPs['ka'], OPs['mu'], OPs['mu']/muHF]]) # value of variables (in array form)
#     writeFile(file) # write data
# =============================================================================
# 1D_DIY figure: one loop = one line
# =============================================================================
# def Dim1_DIY(file, IPs, OPs, ctrl):
#     file['ZoneName'] = ('`h_f_r', ) # name of parameters shown in zone (in tuple form)
#     file['ZoneValues'] = (IPs['vis'], ) # value of parameters shown in zone (in tuple form)
#     site = OPs['At']['O']['s']
#     file['VarsName'] = ('R^*', '`y^*_1', '`y^*_2') # name of variables (in tuple form)
#     file['VarsValues'] = np.concatenate((OPs['n']['O'], OPs['psi']['O']), axis=1) # value of variables (in array form)
#     writeFile(file) # write data
from gOCmethod import Z0index, IntMxySet, DxyDvarSet
def Dim1_DIY(file, IPs, OPs, ctrl):
    for OI in 'O':
        file['ZoneName'] = ('OI', ) # name of parameters shown in zone (in tuple form)
        file['ZoneValues'] = (OI, ) # value of parameters shown in zone (in tuple form)
        file['VarsName'] = ('R^*', '"grad(g_1^*)"', '"grad(g_2^*)"', 'f_1_Z^*', 'f_2_Z^*', 'J_Z^*', 'J_Z^*R^*') # name of variables (in tuple form)
        IPsOPsCtrlOI = {'IPs': IPs, 'OPs': OPs, 'ctrl': ctrl, 'OI': OI}
        RZ = meshRZ(**IPsOPsCtrlOI)
        fjRZ = fjRZset(**IPsOPsCtrlOI)
        JRZ = CurrentDensitySet(fjRZ)
        iZ0 = Z0index(NDW=0, NW=IPs['ND']['s'], Nx=IPs['ND']['nO'])
        R = np.expand_dims(RZ[iZ0][:, 0], axis=1)
        JZ = np.expand_dims(JRZ['Z'][iZ0][:, 0], axis=1)

        DxDr = DxyDvarSet(a=OPs['n']['O'][-1], b=OPs['n']['O'][0])
        Int = IntMxySet(IPs['ND']['n'+OI])/DxDr


        Dgj = {j: np.matmul(OPs['PD'][OI][10], OPs['gj'][OI][j]) for j in (1, 2)}
        print(np.matmul(Int, fjRZ[1]['Z'][iZ0]*R))
        print(np.matmul(Int, fjRZ[2]['Z'][iZ0]*R))
        print(np.matmul(Int, JZ*R))
        file['VarsValues'] = np.concatenate((R, Dgj[1], Dgj[2], fjRZ[1]['Z'][iZ0], fjRZ[2]['Z'][iZ0], JZ, JZ*R), axis=1) # value of variables (in array form)
        writeFile(file) # write data
# =============================================================================
# 2D_DIY figure: one loop = one figure
# =============================================================================
from gFigure import meshRZ, fjRZset, CurrentDensitySet, Dim1to2, CurrentStreamLine1D
def Dim2_DIY(file, IPs, OPs, ctrl):
    for OI in 'O':
        file['ZoneName'] = ('OI', ) # name of parameters shown in zone (in tuple form)
        file['ZoneValues'] = (OI, IPs['ND']['n'+OI], IPs['ND']['s']) # value of parameters shown in zone (in tuple form)
        file['VarsName'] = ('R^*', 'Z^*', 'f_1_R^*', 'f_1_Z^*', 'f_2_R^*', 'f_2_Z^*', \
                            'J_R^*', 'J_Z^*', '`d`f^*', '`y_J^*') # name of variables (in tuple form)
        IPsOPsCtrlOI = {'IPs': IPs, 'OPs': OPs, 'ctrl': ctrl, 'OI': OI}
        RZ = meshRZ(**IPsOPsCtrlOI)
        fjRZ = fjRZset(**IPsOPsCtrlOI)
        JRZ = CurrentDensitySet(fjRZ)
        psiJ = CurrentStreamLine1D(**IPsOPsCtrlOI)
        phid = Dim1to2(fr=OPs['phid'][OI], fq=np.cos(OPs['s'][OI]))
        temp = np.concatenate(tuple(fjRZ[j][RZ] for j in (1, 2) for RZ in 'RZ'), axis=1)
        file['VarsValues'] = np.concatenate((RZ, temp, JRZ['R'], JRZ['Z'], phid, psiJ), axis=1) # value of variables (in array form)
        writeFile(file) # write data
DIYs = {'0D_DIY': Dim0_DIY, '1D_DIY': Dim1_DIY, '2D_DIY': Dim2_DIY}
Files = createFile(ctrlFig=ctrlFig, DIYs=DIYs)
ctrlL['Skip'] = SkipCheck(ctrlSkip=ctrlSkip, Files=Files, FigFirst=False)
# =============================================================================
# main part
# =============================================================================
ctrlMultiSys = False
ctrlSysList = (True, False)
if not ctrlMultiSys: ctrlSysList = ('True', )
startTime = time()
for SysDIY in ctrlSysList:
    # setting part
    if ctrlMultiSys: ctrl['Sys']['m']['IL'] = SysDIY
    # calculation
    resultIPs, resultOPs, resultCtrl = \
        MainProgram(ctrl=deepcopy(ctrl), ctrlData=deepcopy(ctrlData), \
                    ctrlL=deepcopy(ctrlL), Files=Files)
    # packing in folder
    # folderName = str(SysDIY)
    # if ctrlMultiSys: packingFile(packageName=folderName, startTime=startTime)
Beep(10000,500)
if ctrlMultiSys: print('\033[42mtotal '+TimeMessageSet(startTime)+'\033[0m')
PrintBlock(' Program  End ')

