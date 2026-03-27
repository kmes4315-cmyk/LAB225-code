# =============================================================================
# import modules
# =============================================================================
import numpy as np
from time import time
from copy import deepcopy
import gBegin
from gOCmethod import IndexSet, addFactors, gradSet
from gOCmethod_a import a_nsPDset
from gOCmethod_b import b_nsPDset
from gOCmethod_c import c_nsPDset
from gEOF import EOFsolver
from gEquilibrium import eSolver
from gDisturbance import dSolver, dModification, combination12
from gCalculator import njdSet
from gForce import FZset, muSet, KcmSet, muDEPset
from gFigure import LogFileName
# =============================================================================
# some constants
# =============================================================================
#-----dimensional constants-----#
epsilon0 = 8.8541878176e-12
epsilonM = 78.54*epsilon0 #epsilon m
epsilonP = 2*78.54*epsilon0 #epsilon p
kB = 8.314/6.02e23 #Boltzmann constant
Temperature = 298 #K
ElementCharge = 1.6e-19 #C
viscosityM = 8.9e-4 #etam, kg/m-s
densityM = 1e3 #rhofm, kg/m^3
densityP = 1.1e3 #rhofp, kg/m^3
ParticleRadius = 1e-6 #m
phi0 = kB*Temperature/ElementCharge #V
velocity0 = epsilonM*phi0**2/viscosityM/ParticleRadius #m/s
#-----dimensionless constants-----#
zj = {1: 1, 2: -1, 3: 1} # 1: cation, 2: anion 3: H+
Re = velocity0*ParticleRadius*densityM/viscosityM
densityP_M = densityP/densityM
epsilonP_M = epsilonP/epsilonM # epsilon p/epsilon m
# =============================================================================
# set by administrator
# =============================================================================
version = 1.2
# ctrlPackage['Create']: True=bulid pyc package, False=not build
ctrlPackage = {'Name': 'a_SlipCore_DC', 'Create': True}
# parameters allow to be changed by gInterface
__ctrlSysAllow = \
    {\
      'major': ('2D', 'Bispherical'), \
      'p': ('DL', 'Porous', 'Core', 'SPB'), \
      'm': ('Diffu', 'AC', 'Gel', 'IL', 'CR'), \
      'OB': ('Cell', 'A-W', 'WallCharged') \
      }
__ctrlDataAllow = ('ND', 'ka', 'Pec', 'zeta', 'vis', 'aldam', 'aldap', \
                    'rhoFix', 'rc', 'n30', 'CR', 'w', 'NR', 'H', \
                    'h', 'ro0', 'zetaW', 'kaLc', 'nu')
# default values of parameters
# (if it is not allowed to be changed, the value will overwrite the input one)
__ctrlSys = \
    {\
     'major': {'2D': False, 'Bispherical': False}, \
     'p': {'DL': True, 'Porous': True, 'Core': True}, \
     'm': {'Diffu': True, 'AC': False, 'Gel': False, \
           'IL': False, 'CR': False}, \
     'OB': {'Cell': False, 'A-W': False, 'WallCharged': False}, \
    }
__ctrlData = \
    {\
    'ND': [{'nO': 20, 'nI': 20, 'sU': 10, 'sW': 30, 'sD': 10}], \
    'ka': np.logspace(0, 0, 0+1).tolist(), \
    'Pec': [{1: 0.26, 2: 0.26}], \
    'zeta': np.linspace(1, 1, 1).tolist(), \
    'vis': np.logspace(np.log10(1.0), np.log10(1.0), 0+1).tolist(), \
    'aldam': [0.1], \
    'aldap': [3.0], \
    'rhoFix': [1.0], \
    'rc': [1e-12], \
    'n30': [1e-6], \
    'CR': [{0: 1.0, 1: 1e-6, 2: 0.0}], \
    'w': np.logspace(-3, -3, 0+1).tolist(), \
    'NR': [100], \
    'H': [0.1], \
    'h': [np.cosh(2.0)], \
    'ro0': [{'U': 6.0, 'W': 2.0, 'D': 6.0}], \
    'zetaW':  np.linspace(-3, 3, 3).tolist(), \
    'kaLc': [0.0], \
    'nu': [0.0], \
    }
# =============================================================================
# overwrite of
# =============================================================================
def ctrlSysLock(ctrl):
    for key1, value in __ctrlSys.items():
        if key1 not in ctrl['Sys'].keys(): ctrl['Sys'][key1] = {}
        for key2 in value.keys():
            if key2 not in __ctrlSysAllow[key1]:
                ctrl['Sys'][key1][key2] = __ctrlSys[key1][key2]
def ctrlDataLock(ctrlData):
    for key in __ctrlData.keys():
        if key not in __ctrlDataAllow:
            ctrlData[key] = __ctrlData[key]
# =============================================================================
# used in gPycPackage
# =============================================================================
def SysAllowChange():
    allowSys = {}
    for key1, value in __ctrlSys.items():
        if len(__ctrlSysAllow[key1])!=0:
            allowSys[key1] = {}
            for key2 in value:
                if key2 in __ctrlSysAllow[key1]:
                    allowSys[key1][key2] = "\"<class 'bool'>\""
                else:
                    allowSys[key1][key2] = __ctrlSys[key1][key2]
    return allowSys
def DataAllowChange():
    allowData = {}
    for key in __ctrlData:
        if key in __ctrlDataAllow:
            ValueType = type(__ctrlData[key][0])
            if ValueType==dict:
                allowData[key] = [{i: str(type(xi)) \
                                   for i, xi in __ctrlData[key][0].items()}]
            else:
                allowData[key] = [str(ValueType)]
    return allowData
# =============================================================================
# interface
# =============================================================================
def MainProgram(ctrl, ctrlData, ctrlL, Files):
    #-----pretreatment-----#
    def ctrlPreTreatment():
        ctrlSysLock(ctrl)
        ctrlDataLock(ctrlData)
        gBegin.OverWrite(ctrl=ctrl, ctrlData=ctrlData)
        ctrl['Fig'] = {'Change': gBegin.DataTranslation(ctrlData), \
                       'xVar': ctrlL['Seq'][-1]}
    def IPsSet():
        IPs = {'zj': zj.copy(), 'Re': Re, \
               'density': densityP_M, 'epsilon': epsilonP_M}
        if not ctrl['Sys']['m']['CR']: del IPs['zj'][3]
        temp = gBegin.ValueSelector(Dict=ctrlData, \
                                    Keys=ctrl['Fig']['Change'], reverse=True)
        IPs.update(temp)
        return IPs
    #-----parameter loops-----#
    def ParameterLoops():
        ctrlL['IPsOld'] = {} # used in ChangedCheck
        OPs = {}
        IPsss, xVars = gBegin.DataExpansion(Data=ctrlData, Seq=ctrlL['Seq']) # for loop
        for IPss in IPsss:
            IPs.update(zip(ctrlL['Seq'], IPss))
            ctrl['Fig']['FL'] = True
            for xVar in xVars:
                IPs[ctrlL['Seq'][-1]] = xVar
                IPsOPsCtrl = {'IPs': IPs, 'OPs': OPs, 'ctrl': ctrl}
                LoopBody(**IPsOPsCtrl, ctrlL=ctrlL, Files=Files)
                ctrlL['IPsOld'] = deepcopy(IPs)
                FiguresOutput(IPsOPsCtrl, Files=Files)
                if ctrl['Fig']['FL']: ctrl['Fig']['FL'] = False
                Timer['now']+=1
                gBegin.EstimateTime(Timer)
        return OPs
    # pretreatment
    ctrlPreTreatment()
    Timer = {'now': 0, 'start': time(), 'loopN': gBegin.loopNset(ctrlData)}
    #start
    IPs = IPsSet()
    message = gBegin.MessageSet(ctrl=ctrl, IPs=IPs, Files=Files, \
                                loopN=Timer['loopN'])
    print(message)
    with open(LogFileName,'w') as LogFile: LogFile.write(message+'\n')
    # parameter loops
    OPs = ParameterLoops()
    # end
    TimeMessage = gBegin.TimeMessageSet(Timer['start'])
    print(gBegin.line)
    print('\033[44m'+TimeMessage+'\033[0m')
    with open(LogFileName,'a') as LogFile: LogFile.write(TimeMessage+'\n')
    return IPs, OPs, ctrl
# =============================================================================
# loop body
# =============================================================================
def LoopBody(IPs, OPs, ctrl, ctrlL, Files):
    print(gBegin.line)
    # print IPs information
    IPsPrintStep(IPs=IPs, ctrl=ctrl)
    # IPsModification
    if ctrl['Sys']['major']=='a':
        if ctrlL.get('ro(ka)') and not ctrl['Sys']['OB']['Cell']:
            ctrlL['ro(ka)'](IPs=IPs, ctrl=ctrl)
        else:
            roSet(IPs=IPs, ctrl=ctrl)
    ctrlL['IPs(x)'](IPs)
    # package of IPs, OPs, ctrl
    IPsOPsCtrl = {'IPs': IPs, 'OPs': OPs, 'ctrl': ctrl}
    # write IPs, OPs, ctrl into different module
    IPsOPsCtrlWrite(**IPsOPsCtrl)
    # warning
    IPsWarningStep(IPs=IPs, ctrl=ctrl)
    if ctrlL['Skip']>=5: return
    Changed = gBegin.ChangedCheck(IPs=IPs, IPsOld=ctrlL['IPsOld'])
    # numerical grid
    if Changed['OC']: OCmethodStep(**IPsOPsCtrl)
    if ctrlL['Skip']>=4: return
    # electro osmotic flow
    if ctrl['Sys']['major']=='c' and Changed['EOF']: EOFstep(**IPsOPsCtrl)
    if ctrlL['Skip']>=3: return
    # equilibrium
    if Changed['phie']: EquilibriumStep(OPs)
    if ctrlL['Skip']>=2: return
    # disturbance
    DisturbanceStep(OPs)
    if ctrlL['Skip']>=1: return
    # force
    ForceStep(OPs=OPs, ctrl=ctrl)
    #modification of variables
    if ctrl['Sys']['major']=='b': dModification()
    if ctrlL['Skip']>=0: return
    if gBegin.TrueTest(Files=Files, subtype='debug', dims='12'):
        debugFigureStep(IPsOPsCtrl=IPsOPsCtrl, Files=Files)
    if ctrlL['Skip']>=-1: return
    combination12()
#-----ctrlSkip = 5-----#
def IPsPrintStep(IPs, ctrl):
    ChangedIPs = gBegin.ValueSelector(Dict=IPs, Keys=ctrl['Fig']['Change'])
    print(gBegin.dictText(x=ChangedIPs, title='IPs (changing)'))
    gBegin.nj0Set(IPs=IPs, CR=ctrl['Sys']['m']['CR'])
    print('  nj0: ', IPs['nj0'])
def IPsWarningStep(IPs, ctrl):
    gBegin.BC_warning(ctrl)
    if ctrl['Sys']['major']=='a' and IPs['ND']['nO']<50:
        print('\033[41mThe number of grid may be too small\033[0m')
    if ctrl['Sys']['major'] in 'bc':
        if ctrl['Sys']['p'] in 'DGP' and IPs['rc']>0.1:
            print('\033[41m rc = %.2f, sure?\033[0m'%IPs['rc'])
    if gBegin.SizeCheck(ND=IPs['ND'], dVars=ctrl['Sys']['dVars'], Nmax=20000):
        ctrl['Do']['dIter'] = True
        print('\033[41mIteration of disturbance ON!\033[0m')
def roSet(IPs, ctrl):
    if ctrl['Sys']['major']=='a':
        if ctrl['Sys']['OB']['Cell']: IPs['ro'] = IPs['H']**(-1.0/3.0)
        else: IPs['ro'] = 3.0+20.0/(IPs['ka']+0.1)
        print('  ro: ', IPs['ro'])
#-----ctrlSkip = 4-----#
nsPDset = {'a': a_nsPDset, 'b': b_nsPDset, 'c': c_nsPDset}
def OCmethodStep(IPs, OPs, ctrl):
    print('\033[44mOrthogonal Collocation Method...\033[0m')
    abcSys = ctrl['Sys']['major']
    OPs['n'], OPs['s'], OPs['PD'] = nsPDset[abcSys](IPs=IPs, ctrl=ctrl)
    #indexes
    OPs['At'], OPs['At_1'] = IndexSet(ND=IPs['ND'], ctrlSys=ctrl['Sys'])
    #scale factors
    majorSys=ctrl['Sys']['major']
    OPs['h'], OPs['R'], OPs['Z'], OPs['gradZ'] = \
        addFactors(n=OPs['n'], s=OPs['s'], majorSys=majorSys, IPs=IPs)
    #other operators
    OPs['grad'] = gradSet(PD=OPs['PD'], h=OPs['h'], majorSys=majorSys)
#-----ctrlSkip = 3-----#
def EOFstep(IPs, OPs, ctrl):
    OPs['Rend'] = {ud: OPs['R']['O'][OPs['At']['O'][ud]] for ud in 'ud'}
    if ctrl['Sys']['OB']['WallCharged']:
        print('\033[44mSolving Electro-osmotic flow...\033[0m')
        OPs['phieoo'], OPs['vZoo'], OPs['psioo'] = \
            EOFsolver(IPs=IPs, OPs=OPs, ctrl=ctrl)
    else:
        OO = {UD: np.zeros(RUD.shape) for UD, RUD in OPs['Rend'].items()}
        for i in ('phieoo', 'vZoo', 'psioo'): OPs[i] = OO
#-----ctrlSkip = 2-----#
def EquilibriumStep(OPs):
    print('\033[44mSolving Equilibrium Electric Potential...\033[0m')
    OPs['phie'], OPs['nje'], OPs['grad(phie)'] = eSolver()
#-----ctrlSkip = 1-----#
def DisturbanceStep(OPs):
    print('\033[44mSolving Disturbance Variables...\033[0m')
    OPs['gj'], OPs['psi'], OPs['phid'] = dSolver()
    OPs['njd'] = njdSet(phid=OPs['phid'], gj=OPs['gj'])
#-----ctrlSkip = 0-----#
def ForceStep(OPs, ctrl):
    print('\033[44mSolving Mobility...\033[0m')
    OPs['FZ'] = FZset()
    OPs['mu'] = muSet()
    print('\033[42m  mu = {}\033[0m'.format(OPs['mu']))
    if gBegin.DEPsystem(ctrl['Sys']):
        OPs['Kcm'] = KcmSet()
        print('\033[42m  Kcm = {}\033[0m'.format(OPs['Kcm']))
        OPs['muDEP'] = muDEPset()
        print('\033[42m  muDEP = {}\033[0m'.format(OPs['muDEP']))
#-----ctrlSkip = -1-----#
def debugFigureStep(IPsOPsCtrl, Files):
    print('\033[41mDebug File Writing...\033[0m')
    for i in '12':
        Files[i+'D_debug']['plot'](file=Files[i+'D_debug'], **IPsOPsCtrl)
# =============================================================================
# Figure output: can use figure module to replace the original one
# =============================================================================
def FiguresOutput(IPsOPsCtrl, Files):
    temp = {file['save'] and key[3:]!='debug' for key, file in Files.items()}
    if True in temp: print('\033[44mFile Writing...\033[0m')
    for key, file in Files.items():
        if file['save']:
            if file['dim']==0: file['FL'] = IPsOPsCtrl['ctrl']['Fig']['FL']
            if key[3:]!='debug': file['plot'](file=file, **IPsOPsCtrl)
# =============================================================================
# some function
# =============================================================================
def IPsOPsCtrlWrite(IPs, OPs, ctrl):
    import gOCmethod, gEquilibrium, gDisturbance, gBCs, gCalculator, gForce
    import gAnalytical
    gOCmethod.tol, gOCmethod.large = ctrl['N']['tol'], ctrl['N']['large']
    gAnalytical.tol = ctrl['N']['tol']
    gAnalytical.IPs, gAnalytical.ctrl = IPs, ctrl
    for x in (gEquilibrium, gDisturbance, gBCs, gCalculator, gForce):
        x.IPs, x.OPs, x.ctrl = IPs, OPs, ctrl