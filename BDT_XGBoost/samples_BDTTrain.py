
import ROOT
import os

ROOT.gErrorIgnoreLevel = ROOT.kFatal

# /eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano/Summer20UL18_106x_nAODv9_Full2018v9/MCl1loose2018v9__MCCorr2018v9NoJERInHorn__l2tightOR2018v9
mcProduction = 'Summer20UL18_106x_nAODv9_Full2018v9'
mcSteps      = 'MCl1loose2018v9__MCCorr2018v9NoJERInHorn__l2tightOR2018v9'
treeBaseDir  = '/eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano'
# limitFiles   = -1
# limitFiles   = 1

def makeMCDirectory():
    return os.path.join(treeBaseDir, mcProduction, mcSteps)

mcDirectory = makeMCDirectory()

from mkShapesRDF.lib.search_files import SearchFiles
s = SearchFiles()
redirector = 'root://eoscms.cern.ch/'


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

def flatten(tagged_files):
    return [f for _, filelist in tagged_files for f in filelist]


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

#=======================================================================
# TRAINIG SAMPLE
# ======================================================================
samples['Hgluglu'] = [
    {'tag': 'Hgluglu', 'files': flatten(nanoGetLocalSampleFiles(signal_path, "ZHgg")),
     'weight': "genWeight*0.8839*0.08187*0.033658*3", 'isSignal': True},
]

samples['qqZHgluglu'] = [
    {'tag': 'qqZHgluglu', 'files': flatten(nanoGetLocalSampleFiles(signal_path, "ZHllHgg")),
     'weight': "genWeight*0.7612*0.08187*0.033658*3", 'isSignal': True},
]

samples['ggZHgluglu'] = [
    {'tag': 'ggZHgluglu', 'files': flatten(nanoGetLocalSampleFiles(signal_path, "ggZHllHgg")),
     'weight': "genWeight*0.1227*0.08187*0.033658*3", 'isSignal': True},
]

samples['DY_train'] = [
    {'tag': 'DY', 'files': flatten(
        # nanoGetSampleFiles(mcDirectory, 'DYJetsToLL_M-10to50_NLO')
        # nanoGetSampleFiles(mcDirectory, 'DYJetsToLL_M-50')),
    #  'weight': mcCommonWeight, 'isSignal': False},
    #======================================================================
     nanoGetSampleFiles(mcDirectory, 'DYJetsToLL_M-50-LO')+
     nanoGetSampleFiles(mcDirectory, 'DYJetsToLL_M-10to50-LO') +
     nanoGetSampleFiles(mcDirectory, 'DYJetsToLL_M-50_HT-100to200') +
     nanoGetSampleFiles(mcDirectory, 'DYJetsToLL_M-50-LO_ext1')),
        'weight': mcCommonWeight, 'isSignal': False},
]


# =======================================================================
# Test sample
# = ====================================================================

samples['DY_test'] = [
    {'tag': 'DY', 'files': flatten(
                nanoGetSampleFiles(mcDirectory, 'DYJetsToLL_M-10to50_NLO')+
                nanoGetSampleFiles(mcDirectory, 'DYJetsToLL_M-50')),
                'weight': mcCommonWeight, 'isSignal': False},
]

# samples["DY_all"] = [
#     {'tag': 'DY_all', 'files': flatten(
#                 nanoGetSampleFiles(mcDirectory, 'DYJetsToLL')),
#                 'weight': mcCommonWeight, 'isSignal': False},
# ]

samples['ZH_HToGluGlu_ZToLL-M125'] = [
    {'tag': 'ggZHgluglu', 'files': flatten(nanoGetSampleFiles(mcDirectory, "ZH_HToGluGlu_ZToLL-M125")),
     'weight': "genWeight*0.1227*0.08187*0.033658*3", 'isSignal': True},
]

print("Limiting number of files per sample to:", limitFiles)
print("Number of samples:", len(samples.keys()))
for sampleName, subentries in samples.items():
    total = sum(len(e['files']) for e in subentries)
    print("Sample:", sampleName, "sub-entries:", len(subentries), "total files:", total)
