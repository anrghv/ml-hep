#!/bin/bash

set -e

cd /afs/cern.ch/user/a/araghav/Analysis/ml-hep/xgb_bdt

# source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc13-opt/setup.sh

source /afs/cern.ch/user/a/araghav/Analysis/latinoRDF/setup.sh

python3 k-xgb.py