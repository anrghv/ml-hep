#ifndef HGG_BDT_HELPERS_H
#define HGG_BDT_HELPERS_H

using namespace ROOT::VecOps;

bool bveto(const RVec<float>& CleanJet_pt, const RVec<float>& CleanJet_eta,
           const RVec<int>& CleanJet_jetIdx, const RVec<float>& Jet_btagDeepB){

            for (size_t i = 0; i < CleanJet_pt.size(); i++){
                if (CleanJet_pt[i] <= 20) continue;
                if (std::abs(CleanJet_eta[i]) >= 2.5) continue;
                int jetIdx = CleanJet_jetIdx[i];
                if (Jet_btagDeepB[jetIdx] > 0.4168) return false;
            }
            return true;
        }

bool pass_preselection(float mll, 
                       const RVec<float>& Lepton_pt,
                       const RVec<float>& Lepton_eta,
                       const RVec<int>& Lepton_pdgId,
                       const RVec<float>& CleanJet_pt,
                       const RVec<float>& CleanJet_eta,
                       const RVec<int>& CleanJet_jetIdx,
                       const RVec<float>& Jet_btagDeepB){

    if (Lepton_pt.size() < 2) return false;  
    if (mll <= 12) return false;  // low mass veto
    if (Lepton_pt[0] <= 25 || Lepton_pt[1] <= 10) return false;  // lepton pt cuts
    if (Lepton_pt.size() > 2 && Lepton_pt[2] >= 15) return false;
    if (std::abs(Lepton_pdgId[1]) != 13 && Lepton_pt[1] <= 13) return false;  
    if (std::abs(Lepton_eta[0]) >= 2.5) return false;
    if (std::abs(Lepton_eta[1]) >= 2.5) return false;
    if (std::abs(Lepton_pdgId[0]) != std::abs(Lepton_pdgId[1])) return false;
    if (!bveto(CleanJet_pt, CleanJet_eta, CleanJet_jetIdx, Jet_btagDeepB)) return false;

    return true;
                       }

 
RVec<float> cleanJet_qgl(const RVec<int>& CleanJet_jetIdx, const RVec<float>& Jet_qgl) {
    RVec<float> out(CleanJet_jetIdx.size());
    for (size_t i = 0; i < CleanJet_jetIdx.size(); i++) {
        int idx = CleanJet_jetIdx[i];
        out[i] = (idx >= 0) ? Jet_qgl[idx] : -1.f;
    }
    return out;
}

 
RVec<size_t> lowestQGLIdx(const RVec<float>& qgl) {
    auto mask = qgl >= 0.f;
    auto validIdx = Nonzero(mask);
    auto validVals = qgl[mask];
    auto order = Argsort(validVals);
    return Take(validIdx, order);
}
 
float getJet(const RVec<float>& coll, const RVec<size_t>& idx, size_t pos, float def) {
    if (pos >= idx.size()) return def;
    return coll[idx[pos]];
}
 
struct DijetVars { float mjj, ptjj, detajj, drjj; };
 
DijetVars dijet_qgl_vars(const RVec<float>& pt, const RVec<float>& eta,
                          const RVec<float>& phi, const RVec<float>& mass,
                          const RVec<size_t>& idx) {
    DijetVars v{-9999.f, -9999.f, -9999.f, -9999.f};
    if (idx.size() < 2) return v;
 
    ROOT::Math::PtEtaPhiMVector j1(pt[idx[0]], eta[idx[0]], phi[idx[0]], mass[idx[0]]);
    ROOT::Math::PtEtaPhiMVector j2(pt[idx[1]], eta[idx[1]], phi[idx[1]], mass[idx[1]]);
    auto sum = j1 + j2;
 
    v.mjj = sum.M();
    v.ptjj = sum.Pt();
    v.detajj = std::abs(eta[idx[0]] - eta[idx[1]]);
    v.drjj = ROOT::VecOps::DeltaR(eta[idx[0]], eta[idx[1]], phi[idx[0]], phi[idx[1]]);
    return v;
}
 
#endif
