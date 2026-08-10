import ROOT
import os

ROOT.gErrorIgnoreLevel = ROOT.kFatal

# MC:   /eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano/Summer20UL18_106x_nAODv9_Full2018v9/MCl1loose2018v9__MCCorr2018v9NoJERInHorn__l2tightOR2018v9/
# DATA: /eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano/Run2018_UL2018_nAODv9_Full2018v9/DATAl1loose2018v9__l2loose__l2tightOR2018v9/
# FAKE: /eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano/Run2018_UL2018_nAODv9_Full2018v9/DATAl1loose2018v9__l2loose__fakeW/

mcProduction = 'Summer20UL18_106x_nAODv9_Full2018v9'
dataReco     = 'Run2018_UL2018_nAODv9_Full2018v9'
mcSteps      = 'MCl1loose2018v9__MCCorr2018v9NoJERInHorn__l2tightOR2018v9'
fakeSteps    = 'DATAl1loose2018v9__l2loose__fakeW'
dataSteps    = 'DATAl1loose2018v9__l2loose__l2tightOR2018v9'

treeBaseDir = '/eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano'
limitFiles = -1
# limitFiles = 1


if limitFiles != -1:
    print("Limiting the number of files to %d" % limitFiles)

def makeMCDirectory(var=''):
    return os.path.join(treeBaseDir, mcProduction, mcSteps.format(var=''))

mcDirectory   = makeMCDirectory()
# fakeDirectory = os.path.join(treeBaseDir, dataReco, fakeSteps)
# dataDirectory = os.path.join(treeBaseDir, dataReco, dataSteps)

print("Running with the following directories:")
print (" mcDirectory = " , mcDirectory)
# print (" fakeDirectory = " , fakeDirectory)
# print (" dataDirectory = " , dataDirectory)

samples = {}
from mkShapesRDF.lib.search_files import SearchFiles
s = SearchFiles()

useXROOTD = True
redirector = 'root://eoscms.cern.ch/'


def nanoGetSampleFiles(path, name):   # it is doing the same as searchFiles but with a limit on the number of files
    # print ("nanoGetSampleFiles!")
    _files = s.searchFiles(path, name, redirector=redirector)
    if limitFiles != -1 and len(_files) > limitFiles:
        return [(name, _files[:limitFiles])]
    else:
        return [(name, _files)]

def nanoGetLocalSampleFiles(path, name):  # it is doing the same as searchFiles but with a limit on the number of files. the difference with nanoGetSampleFiles is that it does not use the redirector, so it is used for local files
    # print ("nanoGetLocalSampleFiles!")
    _files = s.searchFiles(path, name, redirector='')
    if limitFiles != -1 and len(_files) > limitFiles:
        return [(name, _files[:limitFiles])]
    else:
        return [(name, _files)]


########## Signal Samples #########
print("\n------------------------------------------------------------------------------")
print("Getting the list of files for the signal samples...\n")
files_ZHgg = nanoGetLocalSampleFiles("/eos/user/a/amassiro/HIG/ZHggPostProc/Summer20UL18_106x_nAODv9_Full2018v9/MCFull2018v9/", "ZHgg")
# print (" list of files Hgg = ", files_ZHgg)
# print(" number of files Hgg = ", len(files_ZHgg[0][1]))

files_ZHllHgg = nanoGetLocalSampleFiles("/eos/user/a/amassiro/HIG/ZHggPostProc/Summer20UL18_106x_nAODv9_Full2018v9/MCFull2018v9/", "ZHllHgg")
# print (" list of files ZHllHgg = ", files_ZHllHgg)
# print(" number of files ZHllHgg = ", len(files_ZHllHgg[0][1]))

files_ggZHllHgg = nanoGetLocalSampleFiles("/eos/user/a/amassiro/HIG/ZHggPostProc/Summer20UL18_106x_nAODv9_Full2018v9/MCFull2018v9/", "ggZHllHgg")
# print (" list of files ggZHllHgg = ", files_ggZHllHgg)
# print(" number of files ggZHllHgg = ", len(files_ggZHllHgg[0][1]))
print("------------------------------------------------------------------------------")


###########################################
#############  BACKGROUNDS  ###############
###########################################

########## Signal Samples #########
print("\n------------------------------------------------------------------------------")
print("Getting the list of files for the Background samples...\n")
############ DY ############

files_DY = nanoGetSampleFiles(mcDirectory, 'DYJetsToLL_M-10to50_NLO') + \
        nanoGetSampleFiles(mcDirectory, 'DYJetsToLL_M-50')
# print("DY files = ", len(files_DY[0][1]))
# print("DY files = ", len(files_DY[0][1])+ len(files_DY[1][1]))

##### Top #######

files_top = nanoGetSampleFiles(mcDirectory, 'TTTo2L2Nu') + \
        nanoGetSampleFiles(mcDirectory, 'ST_s-channel') + \
        nanoGetSampleFiles(mcDirectory, 'ST_t-channel_top') + \
        nanoGetSampleFiles(mcDirectory, 'ST_t-channel_antitop') + \
        nanoGetSampleFiles(mcDirectory, 'ST_tW_antitop') + \
        nanoGetSampleFiles(mcDirectory, 'ST_tW_top')
# print("Top files = ", len(files_top[0][1])+
#       len(files_top[1][1]) + \
#       len(files_top[2][1]) + \
#       len(files_top[3][1]) + \
#       len(files_top[4][1]) + \
#       len(files_top[5][1])  )

######## Vg ########
files_Vg = nanoGetSampleFiles(mcDirectory, 'Wg_AMCNLOFXFX_01J') + \
        nanoGetSampleFiles(mcDirectory, 'ZGToLLG')
# print("Vg files = ", len(files_Vg[0][1])+len(files_Vg[1][1]))

######## VgS ######## 
files_VgS = nanoGetSampleFiles(mcDirectory, 'Wg_AMCNLOFXFX_01J') + \
        nanoGetSampleFiles(mcDirectory, 'WZTo3LNu_mllmin0p1') + \
        nanoGetSampleFiles(mcDirectory, 'ZGToLLG')
# print("VgS files = ", len(files_VgS[0][1])+len(files_VgS[1][1])+len(files_VgS[2][1]))

############ WZ ############
files_WZ = nanoGetSampleFiles(mcDirectory, 'WZTo3LNu_mllmin0p1') + \
        nanoGetSampleFiles(mcDirectory, 'WZTo2Q2L_mllmin4p0')
# print("WZ files = ", len(files_WZ[0][1]) + len(files_WZ[1][1]))

files_ZZ = nanoGetSampleFiles(mcDirectory, 'ZZTo2L2Nu') + \
        nanoGetSampleFiles(mcDirectory, 'ZZTo2Q2L_mllmin4p0') + \
        nanoGetSampleFiles(mcDirectory, 'ZZTo4L')
# print("ZZ files = ", len(files_ZZ[0][1]) + len(files_ZZ[1][1]) + len(files_ZZ[2][1]))

########## VVV #########
files_VVV = nanoGetSampleFiles(mcDirectory, 'ZZZ') + \
        nanoGetSampleFiles(mcDirectory, 'WZZ') + \
        nanoGetSampleFiles(mcDirectory, 'WWZ') + \
        nanoGetSampleFiles(mcDirectory, 'WWW')
# print("VVV files = ", len(files_VVV[0][1])+len(files_VVV[1][1])+len(files_VVV[2][1])+len(files_VVV[3][1]))

print("\n------------------------------------------------------------------------------")

# samples['ZHgg'] = {  # 60 files         ---- DONE
#     'name': files_ZHgg[0][1],}

samples['ZHllHgg'] = { # 9984 files
    'name': files_ZHllHgg[0][1],}   

samples['ggZHllHgg'] = { # 9946 files
    'name': files_ggZHllHgg[0][1],} 

# samples['DY'] = { #253 FILES
#     'name': files_DY[0][1] + files_DY[1][1],}

# samples['top'] = { # 528 files
#     'name': files_top[0][1] + files_top[1][1] + files_top[2][1] + files_top[3][1] + files_top[4][1] + files_top[5][1],}   

# samples['Vg'] = { # 102 files -------------------- DONE 
#     'name': files_Vg[0][1] + files_Vg[1][1],}    

# samples['VgS'] = { # 215 files
#     'name': files_VgS[0][1] + files_VgS[1][1] + files_VgS[2][1],}   

# samples['WZ'] = { # 135 files
#     'name': files_WZ[0][1] + files_WZ[1][1],}

# samples['ZZ'] = { # 233 files
#     'name': files_ZZ[0][1] + files_ZZ[1][1] + files_ZZ[2][1],}    

# samples['VVV'] = { # 39 files                   DONE 
#     'name': files_VVV[0][1] + files_VVV[1][1] + files_VVV[2][1] + files_VVV[3][1],}

print("Number of samples:", len(samples.keys()))

for sampleName, sample in samples.items():
    print("Sample:", sampleName, "Number of files:", len(sample['name']))