#ifndef HGG_BDT_HEADERS_H
#define HGG_BDT_HEADERS_H

// #include <TMVA/RBDT.hxx>
// #include <vector>

// // 1-Fold evaluation (Single model)
// inline float eval_xgboost(
//     float detajj_qgl, float drjj_qgl, float mjj_qgl, float dphijj_qgl,
//     float LowestQGLJet_eta1, float LowestQGLJet_eta2, float LowestQGLJet_pt1, float LowestQGLJet_pt2,
//     float ptjj_qgl, float dphilljetjet_qgl, float drjj, float detajj,
//     float PuppiMET_pt, float lep_pt0, float lep_pt1, float ptll
// ) {
//     // static ensures the ROOT model file is read from EOS/AFS only ONCE
//     static TMVA::Experimental::RBDT bdt(
//         "bdt_model", 
//         "/eos/user/a/araghav/xgb_outputs/xgb_model.root"
//     );

//     // Feature ordering MUST match mvaVariables from training exactly
//     std::vector<float> inputs = {
//         detajj_qgl, drjj_qgl, mjj_qgl, dphijj_qgl,
//         LowestQGLJet_eta1, LowestQGLJet_eta2, LowestQGLJet_pt1, LowestQGLJet_pt2,
//         ptjj_qgl, dphilljetjet_qgl, drjj, detajj,
//         PuppiMET_pt, lep_pt0, lep_pt1, ptll
//     };

//     return bdt.Compute(inputs)[0];
// }


using namespace ROOT::VecOps;

template<typename container>
float Alt(container c, int index, float alt) {
    if (index < (int)c.size()) {
        return c[index];
    } else {
        return alt;
    }
}

RVec<double> LogVec(const RVec<double>& vec) {
    RVec<double> out;
    for (auto const& el : vec) {
        out.push_back(TMath::Log(el));
    }
    return out;
}

#endif