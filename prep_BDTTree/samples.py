import ROOT
import os

ROOT.gErrorIgnoreLevel = ROOT.kFatal

mcProduction = 'Summer20UL18_106x_nAODv9_Full2018v9'
mcSteps      = 'MCl1loose2018v9__MCCorr2018v9NoJERInHorn__l2tightOR2018v9'
treeBaseDir  = '/eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano'
limitFiles   = -1
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


mcCommonWeight = "XSWeight*SFweight_val*METFilter_MC*PromptGenLepMatch2l_val"

TOP_PTRW = (
    "((topGenPt*antitopGenPt > 0.)"
    "*(TMath::Sqrt(TMath::Exp(0.0615-0.0005*topGenPt)*TMath::Exp(0.0615-0.0005*antitopGenPt)))"
    "+(topGenPt*antitopGenPt <= 0.))"
)

GSTAR_LOW  = "(Gen_ZGstar_mass > 0 && Gen_ZGstar_mass < 4)"
GSTAR_HIGH = "(Gen_ZGstar_mass < 0 || Gen_ZGstar_mass > 4)"

signal_path = "/eos/user/a/amassiro/HIG/ZHggPostProc/Summer20UL18_106x_nAODv9_Full2018v9/MCFull2018v9/"


samples = {}

samples['ZHgg'] = [
    {'tag': 'ZHgg', 'files': flatten(nanoGetLocalSampleFiles(signal_path, "ZHgg")),
     'weight': "genWeight*0.8839*0.08187*0.033658*3", 'isSignal': True},
]

samples['ZHllHgg'] = [
    {'tag': 'ZHllHgg', 'files': flatten(nanoGetLocalSampleFiles(signal_path, "ZHllHgg")),
     'weight': "genWeight*0.7612*0.08187*0.033658*3", 'isSignal': True},
]

samples['ggZHllHgg'] = [
    {'tag': 'ggZHllHgg', 'files': flatten(nanoGetLocalSampleFiles(signal_path, "ggZHllHgg")),
     'weight': "genWeight*0.1227*0.08187*0.033658*3", 'isSignal': True},
]

samples['DY'] = [
    {'tag': 'DY', 'files': flatten(
        nanoGetSampleFiles(mcDirectory, 'DYJetsToLL_M-10to50_NLO') +
        nanoGetSampleFiles(mcDirectory, 'DYJetsToLL_M-50')),
     'weight': mcCommonWeight, 'isSignal': False},
]

samples['ZZ'] = [
    {'tag': 'ZZ', 'files': flatten(
        nanoGetSampleFiles(mcDirectory, 'ZZTo2L2Nu') +
        nanoGetSampleFiles(mcDirectory, 'ZZTo2Q2L_mllmin4p0') +
        nanoGetSampleFiles(mcDirectory, 'ZZTo4L')),
     'weight': mcCommonWeight, 'isSignal': False},
]

samples['VVV'] = [
    {'tag': 'VVV', 'files': flatten(
        nanoGetSampleFiles(mcDirectory, 'ZZZ') +
        nanoGetSampleFiles(mcDirectory, 'WZZ') +
        nanoGetSampleFiles(mcDirectory, 'WWZ') +
        nanoGetSampleFiles(mcDirectory, 'WWW')),
     'weight': mcCommonWeight, 'isSignal': False},
]

samples['Vg'] = [
    {'tag': 'Vg', 'files': flatten(
        nanoGetSampleFiles(mcDirectory, 'Wg_AMCNLOFXFX_01J') +
        nanoGetSampleFiles(mcDirectory, 'ZGToLLG')),
     'weight': "XSWeight*SFweight_val*METFilter_MC*(Gen_ZGstar_mass<=0)", 'isSignal': False},
]

# --------------------------------------------------------------------------------------------------------------------
samples['top'] = [
    {'tag': 'TTTo2L2Nu', 'files': flatten(nanoGetSampleFiles(mcDirectory, 'TTTo2L2Nu')),
     'weight': f"{mcCommonWeight}*{TOP_PTRW}", 'isSignal': False},
    {'tag': 'SingleTop', 'files': flatten(
        nanoGetSampleFiles(mcDirectory, 'ST_s-channel') +
        nanoGetSampleFiles(mcDirectory, 'ST_t-channel_top') +
        nanoGetSampleFiles(mcDirectory, 'ST_t-channel_antitop') +
        nanoGetSampleFiles(mcDirectory, 'ST_tW_antitop') +
        nanoGetSampleFiles(mcDirectory, 'ST_tW_top')),
     'weight': mcCommonWeight, 'isSignal': False},
]

samples['VgS'] = [
    {'tag': 'Wg', 'files': flatten(nanoGetSampleFiles(mcDirectory, 'Wg_AMCNLOFXFX_01J')),
     'weight': f"XSWeight*SFweight_val*METFilter_MC*((Gen_ZGstar_mass>0 && Gen_ZGstar_mass<=0.1))*({GSTAR_LOW}*0.94)",
     'isSignal': False},
    {'tag': 'WZTo3LNu', 'files': flatten(nanoGetSampleFiles(mcDirectory, 'WZTo3LNu_mllmin0p1')),
     'weight': f"XSWeight*SFweight_val*METFilter_MC*((Gen_ZGstar_mass>0.1)*(0.601644*58.59/4.666))*({GSTAR_LOW}*0.94)",
     'isSignal': False},
    {'tag': 'ZGToLLG', 'files': flatten(nanoGetSampleFiles(mcDirectory, 'ZGToLLG')),
     'weight': "XSWeight*SFweight_val*METFilter_MC*(Gen_ZGstar_mass>0)", 'isSignal': False},
]

samples['WZ'] = [
    {'tag': 'WZTo3LNu', 'files': flatten(nanoGetSampleFiles(mcDirectory, 'WZTo3LNu_mllmin0p1')),
     'weight': f"{mcCommonWeight}*({GSTAR_HIGH})*(0.601644*58.59/4.666)", 'isSignal': False},
    {'tag': 'WZTo2Q2L', 'files': flatten(nanoGetSampleFiles(mcDirectory, 'WZTo2Q2L_mllmin4p0')),
     'weight': f"{mcCommonWeight}*({GSTAR_HIGH})", 'isSignal': False},
]

print("Number of samples:", len(samples.keys()))
for sampleName, subentries in samples.items():
    total = sum(len(e['files']) for e in subentries)
    print("Sample:", sampleName, "sub-entries:", len(subentries), "total files:", total)

# print("\nSample details:")
# print(samples)