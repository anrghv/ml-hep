#!/usr/bin/env python

from __future__ import print_function
import os
from ROOT import gROOT, TFile, TChain, TCut, EnableImplicitMT

# import models
# import preselections
# import aliases

EnableImplicitMT()
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

# Reduce sample files for fast dev
if isDEV:
    print("Running in DEV mode, limiting number of files per sample to: ", limitFiles)
    for sampleName, sample in list(samples.items()):
        if sampleName not in ['Hgluglu', 'DY', 'top']:
            samples.pop(sampleName)

cut = "1"


mvaVariables = [
    'mll',
    'lep_pt1',
    'lep_pt2',
    'LowestQGLJet_pt1',
    'LowestQGLJet_pt2',
    'LowestQGLJet_eta1',
    'LowestQGLJet_eta2',
    'mjj_qgl',
    'ptjj_qgl',
    'detajj_qgl',
    'drjj_qgl',
]