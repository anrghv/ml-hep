#!/usr/bin/env python

from __future__ import print_function
import os
from ROOT import gROOT, TFile, TChain, TCut, EnableImplicitMT

# import models
# import preselections
# import aliases

# EnableImplicitMT()
isDEV=False

# Load configuration
# why not import it directly?  
with open("configuration.py") as handle:
    exec(handle.read())

samples={}
structure={}
cuts={}



for f in [samplesFile, structureFile, cutsFile]:
    with open(f) as handle:
        exec(handle.read())

aliases = {}
with open("aliases.py") as handle:
    exec(handle.read())
# Reduce sample files for fast dev
if isDEV:
    print("Running in DEV mode, limiting number of files per sample to: ", limitFiles)
    for sampleName, sample in list(samples.items()):
        if sampleName not in ['Hgluglu', 'DY']:
            samples.pop(sampleName)

cut = preselections
# cut = "1"

mvaVariables = [
    # from aliases
    'detajj_qgl',
    'drjj_qgl',
    'mjj_qgl',
    'dphijj_qgl',
    'LowestQGLJet_eta1',
    'LowestQGLJet_eta2',
    'LowestQGLJet_pt1',
    'LowestQGLJet_pt2',
    'ptjj_qgl',
    # 'Alt$(Jet_qgl,CleanJet_jetIdx[0],2)', # qgl of leading jet
    # 'Alt$(Jet_qgl,CleanJet_jetIdx[1],2)', # qgl of subleading jet
    'dphilljetjet_qgl',
    'drjj',
    # 'CleanJet_qgl_valid',

    # branches in tree 
    'detajj',
    'PuppiMET_pt',
    'Lepton_pt[0]',
    'Lepton_pt[1]',
    'ptll',
]