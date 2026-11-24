
import ROOT
import os

ROOT.gErrorIgnoreLevel = ROOT.kFatal

# /eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano/Summer20UL18_106x_nAODv9_Full2018v9/MCl1loose2018v9__MCCorr2018v9NoJERInHorn__l2tightOR2018v9
mcProduction = 'Summer20UL18_106x_nAODv9_Full2018v9'
mcSteps      = 'MCl1loose2018v9__MCCorr2018v9NoJERInHorn__l2tightOR2018v9'
treeBaseDir  = '/eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano'

dataReco = 'Run2018_UL2018_nAODv9_Full2018v9'
fakeSteps = 'DATAl1loose2018v9__l2loose__fakeW'
dataSteps = 'DATAl1loose2018v9__l2loose__l2tightOR2018v9'

#--------- Keep it commented, limitfiles is set in k-xgb.py and xgb_train.py
#--------- Uncomment here if you are explicitly debugging this script
# limitFiles   = -1   
# limitFiles   = 1

def makeMCDirectory(var=""):
    _treeBaseDir = treeBaseDir + ""
    if var == "":
        return "/".join([_treeBaseDir, mcProduction, mcSteps])
    else:
        return "/".join([_treeBaseDir, mcProduction, mcSteps + "__" + var])

mcDirectory = makeMCDirectory()
fakeDirectory = os.path.join(treeBaseDir, dataReco, fakeSteps)
dataDirectory = os.path.join(treeBaseDir, dataReco, dataSteps)


from search_files import SearchFiles
s = SearchFiles()

useXROOTD = False
redirector = 'root://eoscms.cern.ch/'

# def nanoGetSampleFiles(path, name):
#   _files = searchFiles.searchFiles(path, name, redirector=redirector)
#   return  {name : _files}

# # local files (e.g. /eos/user/...), no redirector
# def nanoGetLocalSampleFiles(path, name):
#   _files = searchFiles.searchFiles(path, name, redirector='')
#   return  {name : _files}


def nanoGetSampleFiles(path, name):
    _files = s.searchFiles(path, name, redirector=redirector)
    if limitFiles != -1 and len(_files) > limitFiles:
        return [(name, _files[:limitFiles])]
    return [(name, _files)]

def nanoGetLocalSampleFiles(path, name):
    _files = s.searchFiles(path, name, redirector='')
    if limitFiles != -1 and len(_files) > limitFiles:
        return [(name, _files[:limitFiles])]
    return [(name, _files)]



def addSubSampleWeights(samples, sampleName, subSampleName, weight):
  if 'weights' not in samples[sampleName].keys():
    samples[sampleName]['weights'] = {}
  if subSampleName in samples[sampleName]['weights'].keys():
    samples[sampleName]['weights'][subSampleName] = "(" + samples[sampleName]['weights'][subSampleName] + ") * " +  weight
  else :
    samples[sampleName]['weights'][subSampleName] = weight


def flatten(tagged_files):
    return [f for _, filelist in tagged_files for f in filelist]
#
# The weights
#

# mcCommonWeight = 'XSWeight * SFweight2l * LepWPCut * LepWPSF * Jet_PUIDSF * btagSF * METFilter_MC * PromptGenLepMatch2l'




mcCommonWeight = "XSWeight*SFweight*METFilter_MC*PromptGenLepMatch2l"

TOP_PTRW = (
    "((topGenPt*antitopGenPt > 0.)"
    "*(TMath::Sqrt(TMath::Exp(0.0615-0.0005*topGenPt)*TMath::Exp(0.0615-0.0005*antitopGenPt)))"
    "+(topGenPt*antitopGenPt <= 0.))"
)

GSTAR_LOW  = "(Gen_ZGstar_mass > 0 && Gen_ZGstar_mass < 4)"
GSTAR_HIGH = "(Gen_ZGstar_mass < 0 || Gen_ZGstar_mass > 4)"

signal_path = "/eos/user/a/amassiro/HIG/ZHggPostProc/Summer20UL18_106x_nAODv9_Full2018v9/MCFull2018v9/"


samples = {}

# samples['Hgluglu'] = [
#     {'tag': 'Hgluglu', 'files': flatten(nanoGetLocalSampleFiles(signal_path, "ZHgg")),    # NLO sample: negative weights
#      'weight': "genWeight*0.8839*0.08187*0.033658*3", 'isSignal': True},
# ]

# samples['qqZHgluglu'] = [
#     {'tag': 'qqZHgluglu', 'files': flatten(nanoGetLocalSampleFiles(signal_path, "ZHllHgg")), # NLO sample: negative weights
#      'weight': "genWeight*0.7612*0.08187*0.033658*3", 'isSignal': True},
# ]

samples['ggZHgluglu'] = [
    {'tag': 'ggZHgluglu', 'files': flatten(nanoGetLocalSampleFiles(signal_path, "ggZHllHgg")), # Lo sample: positive weights
     'weight': "genWeight*0.1227*0.08187*0.033658*3", 'isSignal': True},
]

# samples['ZH_HToGluGlu_ZToLL-M125'] = [
#     {'tag': 'ggZHgluglu', 'files': flatten(nanoGetSampleFiles(mcDirectory, "ZH_HToGluGlu_ZToLL-M125")), # NLO sample: negative weights
#      'weight': "genWeight*0.1227*0.08187*0.033658*3", 'isSignal': True},
# ]

samples['DY'] = [
    {'tag': 'DY', 'files': flatten(
        # nanoGetSampleFiles(mcDirectory, 'DYJetsToLL_M-10to50_NLO')
        # nanoGetSampleFiles(mcDirectory, 'DYJetsToLL_M-50')),
    #  'weight': mcCommonWeight, 'isSignal': False},
    #======================================================================
     nanoGetSampleFiles(mcDirectory, 'DYJetsToLL_M-50-LO')+                  # Lo sample: positive weights
     nanoGetSampleFiles(mcDirectory, 'DYJetsToLL_M-10to50-LO') +             # Lo sample: positive weights
     nanoGetSampleFiles(mcDirectory, 'DYJetsToLL_M-50_HT-100to200') +       # Lo sample: positive weights
     nanoGetSampleFiles(mcDirectory, 'DYJetsToLL_M-50-LO_ext1')),           # Lo sample: positive weights
        'weight': mcCommonWeight, 'isSignal': False},
]



# samples['DY_test'] = [
#     {'tag': 'DY', 'files': flatten(
#                 nanoGetSampleFiles(mcDirectory, 'DYJetsToLL_M-10to50_NLO')+    #NLO sample: negative weights
#                 nanoGetSampleFiles(mcDirectory, 'DYJetsToLL_M-50')),            # NLO sample: NLO negative weights
#                 'weight': mcCommonWeight, 'isSignal': False},
# ]

# samples["DY_all"] = [
#     {'tag': 'DY_all', 'files': flatten(
#                 nanoGetSampleFiles(mcDirectory, 'DYJetsToLL')),
#                 'weight': mcCommonWeight, 'isSignal': False},
# ]

# samples['ZH_HToGluGlu_ZToLL-M125'] = [
#     {'tag': 'ggZHgluglu', 'files': flatten(nanoGetSampleFiles(mcDirectory, "ZH_HToGluGlu_ZToLL-M125")),
#      'weight': "genWeight*0.1227*0.08187*0.033658*3", 'isSignal': True},
# ]

print("Limiting number of files per sample to:", limitFiles)
print("Number of samples:", len(samples.keys()))
for sampleName, subentries in samples.items():
    total = sum(len(e['files']) for e in subentries)
    print("Sample:", sampleName, "sub-entries:", len(subentries), "total files:", total)

# print(makeMCDirectory())
