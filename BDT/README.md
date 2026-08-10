# Configuration for Hgg BDT training

<!-- Configurations to train the BDTs used in the Hgg analysis. We prepare two separate trainings, for two final states:
- same-sign same flavor (SSSF)
- opposite-sign same flavor (OSSF) -->

The signal samples are:
- Hgluglu
- qqZHgluglu
- ggZHgluglu

And as backgrounds:
- Dy
- top
- Vg
- VgS
- ZZ
- WZ
- VVV

The instructions to run the trainings follow.


### Train BDTs



    python ClassificationBDTHgg.py

<!-- OS-SF: -->
<!--  -->
    <!-- python ClassificationBDTOSSF.py -->


### Plot training results

SS-SF:

     root -l -b -q 'plotAll.C("./","TMVA_SSSF","plots_BDT_SSSF","datasetSSSF")'

OS-SF:

     root -l -b -q 'plotAll.C("./","TMVA_OSSF","plots_BDT_OSSF","datasetOSSF")'
