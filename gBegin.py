import numpy as np
from time import time, strftime, localtime
from itertools import product as itertools_product
from sys import exit as sys_exit
# =============================================================================
# start and end blocks
# =============================================================================
windowLength = 80
symbol = '#'
line = symbol*windowLength
def PrintBlock(Text):
    TextLen = len(Text)
    LeftLen = (windowLength-TextLen)//2
    RightLen = windowLength-LeftLen-TextLen
    print(line+'\n'+symbol*LeftLen+Text+symbol*RightLen+'\n'+line)
# =============================================================================
# system and data set simplification
# =============================================================================
def OverWrite(ctrl, ctrlData):
    abcSystems(ctrl['Sys'])
    BallKinds(ctrl['Sys'])
    RegionNumbers(ctrl['Sys'])
    BC_OverWrite(ctrl)
    Do_OverWrite(ctrl)
    Data_OverWrite(ctrl, ctrlData)
def ZeroOut(Data, keys, O):
    for key in keys: Data[key] = (O, )
def abcSystems(Sys):
    def aSysSet():
        Sys['major'] = 'a'
        del Sys['OB']['A-W'], Sys['OB']['WallCharged']
    def bSysSet():
        Sys['major'] = 'b'
        Sys['m']['IL'] = False
        del Sys['OB']['Cell'], Sys['OB']['WallCharged']
    def cSysSet():
        Sys['major'] = 'c'
        del Sys['OB']['Cell'], Sys['OB']['A-W']
    if Sys['major']['2D']:
        if Sys['major']['Bispherical']: bSysSet() #plane
        else: cSysSet() #cylinder
    else: aSysSet() #1D
def BallKinds(Sys):
    if Sys['p']['DL']:
        if Sys['p']['Porous']:
            if Sys['p']['Core'] and Sys['major']=='a': Sys['p'] = 'M'
            else: Sys['p'] = 'G'
        else:
            Sys['p'] = 'D'
    else:
        if Sys['p']['Porous']:
            if Sys['p']['Core']: Sys['p'] = 'S'
            else: Sys['p'] = 'P'
        else:
            Sys['p'] = 'R'
def RegionNumbers(Sys):
    # one region, 4 vars: a+RDG
    Sys['OI'] = ['O', ]
    Sys['eVars'] = ['O', ]
    Sys['dVars'] = ['g1O', 'g2O', 'psiO', 'phidO']
    # if Sys['m']['CR']: Sys['dVars'].append('g3O') #CR
    # two region, 5 vars: bc+DG
    if Sys['p'] in 'DG' and Sys['major'] in 'bc':
        Sys['OI'].append('I')
        Sys['dVars'].append('psiI')
    # two region, 8 vars: abc+PSM
    elif Sys['p'] in 'PSM':
        Sys['OI'].append('I')
        Sys['eVars'].append('I')
        Sys['dVars'].extend(['g1I', 'g2I', 'psiI', 'phidI'])
        # if Sys['m']['CR'] and Sys['p']!='P': #CR pouous is too complex
        #     Sys['dVars'].append('g3I') #CR
def BC_OverWrite(ctrl):
    def gjSZ():
        if ctrl['Sys']['m']['Diffu']: ctrl['BC']['SZ']['gj'] = False #diffusiophoresis
        else: ctrl['BC']['SZ']['gj'] = True #electrophoresis
    def aBCfilter():
        if not ctrl['Sys']['OB']['Cell']: del ctrl['BC']['SZ']
        else: gjSZ()
        del ctrl['BC']['conductive']['OB']
    def bBCfilter():
        del ctrl['BC']['SZ']
        if ctrl['Sys']['OB']['A-W']: ctrl['BC']['conductive']['OB'] = False
        ctrl['BC']['Em>>Ep'] = False
        ctrl['BC']['infRef'] = True
        ctrl['BC']['L3=L2'] = False
    def cBCfilter():
        gjSZ()
        ctrl['BC']['Em>>Ep'] = False
        ctrl['BC']['L3=L2'] = False
    # abc
    if ctrl['Sys']['major']=='a': aBCfilter()
    elif ctrl['Sys']['major']=='b': bBCfilter()
    elif ctrl['Sys']['major']=='c': cBCfilter()
    # RDGPSM
    if not ctrl['Sys']['m']['IL']: del ctrl['BC']['L3=L2']
    if ctrl['Sys']['m']['CR']: del ctrl['BC']['zeta as sigma']
    if ctrl['Sys']['p'] in 'RDGP': del ctrl['BC']['SPB']
    if ctrl['Sys']['p']=='P':
        del ctrl['BC']['conductive']['s']
        del ctrl['BC']['zeta as sigma']
        del ctrl['BC']['Em>>Ep']
    if ctrl['Sys']['p']=='R': ctrl['BC']['conductive']['s'] = False #20200701
    if ctrl['Sys']['p'] not in 'GPSM': del ctrl['BC']['tauDBB'] #20200703
    if ctrl['Sys']['p'] not in 'DG': del ctrl['BC']['MWstress'] #20200706
def Do_OverWrite(ctrl):
    if ctrl['Sys']['major']=='a':
        TwoRegion = ctrl['Sys']['p'] in 'PSM'
        AC = ctrl['Sys']['m']['AC']
        if TwoRegion or AC: ctrl['Do']['a']['psiEq3'] = False
        if ctrl['Sys']['OB']['Cell'] or TwoRegion:
            ctrl['Do']['a']['expGrid'] = False
    else:
        del ctrl['Do']['a']
    if ctrl['Do']['e']['old->']: ctrl['Do']['e']['->NL'] = True
    if ctrl['Sys']['m']['AC']: ctrl['Do']['preconditioner'] = False
cOnly = ('NR', 'ro0', 'zetaW')
def Data_OverWrite(ctrl, ctrlData):
    def aIPsFilter():
        if not ctrl['Sys']['OB']['Cell']: ctrlData['H'] = (0.0, )
        ctrlData['h'] = (0.0, )
        ZeroOut(Data=ctrlData, keys=cOnly, O=None) #20200630
    def bIPsFilter():
        ctrlData['H'] = (None, )
        ZeroOut(Data=ctrlData, keys=cOnly, O=None) #20200630
    def cIPsFilter():
        ctrlData['H'], ctrlData['h'] = (None, ), (0.0, )
        if ctrl['Sys']['OB']['WallCharged']:
            if ctrl['Sys']['m']['Diffu']:
                ctrl['Sys']['OB']['WallCharged'] = False
        else:
            ctrlData['zetaW'], ctrlData['NR'] = (0.0, ), (None, )
        for ro0 in ctrlData['ro0']:
            if ro0['D']!=ro0['U']: ro0['D'] = ro0['U'].copy()
    def NDfilter():
        for ND in ctrlData['ND']:
            if ctrl['Sys']['major']=='c':
                ND['sD'] = ND['sU']
                if ND['sW']%2==0: ND['sW'] = ND['sW']+1
            ND['s'] = sum(ND['s'+i] for i in 'DWU')
            Ns = 1 if ctrl['Sys']['major']=='a' else ND['s']
            for OI in ctrl['Sys']['OI']: ND[OI] = ND['n'+OI]*Ns
    def rcFilter():
        def rcTrim(): ctrlData['rc'] = (ctrlData['rc'][0], )
        if ctrl['Sys']['p']=='R': ctrlData['rc'] = (1.0, )
        elif ctrl['Sys']['p'] in 'DG':
            if ctrl['Sys']['major']=='a': ctrlData['rc'] = (1.0, )
            elif ctrl['Sys']['major'] in 'bc': rcTrim()
        elif ctrl['Sys']['p']=='P': rcTrim()
    #------------------------------------------------------------------------#
    if ctrl['Sys']['major']=='a': aIPsFilter()
    elif ctrl['Sys']['major']=='b': bIPsFilter()
    elif ctrl['Sys']['major']=='c': cIPsFilter()
    # ND
    NDfilter()
    # ka Pec
    # zeta
    if ctrl['Sys']['p']=='P': ctrlData['zeta'] = (None, )
    # vis
    if ctrl['Sys']['p']=='R': ctrlData['vis'] = ('inf', )
    elif ctrl['Sys']['p'] in 'PS': ctrlData['vis'] = (1.0, )
    # aldam
    if not ctrl['Sys']['m']['Gel']: ctrlData['aldam'] = (0.0, )
    # aldap
    if ctrl['Sys']['p'] in 'RD': ctrlData['aldap'] = (None, )
    # rhofix
    if ctrl['Sys']['p'] in 'RDG': ctrlData['rhoFix'] = (None, )
    # rc
    rcFilter()
    # n30 CR
    if ctrl['Sys']['m']['CR']:
        ZeroOut(Data=ctrlData, keys=('zeta', ), O=None)
        # for Pec in ctrlData['Pec']: Pec[3] = 0.056
    else:
        ZeroOut(Data=ctrlData, keys=('CR', 'n30'), O=None)
    # w
    if not ctrl['Sys']['m']['AC']: ctrlData['w'] = (0.0, )
    # NR H h ro0 zetaW
    if not ctrl['Sys']['m']['IL']:
        ctrlData['kaLc'] = (0.0, )
        ctrlData['nu'] = (0.0, )
# =============================================================================
# convert ctrlData into IPs loop form
# =============================================================================
def DataExpansion(Data, Seq):
    if set(Data)-set(Seq):
        print('\n\033[41mctrlData and ctrlSeq dismatch!\033[0m')
    temp = (Data[key] for key in Seq[0:-1])
    return itertools_product(*temp), Data[Seq[-1]]
# =============================================================================
# basic information
# =============================================================================
def MessageSet(ctrl, IPs, Files, loopN):
    message = ['\033[42m'+SystemTranslation(ctrl)+'\033[0m']
    message.append('i.e.')
    message.append(dictText(x=ctrl['Sys'], title='ctrlSys:'))
    message.append(dictText(x=ctrl['BC'], title='ctrlBC:'))
    message.append('Parameters Changing: '+str(ctrl['Fig']['Change']))
    if True in {file['save'] for file in Files.values() if file['dim']==0}:
        message.append('x variable: '+str(ctrl['Fig']['xVar']))
    message.append('Output: '+ResultTranslation(Files))
    message.append(dictText(x=ctrl['Do'], title='ctrlDo:'))
    message.append(dictText(x=IPs, title='IPs (without changing):'))
    message.append('total number of loops: '+str(loopN))
    return '\n'.join(message)
def TimeMessageSet(startTime):
    TimeMessage = ['time cost={:5.1f} s'.format(time()-startTime)]
    StartEnd = (strftime("%Y %m.%d %H:%M:%S", localtime(i)) \
                for i in (startTime, time()))
    TimeMessage.append('(from {} to {})'.format(*StartEnd))
    return '\n'.join(TimeMessage)
#Translate parameters into sentence
particleName = {'R': 'Rigid Particle', 'D': 'Newtonian Droplet', \
                'G': 'DBB Droplet', 'P': 'Porous Particle', \
                'S': 'Soft Particle', 'M': 'Soft Particle with Slip Core'}
def SystemTranslation(ctrl):
    def ConductiveTest():
        if ctrl['BC']['conductive']['OB']: return 'Conductive'
        else: return 'Non-Conductive'
    Sys = []
    if ctrl['Sys']['major']=='a':
        if ctrl['Sys']['OB']['Cell']: Sys.append('Suspension of')
        else: Sys.append('Single')
    if ctrl['Sys']['m']['CR']:
        Sys.append('Charge Regularation')
    elif ctrl['Sys']['p'] in 'RDGSM':
        if ctrl['BC'].get('zeta as sigma'):
            Sys.append('Constant Surface charge')
        else:
            Sys.append('Constant Zeta-potential')
    if ctrl['Sys']['p'] in 'RDGSM':
        if ctrl['BC']['conductive']['s']: Sys.append('Conductive')
        else: Sys.append('Non-Conductive')
    Sys.append(particleName[ctrl['Sys']['p']])
    if ctrl['BC'].get('SPB'): Sys.append('(SPB)')
    if ctrl['Sys']['m']['Diffu']: Sys.append('Diffusio-')
    elif ctrl['Sys']['m']['AC']: Sys.append('AC Electro-')
    else: Sys.append('DC Electro-')
    if ctrl['BC']['infRef']: Sys.append('phoresis')
    else: Sys.append('osmosis')
    if ctrl['Sys']['m']['Gel']: Sys.append('in DBB Fluid (Gel)')
    else: Sys.append('in Newtonian Fluid')
    if ctrl['Sys']['m']['IL']: Sys.append('with Ionic Liquid as Electrolyte')
    else: Sys.append('with Point-charge Electrolyte')
    if ctrl['Sys']['major']=='b':
        Sys.append('moving away from')
        if ctrl['Sys']['OB']['A-W']: Sys.append('Air-Water Interface')
        else: Sys.append(ConductiveTest()+' Plane')
    elif ctrl['Sys']['major']=='c':
        Sys.append('moving in')
        if ctrl['Sys']['OB']['WallCharged']: Sys.append('a Charged')
        else: Sys.append('an Uncharged '+ConductiveTest())
        Sys.append('Open-End Cylinder')
    return ' '.join(Sys)
#output figure types
def ResultTranslation(Files):
    output = tuple(key for key, file in Files.items() if file['save'])
    if output: return ', '.join(output)
    else: return '\033[41mNone\033[0m'
#parameters will change
def DataTranslation(Data):
    return tuple(var for var, varData in Data.items() if len(varData)>1)
#warning about ctrl['BC']
def BC_warning(ctrl): #20200706
    Allkeys = ctrl['BC'].keys()
    if 'SZ' in Allkeys:
        if 'phid' in ctrl['BC']['SZ']:
            if not ctrl['BC']['SZ']['phid']:
                print('\033[41mLN BC, sure?\033[0m')
    if ctrl['BC'].get('zeta as sigma'):
        print('\033[41mzeta means surface charge, sure?\033[0m')
    if 'tauDBB' in Allkeys:
        if ctrl['BC']['tauDBB']:
            print('\033[41mBC with tauDBB, sure?\033[0m')
    if 'MWstress' in Allkeys:
        if not ctrl['BC']['MWstress']:
            print('\033[41mold and wrong BC, sure?\033[0m')
    if 'conductive' in Allkeys:
        if ctrl['BC']['conductive']:
            text = ("conductive", ctrl['BC']['conductive'])
            print('\033[41mNote: {}={}\033[0m'.format(*text))
# =============================================================================
# time estimate
# =============================================================================
def loopNset(ctrlData):
    return np.prod([len(DataValue) for DataValue in ctrlData.values()])
def EstimateTime(tCounter):
    end = time() #now
    TimeCost = end-tCounter['start'] #time passed
    progress = tCounter['now']/tCounter['loopN'] #number of loop passed
    #estimated time needed for all loop - time passed
    TimeRemain = TimeCost/progress-TimeCost #linear expolation estimation
    Fulllen = 10 #progress bar full length
    barlen = int(Fulllen*progress) #length of progress bar now
    text = '\033[44mtime remain (estimated)={:5.1f} s\033[0m'
    print(text.format(TimeRemain))
    text = '█'*barlen+' '*(Fulllen-barlen)+'▏'+'{:4.0f}/{:4.0f} completed'
    print(text.format(tCounter['now'],tCounter['loopN']))
# =============================================================================
# skip some loop stages
# =============================================================================
# what is used in each part, if change nothing, the calculation part will pass through
IPnames = {'OC': ('ND', 'rc', 'H', 'h', 'ro0', 'ro'), \
           'EOF': ('NR', 'ro0', 'ka', 'zetaW', 'w', 'aldam', 'kaLc', 'nu'), \
           'phie': ('ka', 'zeta', 'rhoFix', 'n30', 'CR', 'kaLc', 'nu')}
def ChangedCheck(IPs, IPsOld):
    #what is changed compared with previous loop
    Changed = {i: True in {IPs.get(j)!=IPsOld.get(j) for j in IPnames[i]} \
               for i in IPnames.keys()}
    Changed['EOF'] = Changed['OC'] or Changed['EOF']
    Changed['phie'] = Changed['EOF'] or Changed['phie']
    return Changed
subtype_dims = {'DIY': ('DIY', '012'), \
                -2: ('real', '12'), -1: ('debug', '12'), 0: ('mu', '0'),
                1: ('mu', '0'), 2: ('phie', '12'), \
                3: ('EOF', '1'), 4: ('mesh', '2')}
def TrueTest(Files, subtype, dims):
    return (True in {Files[i+'D_'+subtype]['save'] for i in dims})
def SkipCheck(ctrlSkip, Files, FigFirst):
    #prevent ctrlSkip -><- figure output
    #FigFirst: True=change ctrlSkip, False=change Files
    if FigFirst:
        if not TrueTest(Files, *subtype_dims['DIY']):
            for i in range(-2, 5):
                if TrueTest(Files, *subtype_dims[i]):
                    ctrlSkip = i
                    break
    else:
        for i in range(-2, ctrlSkip)[::-1]:
            for dim in subtype_dims[i][-1]:
                Files[dim+'D_'+subtype_dims[i][0]]['save'] = False
    return ctrlSkip
# =============================================================================
# modification of inputs
# =============================================================================
def nj0Set(IPs, CR):
    IPs['nj0'] = {1: 1.0}
    if CR: IPs['nj0'][3] = IPs['n30']
    temp = sum(IPs['zj'][j]*IPs['nj0'][j] for j in IPs['nj0'].keys())
    IPs['nj0'][2] = temp/abs(IPs['zj'][2])
    return IPs['nj0']
# prevent RAM overflow
def SizeCheck(ND, dVars, Nmax):
    # (matrix not work?, iteration not work?)
    if ND.get('I'): NOI = max(ND['O'], ND['I'])
    else: NOI = ND['O']
    Nt = sum(ND[var[-1]] for var in dVars)
    if NOI>Nmax:
        MatrixStop, ProgramStop = True, True
    elif Nt>Nmax:
        MatrixStop, ProgramStop = True, False
    else:
        MatrixStop, ProgramStop = False, False
    if ProgramStop:
        print('\033[41m Number of grids = {} > {}!\033[0m'.format(Nt, Nmax))
        sys_exit(1)
    return MatrixStop
# =============================================================================
# some function
# =============================================================================
def DEPsystem(ctrlSys):
    return ctrlSys['m']['AC'] and ctrlSys['major'] in 'ab'
def KeyDelete(DictKeys, delKeys):
    return set(DictKeys)-set(delKeys)
def ValueSelector(Dict, Keys, reverse=False):
    if reverse: selected = KeyDelete(DictKeys=Dict.keys(), delKeys=Keys)
    else: selected = Keys
    return {key: Dict[key] for key in selected}
def dictText(x, title):
    text = [title]
    for key, value in x.items(): text.append('  '+str(key)+': '+str(value))
    return '\n'.join(text)
MaxRavelAbs = lambda x: max(np.ravel(abs(x)))