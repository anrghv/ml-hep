#!/usr/bin/env python
from ROOT import TMVA, TFile, TTree, TCut, TChain
from subprocess import call
from os.path import isfile

import configHgg_cfg  as config

# Setup TMVA
def runJob():
    # For setup the TMVA environment.
    TMVA.Tools.Instance()
    # Needed for TMVA to communicate with python
    # TMVA.PyMethodBase.PyInitialize()

    output = TFile.Open('TMVA_Hgg.root', 'RECREATE') # Output root file
    # -----------------------------------------------------------------------------------------------------------------
    # -----------------------Understand this line ---------------------------------------------------------------------
    factory = TMVA.Factory('TMVAClassification', output,'!V:!Silent:Color:DrawProgressBar:AnalysisType=Classification')
    # factory = TMVA.Factory('TMVAClassification', output,'!V:!Silent:Color:DrawProgressBar:Transformations=D,G:AnalysisType=Classification')
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
        for aliasName, alias in config.aliases.items():
            if alias_applies(sampleName, alias):
                sample['tree'].SetAlias(aliasName, alias['expr'])
                # print("Setting alias: ", aliasName, " for sample: ", sampleName, " with expression: ", alias['expr'])
                
        if config.structure[sampleName]['isSignal']==1:
            dataloader.AddSignalTree(sample['tree'], 1.0)
        else:
            dataloader.AddBackgroundTree(sample['tree'], 1.0)
        # output_dim += 1

    print("Finished loading all samples")
    print("Preparing train/test trees...")  
    # dataloader.PrepareTrainingAndTestTree(TCut(config.cut),'SplitMode=Random:NormMode=NumEvents:!V')
    dataloader.PrepareTrainingAndTestTree(TCut(config.cut),'nTrain_Signal=10_000:nTrain_Background=10_000:nTest_Signal=5_000:nTest_Background=5_000:SplitMode=Random:NormMode=NumEvents:!V')
    print("Finished PrepareTrainingAndTestTree")
    # dataloader.PrepareTrainingAndTestTree(TCut(config.cut),'nTrain_Signal=100000:nTrain_Background=100000:SplitMode=Random:NormMode=NumEvents:!V')#SSSF
    print("Starting BookMethod")
    factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTG4",   "!H:!V:NTrees=500:MinNodeSize=1.5%:BoostType=Grad:Shrinkage=0.05:UseBaggedBoost:GradBaggingFraction=0.5:nCuts=50:MaxDepth=2" );
    # factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTG4",   "!H:!V:NTrees=500:MinNodeSize=1.5%:BoostType=Grad:Shrinkage=0.05:UseBaggedBoost:GradBaggingFraction=0.5:nCuts=500:MaxDepth=2" );
    # factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTG4D3",   "!H:!V:NTrees=500:MinNodeSize=1.5%:BoostType=Grad:Shrinkage=0.05:UseBaggedBoost:GradBaggingFraction=0.5:nCuts=500:MaxDepth=3" );
    # factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTG4D4",   "!H:!V:NTrees=500:MinNodeSize=1.5%:BoostType=Grad:Shrinkage=0.05:UseBaggedBoost:GradBaggingFraction=0.5:nCuts=500:MaxDepth=4" );
    # factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTG4D5",   "!H:!V:NTrees=500:MinNodeSize=1.5%:BoostType=Grad:Shrinkage=0.05:UseBaggedBoost:GradBaggingFraction=0.5:nCuts=500:MaxDepth=5" );
    # factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTG4D6",   "!H:!V:NTrees=500:MinNodeSize=1.5%:BoostType=Grad:Shrinkage=0.05:UseBaggedBoost:GradBaggingFraction=0.5:nCuts=500:MaxDepth=6" );
    # factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTG4C3", "!H:!V:NTrees=500:MinNodeSize=1.5%:BoostType=Grad:Shrinkage=0.05:UseBaggedBoost:GradBaggingFraction=0.5:nCuts=300:MaxDepth=2" );
    # factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTG4SK01",   "!H:!V:NTrees=500:MinNodeSize=1.5%:BoostType=Grad:Shrinkage=0.01:UseBaggedBoost:GradBaggingFraction=0.5:nCuts=500:MaxDepth=2" );
    # factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTG4F07"    ,   "!H:!V:NTrees=500:MinNodeSize=1.5%:BoostType=Grad:Shrinkage=0.05:UseBaggedBoost:GradBaggingFraction=0.7:nCuts=500:MaxDepth=2" );
    # factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTG4SK01F07",   "!H:!V:NTrees=500:MinNodeSize=1.5%:BoostType=Grad:Shrinkage=0.01:UseBaggedBoost:GradBaggingFraction=0.7:nCuts=500:MaxDepth=2" );
    print("Finished BookMethod")

    # Run training, test and evaluation
    
    print("Starting training...")
    factory.TrainAllMethods()
    factory.TestAllMethods()
    factory.EvaluateAllMethods()

    output.Close()

from ROOT import gInterpreter
gInterpreter.Declare('using namespace ROOT::VecOps;')


if __name__ == "__main__":
    runJob()