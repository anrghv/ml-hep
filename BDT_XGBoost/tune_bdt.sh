#!/bin/bash

set -e

cd /afs/cern.ch/user/a/araghav/Analyses/Run3/ml-hep/BDT_XGBoost

# source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc13-opt/setup.sh

source /afs/cern.ch/user/a/araghav/Analyses/Run3/mkShapesRDF/start.sh

python3 tuning.py