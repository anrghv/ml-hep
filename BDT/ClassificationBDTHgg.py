#!/usr/bin/env python
from ROOT import TMVA, TFile, TTree, TCut, TChain
from subprocess import call
from os.path import isfile
from datetime import datetime
from zoneinfo import ZoneInfo
import os

import configHgg_cfg  as config

# Setup TMVA
def runJob():
    # For setup the TMVA environment.
    TMVA.Tools.Instance()

    # output = TFile.Open('lxplus/TMVA_Hgg.root', 'RECREATE') # Output root file if running on lxplus
    # output = TFile.Open('TMVA_Hgg.root', 'RECREATE') # Output root file if running on condor
    # output = TFile.Open('/eos/user/a/araghav/from_BDT/TMVA_Hgg.root', 'RECREATE') # Output root file if running on condors
    output = TFile.Open('/eos/user/a/araghav/condor_from_BDT/TMVA_Hgg_splitmode_random.root', 'RECREATE') # Output root file if running on condors
    # -----------------------------------------------------------------------------------------------------------------
    # -----------------------Understand this line ---------------------------------------------------------------------
    factory = TMVA.Factory('TMVAClassification', output,'!V:!Silent:Color:DrawProgressBar:AnalysisType=Classification')
    # -----------------------------------------------------------------------------------------------------------------

    
    def alias_applies(sampleName, alias):
        if 'samples' not in alias:
            return True
        scope = alias['samples']
        # print("Checking if alias applies to sample: ", sampleName, " with scope: ", scope)
        if isinstance(scope, str):
            return sampleName == scope
        return sampleName in scope

    dataloader = TMVA.DataLoader('datasetHgg') # Create a new dataloader. It will contain the training and test data.
    for br in config.mvaVariables:
        dataloader.AddVariable(br)

    for sampleName, sample in config.samples.items():
        print("Processing sample: ", sampleName)
        if config.structure[sampleName]['isData']==1: #skips data from the training
            print("Skipping sample: ", sampleName, " because it is data")
            continue

        sample['tree'] = TChain("Events")
        print(sampleName)
        for tag, filelist, *rest in sample['name']:    
            for f in filelist:
                sample['tree'].Add(f)

        # tree = TChain("Events")
        # for entry in sample:
        #     for f in entry['files']:
        #         tree.Add(f)

        for aliasName, alias in config.aliases.items():
            if alias_applies(sampleName, alias):
                # print("Adding alias: ", aliasName, " to sample: ", sampleName)
                sample['tree'].SetAlias(aliasName, alias['expr'])
                # tree.SetAlias(aliasName, alias['expr'])
                
        if config.structure[sampleName]['isSignal']==1:
            dataloader.AddSignalTree(sample['tree'], 1.0)
            # dataloader.AddSignalTree(tree, 1.0)
        else:
            dataloader.AddBackgroundTree(sample['tree'], 1.0)
            # dataloader.AddBackgroundTree(tree, 1.0)

    print("Finished loading all samples")
    print("Preparing train/test trees...")  
    # dataloader.SetSignalWeightExpression("eventWeight")
    # dataloader.SetBackgroundWeightExpression("eventWeight")
    dataloader.PrepareTrainingAndTestTree(TCut(config.cut),'SplitMode=Random:NormMode=NumEvents:!V')
    # dataloader.PrepareTrainingAndTestTree(TCut(config.cut),'nTrain_Signal=8_000:nTrain_Background=10_000:nTest_Signal=5_000:nTest_Background=5_000:SplitMode=Random:NormMode=NumEvents:!V')
    print("Finished PrepareTrainingAndTestTree")
    # dataloader.PrepareTrainingAndTestTree(TCut(config.cut),'nTrain_Signal=100000:nTrain_Background=100000:SplitMode=Random:NormMode=NumEvents:!V')#SSSF
    print("Starting BookMethod")
    # factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTG4",   "!H:!V:NTrees=500:MinNodeSize=1.5%:BoostType=Grad:Shrinkage=0.05:UseBaggedBoost:GradBaggingFraction=0.5:nCuts=50:MaxDepth=2" );
    factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTG4",   "!H:!V:NTrees=500:MinNodeSize=1.5%:BoostType=Grad:Shrinkage=0.05:UseBaggedBoost:GradBaggingFraction=0.5:nCuts=50:MaxDepth=2" );
    factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTG4D3",   "!H:!V:NTrees=500:MinNodeSize=1.5%:BoostType=Grad:Shrinkage=0.05:UseBaggedBoost:GradBaggingFraction=0.5:nCuts=500:MaxDepth=3" );
    factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTG4D4",   "!H:!V:NTrees=500:MinNodeSize=1.5%:BoostType=Grad:Shrinkage=0.05:UseBaggedBoost:GradBaggingFraction=0.5:nCuts=500:MaxDepth=4" );
    factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTG4D5",   "!H:!V:NTrees=500:MinNodeSize=1.5%:BoostType=Grad:Shrinkage=0.05:UseBaggedBoost:GradBaggingFraction=0.5:nCuts=500:MaxDepth=5" );
    # factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTG4D6",   "!H:!V:NTrees=500:MinNodeSize=1.5%:BoostType=Grad:Shrinkage=0.05:UseBaggedBoost:GradBaggingFraction=0.5:nCuts=500:MaxDepth=6" );
    factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTG4C3", "!H:!V:NTrees=500:MinNodeSize=1.5%:BoostType=Grad:Shrinkage=0.05:UseBaggedBoost:GradBaggingFraction=0.5:nCuts=500:MaxDepth=2" );
    factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTG4SK01",   "!H:!V:NTrees=500:MinNodeSize=1.5%:BoostType=Grad:Shrinkage=0.01:UseBaggedBoost:GradBaggingFraction=0.5:nCuts=500:MaxDepth=2" );
    factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTG4F07"    ,   "!H:!V:NTrees=500:MinNodeSize=1.5%:BoostType=Grad:Shrinkage=0.05:UseBaggedBoost:GradBaggingFraction=0.7:nCuts=500:MaxDepth=2" );
    # factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTG4SK01F07",   "!H:!V:NTrees=500:MinNodeSize=1.5%:BoostType=Grad:Shrinkage=0.01:UseBaggedBoost:GradBaggingFraction=0.7:nCuts=500:MaxDepth=2" );
    print("Finished BookMethod")

    # Run training, test and evaluation
    
    print("Starting training...")
    print(datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d-%m-%Y %H:%M:%S IST"))
    factory.TrainAllMethods()
    factory.TestAllMethods()
    factory.EvaluateAllMethods()

    output.Close()

from ROOT import gInterpreter
gInterpreter.Declare('using namespace ROOT::VecOps;')

if __name__ == "__main__":
    print("\nCode is running on: ", os.uname()[1])
    # this will confirm if the aliases are loaded. will print a yes if the aliases are loaded correctly. If not, it will print a no.
    if hasattr(config, 'aliases'):
        print("Aliases are loaded: Yes")
    else:
        print("Aliases are loaded: No")
    print("samples loaded: ", list(config.samples.keys()))

    runJob()
