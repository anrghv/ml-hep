#ifndef HGG_BDT_HELPERS_H
#define HGG_BDT_HELPERS_H

using namespace ROOT::VecOps;


template<typename T>
T Alt(const RVec<T>& v, size_t i, T def) {
    return i < v.size() ? v[i] : def;
}

RVec<double> LogVec(const RVec<double>& vec){
    RVec<double> out;
    out.reserve(vec.size());
    for (auto const& el : vec) out.push_back(TMath::Log(el));
    return out;
}

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
 
struct DijetVars { float mjj, ptjj, detajj, dphijj, drjj; };
 
DijetVars dijet_qgl_vars(const RVec<float>& pt, const RVec<float>& eta,
                          const RVec<float>& phi, const RVec<float>& mass,
                          const RVec<size_t>& idx) {
    DijetVars v{-9999.f, -9999.f, -9999.f, -9999.f, -9999.f};
    if (idx.size() < 2) return v;
 
    ROOT::Math::PtEtaPhiMVector j1(pt[idx[0]], eta[idx[0]], phi[idx[0]], mass[idx[0]]);
    ROOT::Math::PtEtaPhiMVector j2(pt[idx[1]], eta[idx[1]], phi[idx[1]], mass[idx[1]]);
    auto sum = j1 + j2;
 
    v.mjj = sum.M();
    v.ptjj = sum.Pt();
    v.detajj = std::abs(eta[idx[0]] - eta[idx[1]]);
    v.dphijj = ROOT::VecOps::DeltaPhi(phi[idx[0]], phi[idx[1]]);
    v.drjj = ROOT::VecOps::DeltaR(eta[idx[0]], eta[idx[1]], phi[idx[0]], phi[idx[1]]);
    return v;
}


bool breq(const RVec<float>& CleanJet_pt, const RVec<float>& CleanJet_eta,
          const RVec<int>& CleanJet_jetIdx, const RVec<float>& Jet_btagDeepB) {
    for (size_t i = 0; i < CleanJet_pt.size(); i++) {
        if (CleanJet_pt[i] <= 30) continue;
        if (std::abs(CleanJet_eta[i]) >= 2.5) continue;
        int jetIdx = CleanJet_jetIdx[i];
        if (Jet_btagDeepB[jetIdx] > 0.4168) return true;
    }
    return false;
}
 
double bVetoSF(const RVec<float>& CleanJet_pt, const RVec<float>& CleanJet_eta,
               const RVec<int>& CleanJet_jetIdx, const RVec<float>& Jet_btagSF_deepcsv_shape) {
    double sum = 0.;
    for (size_t i = 0; i < CleanJet_pt.size(); i++) {
        bool inRange = CleanJet_pt[i] > 20 && std::abs(CleanJet_eta[i]) < 2.5;
        sum += inRange ? TMath::Log(Jet_btagSF_deepcsv_shape[CleanJet_jetIdx[i]]) : TMath::Log(1.0);
    }
    return TMath::Exp(sum);
}
 
double bReqSF(const RVec<float>& CleanJet_pt, const RVec<float>& CleanJet_eta,
              const RVec<int>& CleanJet_jetIdx, const RVec<float>& Jet_btagSF_deepcsv_shape) {
    double sum = 0.;
    for (size_t i = 0; i < CleanJet_pt.size(); i++) {
        bool inRange = CleanJet_pt[i] > 30 && std::abs(CleanJet_eta[i]) < 2.5;
        sum += inRange ? TMath::Log(Jet_btagSF_deepcsv_shape[CleanJet_jetIdx[i]]) : TMath::Log(1.0);
    }
    return TMath::Exp(sum);
}
 
bool topcr(float mtw2, float mll, bool zeroJet, bool bVetoFlag, bool bReqFlag) {
    return mtw2 > 30 && mll > 50 && ((zeroJet && !bVetoFlag) || bReqFlag);
}
 
double btagSF(bool bVetoFlag, bool topcrFlag, bool zeroJetFlag,
              double bVetoSFval, double bReqSFval) {
    return (bVetoFlag || (topcrFlag && zeroJetFlag)) * bVetoSFval
         + (topcrFlag && !zeroJetFlag) * bReqSFval;
}
 
double jet_PUIDSF(const RVec<int>& Jet_jetId, const RVec<float>& Jet_PUIDSF_loose) {
    double sum = 0.;
    for (size_t i = 0; i < Jet_jetId.size(); i++) {
        if (Jet_jetId[i] >= 2) sum += TMath::Log(Jet_PUIDSF_loose[i]);
    }
    return TMath::Exp(sum);
}
 
double lepWPCut(const RVec<int>& Lepton_pdgId, const RVec<int>& Lepton_muonIdx,
                 const RVec<float>& Muon_mvaTTH, const RVec<float>& Lepton_mvaTTH_UL,
                 float LepCut2l_branch) {
    bool ele0 = std::abs(Lepton_pdgId[0])==11 && Lepton_mvaTTH_UL[0] > 0.90;
    bool mu0  = std::abs(Lepton_pdgId[0])==13 && Muon_mvaTTH[Lepton_muonIdx[0]] > 0.82;
    bool ele1 = std::abs(Lepton_pdgId[1])==11 && Lepton_mvaTTH_UL[1] > 0.90;
    bool mu1  = std::abs(Lepton_pdgId[1])==13 && Muon_mvaTTH[Lepton_muonIdx[1]] > 0.82;
    return LepCut2l_branch * ((ele0||mu0) && (ele1||mu1));
}
 
double promptGenLepMatch2l(const RVec<int>& Lepton_promptgenmatched) {
    return Alt<int>(Lepton_promptgenmatched, 0, 0) * Alt<int>(Lepton_promptgenmatched, 1, 0);
}

bool qglCut(const RVec<float>& CleanJet_qgl_valid) {
    if (CleanJet_qgl_valid.size() < 2) return false;
    auto sorted = Sort(CleanJet_qgl_valid);
    return sorted[0] < 0.5f && sorted[1] < 0.5f;
}

ROOT::Math::PtEtaPhiMVector leptonP4(const RVec<float>& Lepton_pt, const RVec<float>& Lepton_eta,
                                      const RVec<float>& Lepton_phi, size_t pos) {
    if (pos >= Lepton_pt.size()) return ROOT::Math::PtEtaPhiMVector(0., 0., 0., 0.);
    return ROOT::Math::PtEtaPhiMVector(Lepton_pt[pos], Lepton_eta[pos], Lepton_phi[pos], 0.0);
}

ROOT::Math::PtEtaPhiMVector jetP4(const RVec<float>& pt, const RVec<float>& eta,
                                   const RVec<float>& phi, const RVec<float>& mass,
                                   const RVec<size_t>& idx, size_t pos) {
    if (pos >= idx.size()) return ROOT::Math::PtEtaPhiMVector(0., 0., 0., 0.);
    size_t i = idx[pos];
    return ROOT::Math::PtEtaPhiMVector(pt[i], eta[i], phi[i], mass[i]);
}

double drjjPlain(const RVec<float>& CleanJet_eta, const RVec<float>& CleanJet_phi) {
    if (CleanJet_eta.size() < 2) return -9999.0;
    return ROOT::VecOps::DeltaR(CleanJet_eta[0], CleanJet_eta[1], CleanJet_phi[0], CleanJet_phi[1]);
}

double dphiLLJetQGL(const ROOT::Math::PtEtaPhiMVector& lep1, const ROOT::Math::PtEtaPhiMVector& lep2,
                     float jetPhi1, size_t nQGLJets) {
    if (nQGLJets < 1) return -9999.0;
    return std::abs((double)ROOT::VecOps::DeltaPhi((float)(lep1 + lep2).Phi(), jetPhi1));
}

double dphiLLJetJetQGL(const ROOT::Math::PtEtaPhiMVector& lep1, const ROOT::Math::PtEtaPhiMVector& lep2,
                        const ROOT::Math::PtEtaPhiMVector& jet1, const ROOT::Math::PtEtaPhiMVector& jet2,
                        size_t nQGLJets) {
    if (nQGLJets < 2) return -9999.0;
    return std::abs((double)ROOT::VecOps::DeltaPhi((float)(lep1 + lep2).Phi(), (float)(jet1 + jet2).Phi()));
}

float btagAtLowestQGL(const RVec<float>& Jet_btag, const RVec<int>& CleanJet_jetIdx,
                       const RVec<size_t>& idx, size_t pos, float def) {
    if (pos >= idx.size()) return def;
    int jetIdx = CleanJet_jetIdx[idx[pos]];
    return Alt<float>(Jet_btag, (size_t)jetIdx, def);
}

bool isZeroJet(const RVec<float>& CleanJet_pt) {
    return Alt<float>(CleanJet_pt, 0, 0.f) < 30.f;
}
bool isOneJet(const RVec<float>& CleanJet_pt) {
    return Alt<float>(CleanJet_pt, 0, 0.f) > 30.f && Alt<float>(CleanJet_pt, 1, 0.f) < 30.f;
}
bool isMultiJet(const RVec<float>& CleanJet_pt) {
    return Alt<float>(CleanJet_pt, 1, 0.f) > 30.f;
}

bool holeVeto(const RVec<float>& Lepton_eta, const RVec<float>& Lepton_phi, const RVec<int>& Lepton_pdgId,
              const RVec<float>& CleanJet_eta, const RVec<float>& CleanJet_phi) {
    bool lep0 = Lepton_eta.size() > 0 && Lepton_eta[0] < -1.3 && Lepton_eta[0] > -2.5
                && Lepton_phi[0] > -1.57 && Lepton_phi[0] < -0.87 && std::abs(Lepton_pdgId[0]) == 11;
    bool lep1 = Lepton_eta.size() > 1 && Lepton_eta[1] < -1.3 && Lepton_eta[1] > -2.5
                && Lepton_phi[1] > -1.57 && Lepton_phi[1] < -0.87 && std::abs(Lepton_pdgId[1]) == 11;

    bool jet0 = Alt<float>(CleanJet_eta, 0, 99.f) < -1.3 && Alt<float>(CleanJet_eta, 0, -99.f) > -2.5
                && Alt<float>(CleanJet_phi, 0, -99.f) > -1.57 && Alt<float>(CleanJet_phi, 0, 99.f) < -0.87;
    bool jet1 = Alt<float>(CleanJet_eta, 1, 99.f) < -1.3 && Alt<float>(CleanJet_eta, 1, -99.f) > -2.5
                && Alt<float>(CleanJet_phi, 1, -99.f) > -1.57 && Alt<float>(CleanJet_phi, 1, 99.f) < -0.87;

    return lep0 || lep1 || jet0 || jet1;
}

#endif