import numpy as np
IPs, OPs, ctrl = {}, {}, {} #changed by main program
# =============================================================================
# equilibrium
# =============================================================================
def Sum_nj_Set(nj, order):
    return sum(IPs['zj'][j]**order*nj[j] for j in IPs['zj'].keys())
ka2_SumI0 = lambda: IPs['ka']**2/Sum_nj_Set(nj=IPs['nj0'], order=2)
rhoSet = lambda nj: ka2_SumI0()*Sum_nj_Set(nj=nj, order=1)
def njeSet(phie):
    expTerm = {j: np.exp(-zj*phie) for j, zj in IPs['zj'].items()}
    nj0exp = {j: IPs['nj0'][j]*expj for j, expj in expTerm.items()}
    if ctrl['Sys']['m']['IL']:
        down = IPs['nu']*(sum(nj0exp.values())-sum(IPs['nj0'].values()))+1.0
    else:
        down = 1.0
    return {j: nj0expj/down for j, nj0expj in nj0exp.items()}
def rhoFixModify(nje, OI):
    if OI=='I':
        if ctrl['Sys']['p'] in 'PSM':
            rhoFix = IPs['rhoFix']
            # if ctrl['Sys']['p']['CR']: rhoFix = rhoFix*CRfactor(n3e=nje[3]) #CR pouous
            if ctrl['BC'].get('SPB'): rhoFix = rhoFix/OPs['n']['I']**2
        else:
            rhoFix = 0.0
    elif OI=='O':
        rhoFix = 0.0
    return rhoFix
def DrhoFixDphie(n3e):  #CR pouous
    pass
def nuTermSet():
    OItext = 'OI' if 'phidI' in ctrl['Sys']['dVars'] else 'O'
    if ctrl['Sys']['m']['IL']:
        nuTerm = {}
        for OI in OItext:
            nuSumR = IPs['nu']*Sum_nj_Set(nj=OPs['nje'][OI], order=1)
            nuTerm[OI] = {j: 1.0-nuSumR/zj for j, zj in IPs['zj'].items()}
    else:
        nuTerm = {OI: {j: 1.0 for j in IPs['zj'].keys()} for OI in OItext}
    return nuTerm
def l_m1m2Set():
    Lc = IPs['kaLc']/IPs['ka']
    if abs(Lc)<ctrl['N']['tol'] or not ctrl['Sys']['m']['IL']:
        l_m1, m2 = 0.0, IPs['ka']
    else:
        Lc2 = Lc**2
        Delta = (complex(1.0-4.0*IPs['kaLc']**2))**0.5
        l_m1 = (2.0*Lc2/(1.0+Delta))**0.5
        m2 = ((1.0-Delta)/2.0/Lc2)**0.5
    return l_m1, m2
# =============================================================================
# disturbance
# =============================================================================
def rhodScaleTerm(OI):
    # for RHS of plane system
    if ctrl['Sys']['m']['Diffu']:
        lj = nuTermSet()
        Dnjeff_zjnj0 = {j: Dnjeff_zjnjSet(j=j, nj=IPs['nj0']) \
                       for j in IPs['nj0'].keys()}
        temp = {i: Dnjeff_zjnj0[i]*lj['O'][i]*nie \
                for i, nie in OPs['nje']['O'].items()}
        SumDnjeff = Sum_nj_Set(nj=temp, order=2)
        return ka2_SumI0()*SumDnjeff*OPs['Z'][OI]
    else:
        return np.zeros(OPs['Z'][OI].shape)
def njdSet(phid, gj):
    def ILtermSet(OI):
        njegj = {j: OPs['nje'][OI][j]*gj[OI][j] \
                     for j in IPs['zj'].keys()}
        SumR_njegj = Sum_nj_Set(nj=njegj, order=1)
        SumR_nje = Sum_nj_Set(nj=OPs['nje'][OI], order=1)
        return SumR_nje*phid[OI]+SumR_njegj
    njd = {OI: {} for OI in ctrl['Sys']['OI']}
    for OI in ctrl['Sys']['OI']:
        if ctrl['Sys']['m']['IL']: nuSumR = IPs['nu']*ILtermSet(OI)
        else: nuSumR = 0.0
        for j, zj in IPs['zj'].items():
            njd[OI][j] = -zj*OPs['nje'][OI][j]*(phid[OI]+gj[OI][j]-nuSumR/zj)
    return njd
def WmpSet(Inside):
    TermUp = 0.0
    if ctrl['Sys']['m']['AC']:
        if Inside: DensityRatio = IPs['density']
        else: DensityRatio = 1.0
        TermUp = TermUp+1.0j*IPs['w']*IPs['Re']*DensityRatio
    if Inside:
        if ctrl['Sys']['p'] in 'GPSM': TermUp = TermUp+IPs['aldap']**2
        if ctrl['Sys']['p'] in 'G': return (TermUp/IPs['vis'])**0.5
        else: return TermUp**0.5
    else:
        if ctrl['Sys']['m']['Gel']: TermUp = TermUp+IPs['aldam']**2
        return TermUp**0.5
# effective viscosity ratio calculator (for 1D)
def visEffSet(r):
    if ctrl['Sys']['p'] in 'DGM':
        Wpr = WmpSet(True)*r
        Wpr2 = Wpr**2
        tanhWpr = np.tanh(Wpr)
        visEffDown = Wpr2*tanhWpr-3.0*Wpr+3.0*tanhWpr
        if abs(visEffDown)<ctrl['N']['tol']:
            return IPs['vis']
        else:
            visEffUp = Wpr2*Wpr-3.0*Wpr2*tanhWpr+6.0*Wpr-6.0*tanhWpr
            return visEffUp/visEffDown*IPs['vis']/3.0
    else:
        return None
# =============================================================================
# driving force
# =============================================================================
EexTF = {False: np.array([[0.0, 1.0]]), True: np.array([[0.0, 0.0]])}
Dn1exTF = {False: np.array([[0.0, 0.0]]), True: np.array([[0.0, 1.0]])}
AWreverse = lambda AW: -1.0 if AW else 1.0
def UpSet():
    return AWreverse(ctrl['Sys']['OB'].get('A-W'))*np.array([1.0, 0.0])
def l_PecjSet(Pec): #the product of all Pec/Pec[j] #20200701
    l_Pecj = {}
    for j in Pec.keys():
        l_Pecj[j] = 1.0
        for i in {*Pec.keys()}-{j}:
            l_Pecj[j] = l_Pecj[j]*Pec[i]
    return l_Pecj
def EeffSet(nj):
    if ctrl['Sys']['m']['Diffu']: #20200701
        l_Pecj = l_PecjSet(IPs['Pec'])
        Dnj_Pej = {j: DnjeffSet(j=j, nj=nj)*l_Pecj[j] \
                   for j in IPs['Pec'].keys()}
        up = Sum_nj_Set(nj=Dnj_Pej, order=1)
        nj_Pej = {j: nj[j]*l_Pecj[j] for j in nj.keys()}
        down = Sum_nj_Set(nj=nj_Pej , order=2)
        DiffuTerm = up/down
    else:
        DiffuTerm = 0.0 if np.size(nj[1])==1 else np.zeros(nj[1].shape)
    sign = AWreverse(ctrl['Sys']['OB'].get('A-W'))
    return sign*EexTF[ctrl['Sys']['m']['Diffu']]+DiffuTerm
sites = {'a': ('ro', ), 'c': ('u', 'd')}
def EeffForSites():
    if ctrl['Sys']['major']=='a': EeffInf = not ctrl['Sys']['OB']['Cell']
    elif ctrl['Sys']['major']=='b': EeffInf = True
    elif ctrl['Sys']['major']=='c': EeffInf = False
    if EeffInf:
        Eeff = {'inf': EeffSet(IPs['nj0'])}
    else:
        Eeff = {}
        for site in sites[ctrl['Sys']['major']]:
            Eeff[site] = EeffSet({j: nje[OPs['At']['O'][site]] \
                                 for j, nje in OPs['nje']['O'].items()})
    return Eeff
def DnjexSet(j):
    # assume only 1, 2 in external ion gradient
    Dn1ex = Dn1exTF[ctrl['Sys']['m']['Diffu']]
    # such that z1*Dn1ex+z2*Dn2ex+z3*Dn3ex = 0
    if j==1: return Dn1ex
    elif j==2: return Dn1ex*IPs['nj0'][2]/IPs['nj0'][1]
    elif j==3: return Dn1ex*IPs['nj0'][3]/IPs['nj0'][1]
def DnjeffSet(j, nj):
    Dnjex = DnjexSet(j)
    if ctrl['Sys']['m']['IL']:
        nTe = sum(nji for nji in nj.values())
        DnTex = sum(DnjexSet(i) for i in nj.keys())
        nuTerm = IPs['nu']/(1.0-IPs['nu']*nTe)*nj[j]*DnTex
    else:
        nuTerm = 0.0
    return AWreverse(ctrl['Sys']['OB'].get('A-W'))*(Dnjex+nuTerm)
def Dnjeff_zjnjSet(j, nj):
    if ctrl['Sys']['m']['Diffu']:
        return DnjeffSet(j=j, nj=nj)/IPs['zj'][j]/nj[j]
    else:
        return 0.0
def betaSet(): #20200701
    l_Pecj = l_PecjSet(IPs['Pec'])
    alpha = -IPs['zj'][2]/IPs['zj'][1]
    return (l_Pecj[1]-l_Pecj[2])/(l_Pecj[1]+alpha*l_Pecj[2])