import numpy as np
from functools import partial
from os import getcwd, listdir, mkdir
from os.path import getsize, getmtime
from time import strftime, localtime
from shutil import copyfile
from gBegin import ValueSelector, DEPsystem
from gOCmethod import ns2RZ, AxisIndex, IntMxySet, DxyDvarSet
from gCalculator import rhoSet, UpSet, AWreverse, Sum_nj_Set, ka2_SumI0, njeSet
from gAnalytical import DL_psi_vRZ_Inside, LowZetaMu, HighKaMu, phid_Inside
ZoneKeys = ('H', '`L^*', 'ND', 'N_R', 'Pe', '`la_m', '`la', 'h^*', '`ka', \
            '`d_c', 'n_H_0^*', '`n', 'r_c^*', '`r_f_i_x^*', \
            'R_w', '`s_H', '`w^*', '`f_r', '`z_w^*', 'W')
IPsKeys = ('H', 'CR', 'ND', 'NR', 'Pec', 'aldam', 'aldap', 'h', 'ka', \
           'kaLc', 'n30', 'nu', 'rc', 'rhoFix', \
           'ro0', 'vis', 'w', 'zeta', 'zetaW', 'Rw')
key2name = dict(zip(IPsKeys, ZoneKeys))
hCombine = partial(np.concatenate, axis=1)
# =============================================================================
# mu Figure (0D): one loop = one point
# =============================================================================
def Phase(x): return np.angle(x)/np.pi*180.0
ComplexNames = ('Re({})', 'Im({})', '"{} `q_p(degree)"')
ComplexF = (np.real, np.imag, Phase)
AC_OPs = {'mu': '`m^*', 'Kcm': 'K_C_M'}
def Dim0_mu(file, IPs, OPs, ctrl):
    def ACpart(VarsName, VarsValues):
        keys = ['mu']
        if DEPsystem(ctrl['Sys']):
            keys.append('Kcm')
            VarsName.append('`m^*_D_E_P')
            VarsValues.append(OPs['muDEP'])
        for key in keys:
            VarsName.extend(name.format(AC_OPs[key]) for name in ComplexNames)
            VarsValues.extend(f(OPs[key]) for f in ComplexF)
    def VarsSet():
        VarsName = [key2name[ctrl['Fig']['xVar']], '`m^*']
        if np.iscomplex(OPs['mu']): mu = abs(OPs['mu'])
        else: mu = np.real(OPs['mu'])
        VarsValues = [IPs[ctrl['Fig']['xVar']], mu]
        if IPs['zeta']:
            VarsName.append('`m^*/`z^*')
            VarsValues.append(mu/IPs['zeta'])
        if IPs['rhoFix']:
            VarsName.append('`m^*/(`r_f_i_x^*/`la_p^2)')
            VarsValues.append(mu/IPs['rhoFix']*IPs['aldap']**2)
        if ctrl['Sys']['major']=='a' and not ctrl['Sys']['m']['AC']:
            if ctrl['Do']['a']['analytical']:
                VarsName.extend(('`m^*(LowCharged)', '`m^*(high`ka)'))
                muHighka = HighKaMu(r=OPs['n']['O'], nje=OPs['nje']['O'])
                VarsValues.extend((LowZetaMu(), muHighka))
        if ctrl['Sys']['m']['AC']:
            ACpart(VarsName=VarsName, VarsValues=VarsValues)
        return VarsName, [VarsValues]
    IPsChange = ValueSelector(Dict=IPs, Keys=ctrl['Fig']['Change'])
    if ctrl['Fig']['xVar'] in IPsChange.keys():
        del IPsChange[ctrl['Fig']['xVar']]
    file['ZoneName'] = tuple(key2name[i] for i in IPsChange.keys())
    file['ZoneValues'] = tuple(IPsChange.values())
    file['VarsName'], file['VarsValues'] = VarsSet()
    writeFile(file)
# =============================================================================
# r Figure (1D): one loop = one line
# =============================================================================
def Dim1_EOF(file, IPs, OPs, ctrl):
    IPsChange = ValueSelector(Dict=IPs, Keys=ctrl['Fig']['Change'])
    file['ZoneName'] = tuple(key2name[i] for i in IPsChange.keys())
    file['ZoneValues'] = tuple(IPsChange.values())
    file['VarsName'] = ('R^*', '`f_e_~%^*', '`r_e_~%^*' , \
                        'v_Z_~%^*', '`y_~%^*')
    rhoeoo = rhoSet(njeSet(OPs['phieoo']['u']))
    temp1 = tuple(OPs[key]['u'] for key in ('Rend', 'phieoo'))
    temp2 = tuple(OPs[key]['u'] for key in ('vZoo', 'psioo'))
    file['VarsValues'] = hCombine((*temp1, rhoeoo, *temp2))
    writeFile(file)
# =============================================================================
# Contour Figure (2D): one loop = one figure
# =============================================================================
RZtext = ('R^*', 'Z^*')
def meshRZ(IPs, OPs, ctrl, OI):
    if ctrl['Sys']['major']=='a':
        n = np.tile(OPs['n'][OI], (IPs['ND']['s'], 1))
        s = np.repeat(OPs['s'][OI], IPs['ND']['n'+OI], axis=0)
        return hCombine(ns2RZ(n=n, s=s, bis=False, h=0.0))
    elif ctrl['Sys']['major'] in 'bc':
        sign = AWreverse(ctrl['Sys']['OB'].get('A-W'))
        return hCombine((OPs['R'][OI], sign*OPs['Z'][OI]))
def Dim2_mesh(file, IPs, OPs, ctrl):
    def AtDebug(ND, OI, AtName, At):
        for site in At[OI].keys():
            IJ = (len(At[OI][site]), 1)
            file['ZoneValues'] = (AtName+' '+OI+' '+site, ND['n'+OI], \
                                  ND['s'], *IJ)
            file['VarsValues'] = RZ[At[OI][site]]
            writeFile(file)
    def OIzone(OI):
        IJ = (IPs['ND']['n'+OI], IPs['ND']['s'])
        file['ZoneValues'] = (OI, IPs['ND']['n'+OI], IPs['ND']['s'], *IJ)
        file['VarsValues'] = RZ
        writeFile(file)
    file['VarsName'] = RZtext
    file['ZoneName'] = ('place', 'Nn', 'Ns')
    for OI in ctrl['Sys']['OI']:
        RZ = meshRZ(IPs=IPs, OPs=OPs, ctrl=ctrl, OI=OI)
        OIzone(OI)
        for key in ('At', 'At_1'):
            AtDebug(ND=IPs['ND'], OI=OI, AtName=key, At=OPs[key])
# =============================================================================
# 1D or 2D Contour Figure
# =============================================================================
# 1D contour: along R = 0 i.e. the axis
def ContourPlot(file, IPs, OPs, ctrl, eState):
    def aDL_VarsIset(Nvars):
        def rqIset(IPs, q_1D):
            rI_1D = np.linspace(ctrl['N']['tol'], 1.0, IPs['ND']['nI'])
            rI = Dim1to2(fr=np.expand_dims(rI_1D, axis=1), \
                         fq=np.ones((IPs['ND']['s'], 1)))
            qI = Dim1to2(fr=np.ones((IPs['ND']['nI'], 1)), fq=q_1D)
            return rI, qI
        VarsIValues = np.zeros((IPs['ND']['nI']*IPs['ND']['s'], Nvars))
        rI, qI = rqIset(IPs=IPs, q_1D=OPs['s']['O'])
        Np = OPs['psi']['O'].shape[1]
        DpsiS = np.matmul(OPs['PD']['O'][10][OPs['At']['O']['s']], \
                          OPs['psi']['O'])
        if ctrl['BC']['infRef']:
            if Np==1: U = OPs['mu']
            elif Np==2: U = UpSet()
        else:
            U = 0.0
        psiI, vRI, vZI = DL_psi_vRZ_Inside(r=rI, q=qI, DpsiS=DpsiS, Up=U)
        VarsIValues[:, 0] = (rI*np.sin(qI))[:, 0] #R
        VarsIValues[:, 1] = (rI*np.cos(qI))[:, 0] #Z
        phidS = OPs['phid']['O'][OPs['At']['O']['s']]
        VarsIValues[:, 2] = phid_Inside(r=rI, q=qI, phidS=phidS)[:, 0] #phid
        VarsIValues[:, -5*Np:-4*Np] = psiI #psi
        VarsIValues[:, -4*Np:-3*Np] = vRI #vR
        VarsIValues[:, -3*Np:-2*Np] = vZI #vZ
        return VarsIValues
    def siteSet(OI):
        if ctrl['Sys']['major']=='a':
            Nt = IPs['ND']['n'+OI]*IPs['ND']['s']
            ax = AxisIndex(Nt=Nt, Nx=IPs['ND']['n'+OI])
            return ax[0:len(ax)//2]
        elif ctrl['Sys']['major'] in 'bc':
            return OPs['At'][OI]['ax']
    def OIzone(OI):
        IJ = () if file['dim']==1 else (IPs['ND']['n'+OI], IPs['ND']['s'])
        file['ZoneValues'] = (*IPsChange.values(), OI, *IJ)
        file['VarsValues'] = ContourVarsSet(IPs=IPs, OPs=OPs, ctrl=ctrl, \
                                            OI=OI, eState=eState)
        if file['dim']==1:
            temp = file['VarsValues'][siteSet(OI)]
            file['VarsValues'] = temp[temp[:, 1].argsort(), :]
        writeFile(file)
    Np = 1 if eState else OPs['psi']['O'].shape[1]
    file['VarsName'] = ContourVarsNamesSet(eState=eState, Nj=len(IPs['nj0']),
                                           Np=Np)
    IPsChange = ValueSelector(Dict=IPs, Keys=ctrl['Fig']['Change'])
    file['ZoneName'] = (*(key2name[i] for i in IPsChange.keys()), 'OI')
    for OI in ctrl['Sys']['OI']: OIzone(OI)
    lD_2D = ctrl['Sys']['major']+str(file['dim'])=='a2'
    if lD_2D and ctrl['Sys']['p'] in 'DG':
        IJ = (IPs['ND']['nI'], IPs['ND']['s'])
        file['ZoneValues'] = (*IPsChange.values(), 'I', *IJ)
        file['VarsValues'] = aDL_VarsIset(len(file['VarsName']))
        writeFile(file)
edSet = {True: 'e', False: 'd'}
edTextSet = {True: ('', '_e^*'), False: ('`d', '^*')}
VarsText = ('{}`f{}', '{}`r{}', '{}`r{}/`ka^2')
# e: phi, rho, rho/ka2, nj, ER, EZ
# d: phi, rho, rho/ka2, nj, gj, psi, ER, EZ, vR, vZ
def ContourVarsNamesSet(eState, Nj, Np):
    jIter = range(1, Nj+1)
    edText = edTextSet[eState]
    Names = []
    for text in VarsText: Names.append(text.format(*edText))
    for j in jIter:
        Names.append('{}n_{}{}'.format(edText[0], str(j), edText[1]))
    if not eState:
        for j in jIter: Names.append('g_'+str(j)+'^*')
        Names.append('`y^*')
        Names.extend(['v^*_'+RZ for RZ in RZtext])
    Names.extend([('{}E{}_'+RZ).format(*edText) for RZ in RZtext])
    if eState or Np!=2:
        return [*RZtext, *Names]
    else:
        VarsNames = [*RZtext]
        for var in Names: VarsNames.extend((var+'_1', var+'_2'))
        return VarsNames
def ContourVarsSet(IPs, OPs, ctrl, OI, eState):
    def eVarsSet(edVars):
        if lD:
            edVars = tuple(Dim1to2(fr=fri, fq=np.ones(OPs['s'][OI].shape)) \
                           for fri in edVars)
        return hCombine((RZ, *edVars, *EedRZ))
    def dVarsSet(edVars):
        edVars.extend([*tuple(OPs['gj'][OI][j] for j in jIter)])
        if lD:
            edVars = tuple(Dim1to2(fr=fri, fq=np.cos(OPs['s'][OI])) \
                           for fri in edVars)
            psi = Dim1to2(fr=OPs['psi'][OI], fq=np.sin(OPs['s'][OI])**2)
            vRZ = psi2vRZ_1D(**PD_n_s, psi=OPs['psi'][OI])
        else:
            psi = OPs['psi'][OI]
            vRZ = psi2vRZ_2D(**{i: OPs[i][OI] for i in ('PD', 'psi', 'R')}, \
                             tol=ctrl['N']['tol'])
        return hCombine((RZ, *edVars, psi, *vRZ, *EedRZ))
    lD = ctrl['Sys']['major']=='a'
    RZ = meshRZ(IPs=IPs, OPs=OPs, ctrl=ctrl, OI=OI)
    jIter = OPs['nje']['O'].keys()
    ed = edSet[eState]
    njKey, phiKey = 'nj'+ed, 'phi'+ed
    njed = tuple(OPs[njKey][OI][j] for j in jIter)
    rhoed = rhoSet(OPs[njKey][OI])
    phied = OPs[phiKey][OI]
    edVars = [phied, rhoed, rhoed/IPs['ka']**2, *njed]
    if lD:
        PD_n_s = {i: OPs[i][OI] for i in ('PD', 'n', 's')}
        EedRZ = phi2EREZ_1D(**PD_n_s, phi=phied, eState=eState)
    else:
        EedRZ = phi2EREZ_2D(PD=OPs['PD'][OI], phi=phied)
    return eVarsSet(edVars) if eState else dVarsSet(edVars)
# =============================================================================
# conversion
# =============================================================================
def Dim1to2(fr, fq):
    return np.tile(fr, (len(fq), 1))*np.repeat(fq, len(fr), axis=0)
def phi2EREZ_1D(PD, phi, n, s, eState):
    cosq, sinq = (cs(s) for cs in (np.cos, np.sin))
    DphiDr = np.matmul(PD[10], phi)
    if eState:
        return tuple(-Dim1to2(fr=DphiDr, fq=fq) for fq in (sinq, cosq))
    else:
        cosq2, sinq2 = cosq**2, sinq**2
        phi_n = phi/n
        DphidDR = Dim1to2(fr=DphiDr-phi_n, fq=cosq*sinq)
        DphidDZ = Dim1to2(fr=DphiDr, fq=cosq2)+Dim1to2(fr=phi_n, fq=sinq2)
        return -DphidDR, -DphidDZ
def phi2EREZ_2D(PD, phi):
    return tuple(-np.matmul(PD[DRZ], phi) for DRZ in ('D1R', 'D1Z'))
def psi2vRZ_1D(PD, psi, n, s):
    # vR = vr*cosq-vq*sinq
    # vZ = vr*sinq+vq*cosq
    cosq, sinq = (cs(s) for cs in (np.cos, np.sin))
    DpsiDr_n = np.matmul(PD[10], psi)/n
    psi_n2 = 2.0*psi/n**2
    vR = Dim1to2(fr=DpsiDr_n-psi_n2, fq=cosq*sinq)
    vZ = -Dim1to2(fr=psi_n2, fq=cosq**2)-Dim1to2(fr=DpsiDr_n, fq=sinq**2)
    return vR, vZ
def psi2vRZ_2D(PD, psi, R, tol):
    R[abs(R)<tol] = tol
    return np.matmul(PD['D1Z'], psi)/R, -np.matmul(PD['D1R'], psi)/R
# =============================================================================
# current
# =============================================================================
def fjRZset(IPs, OPs, ctrl, OI):
    def nje2D_gradgj_vRZ_Set():
        DgjDR, DgjDZ, nje2D = {}, {}, {}
        if ctrl['Sys']['major']=='a':
            PDns = {i: OPs[i][OI] for i in ('PD', 'n', 's')}
            for j, gj in OPs['gj'][OI].items():
                DgjDR[j], DgjDZ[j] = phi2EREZ_1D(**PDns, phi=-gj, eState=False)
                nje2D[j] = Dim1to2(fr=OPs['nje'][OI][j], \
                                   fq=np.ones((IPs['ND']['s'], 1)))
            vR, vZ = psi2vRZ_1D(**PDns, psi=OPs['psi'][OI])
        elif ctrl['Sys']['major'] in 'bc':
            for j, gj in OPs['gj'][OI].items():
                DgjDR[j], DgjDZ[j] = phi2EREZ_2D(PD=OPs['PD'][OI], phi=-gj)
                nje2D[j] = OPs['nje'][OI][j].copy()
            vR, vZ = psi2vRZ_2D(PD=OPs['PD'][OI], psi=OPs['psi'][OI], \
                                R=OPs['R'][OI], tol=ctrl['N']['tol'])
        return nje2D, {'R': DgjDR, 'Z': DgjDZ}, {'R': vR, 'Z': vZ}
    # fj = zj/Pej*nje*grad(gj)+nje*v
    nje2D, gradgj, vRZ = nje2D_gradgj_vRZ_Set()
    fjRZ = {j: {RZ: nje2D[j]*(vRZ[RZ]+zj/IPs['Pec'][j]*gradgj[RZ][j]) \
                for RZ in 'RZ'} for j, zj in IPs['zj'].items()}
    return fjRZ
def CurrentDensitySet(fjRZ):
    JRZ = {}
    for RZ in 'RZ': JRZ[RZ] = rhoSet({j: fj[RZ] for j, fj in fjRZ.items()})
    return JRZ
def CurrentStreamLine1D(IPs, OPs, ctrl, OI):
    dGjdr = {j: np.matmul(OPs['PD'][OI][10], gj) \
             for j, gj in OPs['gj'][OI].items()}
    temp = {j: OPs['nje'][OI][j]/Pej*dGjdr[j] \
            for j, Pej in IPs['Pec'].items()}
    SumIterm = Sum_nj_Set(nj=temp, order=2)*OPs['n'][OI]**2/2.0
    SumR = Sum_nj_Set(nj=OPs['nje'][OI], order=1)
    SumRterm = -SumR*np.matmul(OPs['PD'][OI][0], OPs['psi'][OI])
    psiJ = Dim1to2(fr=-ka2_SumI0()*(SumIterm+SumRterm), \
                   fq=np.sin(OPs['s'][OI])**2)
    return psiJ
def integralJalongZ0_1D(IPs, OPs, relative):
    meanIntJZ = 0.0
    for OI in OPs['nje'].keys():
        if OI=='O': outer = OPs['At']['O']['ro']
        elif OI=='I': outer = OPs['At']['I']['sI']
        inner = OPs['At'][OI]['s']
        rOuter = OPs['n'][OI][outer][0, 0]
        rInner = OPs['n'][OI][inner][0, 0]
        njeGj_Pecj = {j: nje*OPs['gj'][OI][j]/IPs['Pec'][j] \
                      for j, nje in OPs['nje'][OI].items()}
        ka2 = ka2_SumI0()
        sumTerm = ka2*Sum_nj_Set(nj=njeGj_Pecj, order=2)
        dpsidr = np.matmul(OPs['PD'][OI][10], OPs['psi'][OI])
        vTerm = rhoSet(OPs['nje'][OI])*dpsidr
        DxDr = DxyDvarSet(a=rInner, b=rOuter)
        Int = IntMxySet(IPs['ND']['n'+OI])/DxDr
        JZ = sumTerm-vTerm
        IntJZ = np.matmul(Int, JZ)
        if relative: down = np.matmul(Int, abs(JZ)) #integral of JZ absolute value
        else: down = 1.0 #0.5*(OPs['n'][OI][outer]**2-OPs['n'][OI][inner]**2) #area
        meanIntJZ = meanIntJZ+IntJZ/down
    return 2.0*np.pi*float(meanIntJZ)
# =============================================================================
# file writing
# =============================================================================
ZoneT = 'ZONE T="'
isnaninf = (np.isnan, np.isinf)
contour = {0: '', 1: '', 2: ', I={}, J={}, F=POINT'}
LogFileName = 'ResultLog.txt'
resultFileName = 'Result{}.dat'
PlotFs = {'0D_mu': Dim0_mu, \
          '1D_EOF': Dim1_EOF, \
          '1D_phie': partial(ContourPlot, eState=True), \
          '1D_debug': partial(ContourPlot, eState=False), \
          '1D_real': partial(ContourPlot, eState=False), \
          '2D_mesh': Dim2_mesh, \
          '2D_phie': partial(ContourPlot, eState=True), \
          '2D_debug': partial(ContourPlot, eState=False), \
          '2D_real': partial(ContourPlot, eState=False)}
def createFile(ctrlFig, DIYs):
    NewPlotFs = {**PlotFs, **DIYs}
    Files = {}
    for dim, subtypes in ctrlFig.items():
        for subtype, save in subtypes.items():
            key = str(dim)+'D_'+subtype
            Files[key] = {'noVariableLine': True, 'save': save, 'dim': dim}
            Files[key]['FileName'] = resultFileName.format(key)
            Files[key]['plot'] = NewPlotFs[key]
            if save:
                with open(Files[key]['FileName'],'w') as x: x.write('')
    return Files
def writeVarsNames(file):
    file['noVariableLine'] = False
    with open(file['FileName'],'a') as x:
        x.write('variables='+', '.join(file['VarsName'])+'\n')
def writeZone(file):
    FullZone = ZoneT+'={} '.join((*file['ZoneName'], ''))+'"'
    FullZone = FullZone+contour[file['dim']]
    with open(file['FileName'],'a') as x:
        x.write((FullZone+"\n").format(*file['ZoneValues']))
def writeData(file):
    with open(file['FileName'],'a') as x:
        temp = {isxxx(file['VarsValues']).any() for isxxx in isnaninf}
        if True not in temp:
            VarsLen = len(file['VarsValues'][0])
            for Vars in np.real(file['VarsValues']):
                x.write(('{:16.8e} '*VarsLen+'\n').format(*Vars))
def writeFile(file):
    if file['save']:
        if file['noVariableLine']: writeVarsNames(file)
        if file['dim']==0:
            if file.get('FL'): writeZone(file)
        else:
            writeZone(file)
        writeData(file)
# =============================================================================
# Packaging result files
# =============================================================================
Path_Name = '{}//{}'
def packingFile(packageName, startTime):
    def CopyFile(name):
        oldPath = Path_Name.format(sourcePath, name)
        newPath = Path_Name.format(FullPackageName, name)
        copyfile(oldPath, newPath)
    sourcePath = getcwd()
    now = strftime("%Y%m%d_%H%M%S", localtime())
    FullPackageName = Path_Name.format(sourcePath, now+'_'+packageName)
    mkdir(FullPackageName)
    fileList = listdir(sourcePath)
    for i in PlotFs.keys():
        datName = resultFileName.format(i)
        if datName in fileList:
            if getsize(datName)>0 and getmtime(datName)>startTime:
                CopyFile(datName)
    CopyFile(LogFileName)