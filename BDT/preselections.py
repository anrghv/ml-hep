"""
    NO NEED FOR THIS FILE ANYMORE
"""
# # preselections

# preselections = (
#     'mll>12'
#     ' && Lepton_pt[0]>25'
#     ' && Lepton_pt[1]>10'
#     ' && Alt$(Lepton_pt,2,0) < 15'
#     ' && (abs(Lepton_pdgId[1])==13 || Lepton_pt[1]>13)'
#     ' && abs(Lepton_eta[0])<2.5 && abs(Lepton_eta[1])<2.5'
#     ' && (abs(Lepton_pdgId[0])==abs(Lepton_pdgId[1]))'
#     # ' && bVeto'
# )

preselections = (
    "mll > 12"
    " && Lepton_pt[0] > 25"
    " && Lepton_pt[1] > 10"
    " && Alt$(Lepton_pt[2],0) < 15"
    " && (abs(Lepton_pdgId[1]) == 13 || Lepton_pt[1] > 13)"
    " && abs(Lepton_eta[0]) < 2.5"
    " && abs(Lepton_eta[1]) < 2.5"
    " && (abs(Lepton_pdgId[0]) == abs(Lepton_pdgId[1]))"
    # "&& bVeto"
    # " && Sum$(CleanJet_pt > 20. && abs(CleanJet_eta) < 2.5 && Take(Jet_btagDeepB, CleanJet_jetIdx) > 0.4168) == 0"
    # " && Sum$(CleanJet_pt > 20. && abs(CleanJet_eta) < 2.5 && (Jet_btagDeepB[CleanJet_jetIdx] > 0.4168)) == 0"
    # " && (abs(CleanJet_eta) < 2.5 ) == 0"
)

# bVeto_cut =  "Sum(CleanJet_pt > 20. && abs(CleanJet_eta) < 2.5 && Take(Jet_btagDeepB, CleanJet_jetIdx) > 0.4168) == 0"
# ======================================================================================================================================
# preselections = {}

# preselections['ALL']  = "WH3l_flagOSSF == 0 || WH3l_flagOSSF == 1"

# preselections['SSSF'] = 'WH3l_flagOSSF == 0 \
#                       && Alt$( CleanJet_pt[0], 0) < 30 \
#                       && MinIf$( WH3l_mOSll[], WH3l_mOSll[Iteration$] > 0) > 12 \
#                       && Alt$(Lepton_pt[0],0)>10 \
#                       && Alt$(Lepton_pt[1],0)>10 \
#                       && Alt$(Lepton_pt[2],0)>10 \
#                       && (nLepton>=3 && Alt$(Lepton_pt[3],0)<10) \
#                       && abs(WH3l_chlll) == 1 \
# '

# preselections['OSSF']  = 'WH3l_flagOSSF == 1 \
#                        && WH3l_ZVeto > 20 \
#                        && Alt$( CleanJet_pt[0], 0) < 30 \
#                        && PuppiMET_pt > 50 \
#                        && MinIf$( WH3l_mOSll[], WH3l_mOSll[Iteration$] > 0) > 12 \
#                        && Alt$(Lepton_pt[0],0)>10 \
#                        && Alt$(Lepton_pt[1],0)>10 \
#                        && Alt$(Lepton_pt[2],0)>10 \
#                        && (nLepton>=3 && Alt$(Lepton_pt[3],0)<10) \
#                        && abs(WH3l_chlll) == 1 \
# '