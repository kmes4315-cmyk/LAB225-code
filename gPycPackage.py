from py_compile import compile
from time import strftime, localtime
from re import search as re_search
from functools import partial
from os import listdir, getcwd, mkdir, environ
from os.path import exists, getmtime
from shutil import copyfile
from sys import exit as sys_exit
from sys import version as pyVersion
from gMain import SysAllowChange, DataAllowChange, ctrlPackage
# =============================================================================
# folder creator
# =============================================================================
def CreatePackage(path, name, Ntry=10):
    now = strftime("%Y%m%d_%H%M%S", localtime())
    FullName = path+'\\'+now+'_'+name
    for i in range(Ntry):
        if not exists(FullName):
            mkdir(FullName)
            FileCreated = True
            break
        FullName = FullName+'(%d)'%i
    if not FileCreated:
        print('\033[41mfolder name already exists!\033[0m')
        sys_exit(1)
    return FullName, now
# =============================================================================
# py to pyc
# =============================================================================
def GetPyList(path, regExpr, SkipList):
    return [*filter(partial(re_search, regExpr), set(listdir(path))-SkipList)]
def py2pyc(pyList, SourcePath, PackagePath):
    VerNo = pyVersion[0]+pyVersion[2]
    sub = '.cpython-'+VerNo+'.pyc'
    for pyName in pyList:
        compile(pyName)
        OldPath = SourcePath+'\\__pycache__\\'+pyName[:-3]+sub
        NewPath = PackagePath+'\\'+pyName[:-3]+'.pyc'
        copyfile(OldPath, NewPath)
# =============================================================================
# set gInterface.py
# =============================================================================
def VersionText(pyList):
    verText = '# Build by: '+environ['ComputerName']+'\n'
    verText += '# Last Edit Time of Files:\n'
    for pyName in pyList:
        mTime = strftime("%Y %m.%d %H:%M:%S", localtime(getmtime(pyName)))
        verText += ('#    '+pyName+': '+mTime+'\n')
    return verText
def MainTextSet(fileName):
    with open(fileName, 'r') as x: oText = x.read()
    Sys_a = oText.find("\nctrl['Sys']")
    Sys_b = Sys_a+re_search("\n *}\n", oText[Sys_a:]).end()
    Data_a = oText.find("\nctrlData")
    Data_b = Data_a+re_search("\n *}\n", oText[Data_a:]).end()
    SysPart = oText[:Sys_a]+SysText()
    DataPart = DataText()+oText[Data_b:]
    return SysPart+oText[Sys_b:Data_a]+DataPart
def LinkText(comment, text):
    return "\n# allow change: "+', '.join(comment)+'\\\n'.join(text)
def SysText():
    allowSys = SysAllowChange()
    comment = []
    text = ["\nctrl['Sys'] = {", ]
    for key1, value1 in allowSys.items():
        text.append("    '%s': {"%key1)
        for key2, value2 in value1.items():
            text.append("        '%s': %s, "%(key2, value2))
            if type(value2)!=bool: comment.append(key2)
        text.append("        }, ")
    text.append("    }\n")
    return LinkText(comment=comment, text=text)
def DataText():
    allowData = DataAllowChange()
    comment = []
    text = ["\nctrlData = {", ]
    for key1, value1 in allowData.items():
        text.append("    '%s': %s, "%(key1, value1))
        comment.append(key1)
    text.append("    }\n")
    return LinkText(comment=comment, text=text)
# =============================================================================
# interface
# =============================================================================
def BuildPycPackage(PackageName):
    SourcePath = getcwd()
    PackagePath, now = CreatePackage(path=SourcePath, name=PackageName)
    interface = 'g0Interface.py'
    SkipList = {interface, 'gPycPackage.py'}
    pyList = GetPyList(path=SourcePath, regExpr='^g.*\.py$', SkipList=SkipList)
    py2pyc(pyList=pyList, SourcePath=SourcePath, PackagePath=PackagePath)
    with open(PackagePath+'\\'+interface, 'w') as x:
        x.write(VersionText(pyList)+MainTextSet(interface))
    print('Package: %s is built suceessfully'%PackageName)
if ctrlPackage['Create']: BuildPycPackage(ctrlPackage['Name'])