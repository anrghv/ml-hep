import ROOT
import os
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

ROOT.gErrorIgnoreLevel = ROOT.kFatal
ROOT.ROOT.EnableImplicitMT()

treeName = "Events"
Output_dir = "/eos/user/a/araghav/BDT_Trees_training/"

BASE_COLUMNS = [
    "mll", "lep_pt1", "lep_pt2",
    "LowestQGLJet_pt1", "LowestQGLJet_pt2", "LowestQGLJet_pt3",
    "LowestQGLJet_eta1", "LowestQGLJet_eta2",
    "LowestQGLJet_phi1", "LowestQGLJet_phi2",
    "LowestQGLJet_mass1", "LowestQGLJet_mass2",
    "mjj_qgl", "ptjj_qgl", "detajj_qgl", "drjj_qgl",
    "eventWeight",
]

RAW_PASSTHROUGH_COLUMNS = [
    "nJet", "Jet_area", 
    # "Jet_btagCSVV2", "Jet_btagDeepB", "Jet_btagDeepCvB",
    # "Jet_btagDeepCvL", "Jet_btagDeepFlavB", "Jet_btagDeepFlavCvB", "Jet_btagDeepFlavCvL",
    # "Jet_btagDeepFlavQG", "Jet_chEmEF", "Jet_chFPV0EF", "Jet_chHEF",
    # "Jet_hfsigmaEtaEta", "Jet_hfsigmaPhiPhi", 
    "Jet_mass",
     "Jet_eta",
    #  "Jet_muEF", "Jet_muonSubtrFactor",
    "Jet_neEmEF", "Jet_neHEF", "Jet_phi", "Jet_pt", "Jet_puIdDisc", "Jet_qgl",
    # "Jet_rawFactor", "Jet_bRegCorr", "Jet_bRegRes", "Jet_cRegCorr", "Jet_cRegRes",
    "Jet_electronIdx1", "Jet_electronIdx2", "Jet_hfadjacentEtaStripsSize",
    "Jet_hfcentralEtaStripSize", "Jet_jetId", "Jet_muonIdx1", "Jet_muonIdx2",
    "Jet_nElectrons", "Jet_nMuons", "Jet_puId", "Jet_nConstituents",

    # "PuppiMET_phi", "PuppiMET_phiJERDown", "PuppiMET_phiJERUp", "PuppiMET_phiJESDown",
    # "PuppiMET_phiJESUp", "PuppiMET_phiUnclusteredDown", "PuppiMET_phiUnclusteredUp",
    "PuppiMET_pt",
    #   "PuppiMET_ptJERDown", "PuppiMET_ptJERUp", "PuppiMET_ptJESDown",
    # "PuppiMET_ptJESUp", "PuppiMET_ptUnclusteredDown", "PuppiMET_ptUnclusteredUp",
    # "PuppiMET_sumEt",

    "nLepton", "Lepton_pdgId", "Lepton_electronIdx", "Lepton_muonIdx",
    "Lepton_pt", "Lepton_eta", "Lepton_phi",
    # "nVetoLepton", "VetoLepton_pdgId", "VetoLepton_electronIdx", "VetoLepton_muonIdx",
    # "VetoLepton_pt", "VetoLepton_eta", "VetoLepton_phi",
    "Lepton_isLoose", 
    # "Lepton_isVeto", "dmZll_veto",

    "nCleanJet", "CleanJet_jetIdx", "CleanJet_pt", "CleanJet_eta", "CleanJet_phi",
    # "CleanJet_mass", "CleanJet_corr_JER", "CleanJet_cleanJetIdx_preJER",
    # "CleanJet_pt_JER0Up", "CleanJet_mass_JER0Up", "CleanJet_pt_JER1Up", "CleanJet_mass_JER1Up",
    # "CleanJet_pt_JER2Up", "CleanJet_mass_JER2Up", "CleanJet_pt_JER3Up", "CleanJet_mass_JER3Up",
    # "CleanJet_pt_JER4Up", "CleanJet_mass_JER4Up", "CleanJet_pt_JER5Up", "CleanJet_mass_JER5Up",
    # "CleanJet_pt_JER0Down", "CleanJet_mass_JER0Down", "CleanJet_pt_JER1Down", "CleanJet_mass_JER1Down",
    # "CleanJet_pt_JER2Down", "CleanJet_mass_JER2Down", "CleanJet_pt_JER3Down", "CleanJet_mass_JER3Down",
    # "CleanJet_pt_JER4Down", "CleanJet_mass_JER4Down", "CleanJet_pt_JER5Down", "CleanJet_mass_JER5Down",

    "dphill", "yll", "ptll", "pt1", "pt2", "mth", "mcoll", 
    # "mcollWW", 
    "mTi", "mTe", "choiMass", "mR", "mT2", "channel", "drll",
    "dphilljet", "dphilljetjet", "dphilljetjet_cut",
    "dphillmet", "dphilmet", "dphilmet1", "dphilmet2",
    "mtw1", "mtw2", "mjj", "detajj", "njet",
    # "mllWgSt", "drllWgSt", "mllThird", "mllOneThree", "mllTwoThree",
    "drllOneThree", "drllTwoThree",
    "dphijet1met", "dphijet2met", "dphijjmet", "dphijjmet_cut",
    "dphilep1jet1", "dphilep1jet2", "dphilep2jet1", "dphilep2jet2",
    "mindetajl", "detall", "dphijj", "maxdphilepjj", "dphilep1jj", "dphilep2jj",
]

NEW_ALIAS_COLUMNS = [
    "qgl_j1_lowestqgl", "QGLcut",
    "dphijj_qgl", "drjj",
    "dphilljet_qgl", "dphilljetjet_qgl",
    "btagDeepBj1_lowestqgl", "btagDeepBj2_lowestqgl",
    "btagCSVV2j1_lowestqgl", "btagCSVV2j2_lowestqgl",
    "oneJet", "multiJet",
    "hole_veto",
]

SF_CHAIN_COLUMNS = [
    "zeroJet", "bVeto", "bReq",
    "bVetoSF_val", "bReqSF_val", "topcr_flag", "btagSF_val",
    "Jet_PUIDSF_val", "LepWPCut_val", "PromptGenLepMatch2l_val", "SFweight_val",
]

OUTPUT_COLUMNS = BASE_COLUMNS + RAW_PASSTHROUGH_COLUMNS + NEW_ALIAS_COLUMNS + SF_CHAIN_COLUMNS


_helpers_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers.h")
ROOT.gInterpreter.Declare(f'#include "{_helpers_path}"')

_LEP_CUT_BRANCH = "LepCut2l__ele_mvaFall17V2Iso_WP90__mu_cut_Tight_HWWW"
_LEP_SF_BRANCH = "LepSF2l__ele_mvaFall17V2Iso_WP90__mu_cut_Tight_HWWW"

_SF_CHAIN_INPUT_BRANCHES = [
    "Jet_btagSF_deepcsv_shape", "Jet_PUIDSF_loose", "SFweight2l",
    _LEP_CUT_BRANCH, _LEP_SF_BRANCH, "Lepton_promptgenmatched",
]


def build_dataframe(files, weight_expr):
    df = ROOT.RDataFrame(treeName, files)
    available = set(str(c) for c in df.GetColumnNames())
    has_sf_chain = all(b in available for b in _SF_CHAIN_INPUT_BRANCHES)

    df = (
        df
        .Filter(
            "pass_preselection(mll, Lepton_pt, Lepton_eta, Lepton_pdgId, "
            "CleanJet_pt, CleanJet_eta, CleanJet_jetIdx, Jet_btagDeepB)",
            "preselection",
        )
        .Define("lep_pt1", "Lepton_pt[0]")
        .Define("lep_pt2", "Lepton_pt[1]")
        .Define("CleanJet_qgl", "cleanJet_qgl(CleanJet_jetIdx, Jet_qgl)")
        .Define("qglOrder", "lowestQGLIdx(CleanJet_qgl)")
        .Define("LowestQGLJet_pt1", "getJet(CleanJet_pt, qglOrder, 0, 0.f)")
        .Define("LowestQGLJet_pt2", "getJet(CleanJet_pt, qglOrder, 1, 0.f)")
        .Define("LowestQGLJet_pt3", "getJet(CleanJet_pt, qglOrder, 2, 0.f)")
        .Define("LowestQGLJet_eta1", "getJet(CleanJet_eta, qglOrder, 0, 99.f)")
        .Define("LowestQGLJet_eta2", "getJet(CleanJet_eta, qglOrder, 1, 99.f)")
        .Define("LowestQGLJet_phi1", "getJet(CleanJet_phi, qglOrder, 0, 99.f)")
        .Define("LowestQGLJet_phi2", "getJet(CleanJet_phi, qglOrder, 1, 99.f)")
        .Define("LowestQGLJet_mass1", "getJet(CleanJet_mass, qglOrder, 0, 0.f)")
        .Define("LowestQGLJet_mass2", "getJet(CleanJet_mass, qglOrder, 1, 0.f)")
        .Define("dijetVars", "dijet_qgl_vars(CleanJet_pt, CleanJet_eta, "
                              "CleanJet_phi, CleanJet_mass, qglOrder)")
        .Define("mjj_qgl", "dijetVars.mjj")
        .Define("ptjj_qgl", "dijetVars.ptjj")
        .Define("detajj_qgl", "dijetVars.detajj")
        .Define("drjj_qgl", "dijetVars.drjj")

        .Define("zeroJet", "isZeroJet(CleanJet_pt)")
        .Define("bVeto", "bveto(CleanJet_pt, CleanJet_eta, CleanJet_jetIdx, Jet_btagDeepB)")
        .Define("bReq", "breq(CleanJet_pt, CleanJet_eta, CleanJet_jetIdx, Jet_btagDeepB)")
    )

    if has_sf_chain:
        df = (
            df
            .Define("bVetoSF_val", "bVetoSF(CleanJet_pt, CleanJet_eta, CleanJet_jetIdx, Jet_btagSF_deepcsv_shape)")
            .Define("bReqSF_val", "bReqSF(CleanJet_pt, CleanJet_eta, CleanJet_jetIdx, Jet_btagSF_deepcsv_shape)")
            .Define("topcr_flag", "topcr(mtw2, mll, zeroJet, bVeto, bReq)")
            .Define("btagSF_val", "btagSF(bVeto, topcr_flag, zeroJet, bVetoSF_val, bReqSF_val)")
            .Define("Jet_PUIDSF_val", "jet_PUIDSF(Jet_jetId, Jet_PUIDSF_loose)")
            .Define("LepWPCut_val", f"lepWPCut(Lepton_pdgId, Lepton_muonIdx, Muon_mvaTTH, "
                                     f"Lepton_mvaTTH_UL, {_LEP_CUT_BRANCH})")
            .Define("PromptGenLepMatch2l_val", "promptGenLepMatch2l(Lepton_promptgenmatched)")
            .Define("SFweight_val", f"SFweight2l * LepWPCut_val * {_LEP_SF_BRANCH} * "
                                     f"Jet_PUIDSF_val * btagSF_val")
        )
    else:
        df = (
            df
            .Define("bVetoSF_val", "-9999.0")
            .Define("bReqSF_val", "-9999.0")
            .Define("topcr_flag", "topcr(mtw2, mll, zeroJet, bVeto, bReq)")
            .Define("btagSF_val", "-9999.0")
            .Define("Jet_PUIDSF_val", "-9999.0")
            .Define("LepWPCut_val", "-9999.0")
            .Define("PromptGenLepMatch2l_val", "-9999.0")
            .Define("SFweight_val", "-9999.0")
        )

    df = (
        df

        .Define("Lepton_4DV1", "leptonP4(Lepton_pt, Lepton_eta, Lepton_phi, 0)")
        .Define("Lepton_4DV2", "leptonP4(Lepton_pt, Lepton_eta, Lepton_phi, 1)")
        .Define("LowestQGLJet_4DV1", "jetP4(CleanJet_pt, CleanJet_eta, CleanJet_phi, CleanJet_mass, qglOrder, 0)")
        .Define("LowestQGLJet_4DV2", "jetP4(CleanJet_pt, CleanJet_eta, CleanJet_phi, CleanJet_mass, qglOrder, 1)")

        .Define("qgl_j1_lowestqgl", "getJet(CleanJet_qgl, qglOrder, 0, -9999.f)")
        .Define("CleanJet_qgl_valid", "CleanJet_qgl[CleanJet_qgl >= 0]")
        .Define("QGLcut", "qglCut(CleanJet_qgl_valid)")

        .Define("dphijj_qgl", "dijetVars.dphijj")
    )

    if "drjj" in available:
        df = df.Redefine("drjj", "drjjPlain(CleanJet_eta, CleanJet_phi)")
    else:
        df = df.Define("drjj", "drjjPlain(CleanJet_eta, CleanJet_phi)")

    df = (
        df
        .Define("dphilljet_qgl", "dphiLLJetQGL(Lepton_4DV1, Lepton_4DV2, LowestQGLJet_phi1, qglOrder.size())")
        .Define("dphilljetjet_qgl", "dphiLLJetJetQGL(Lepton_4DV1, Lepton_4DV2, "
                                     "LowestQGLJet_4DV1, LowestQGLJet_4DV2, qglOrder.size())")

        .Define("btagDeepBj1_lowestqgl", "btagAtLowestQGL(Jet_btagDeepB, CleanJet_jetIdx, qglOrder, 0, -9999.f)")
        .Define("btagDeepBj2_lowestqgl", "btagAtLowestQGL(Jet_btagDeepB, CleanJet_jetIdx, qglOrder, 1, -9999.f)")
        .Define("btagCSVV2j1_lowestqgl", "btagAtLowestQGL(Jet_btagCSVV2, CleanJet_jetIdx, qglOrder, 0, -9999.f)")
        .Define("btagCSVV2j2_lowestqgl", "btagAtLowestQGL(Jet_btagCSVV2, CleanJet_jetIdx, qglOrder, 1, -9999.f)")

        .Define("oneJet", "isOneJet(CleanJet_pt)")
        .Define("multiJet", "isMultiJet(CleanJet_pt)")

        .Define("hole_veto", "holeVeto(Lepton_eta, Lepton_phi, Lepton_pdgId, CleanJet_eta, CleanJet_phi)")

        .Define("eventWeight", weight_expr)
    )

    return df


def process_sample(job):
    sampleName, files, weight_expr, outputFile = job

    df = build_dataframe(files, weight_expr)

    available = set(str(c) for c in df.GetColumnNames())
    columns_to_write = [c for c in OUTPUT_COLUMNS if c in available]
    missing = [c for c in OUTPUT_COLUMNS if c not in available]
    if missing:
        print(f"{sampleName}: {len(missing)} requested columns not in this "
              f"sample's tree, skipping: {missing}")

    nTotal = df.Count()
    report = df.Report()
    df.Snapshot(treeName, outputFile, columns_to_write)

    print(f"{sampleName}: {nTotal.GetValue()} events passed")
    report.Print()


def create_BDT_trees(samples):
    jobs = []

    for sampleName, sampleList in samples.items():

        sampleOutputDir = os.path.join(Output_dir, sampleName)
        os.makedirs(sampleOutputDir, exist_ok=True)

        for sample in sampleList:
            tag = sample["tag"]
            files = sample["files"]
            weight_expr = sample["weight"]

            outputFile = os.path.join(
                sampleOutputDir,
                f"{tag}.root"
            )

            jobs.append((
                tag,
                files,
                weight_expr,
                outputFile
            ))

    nWorkers = min(len(jobs), multiprocessing.cpu_count())

    print(
        f"\nProcessing {len(jobs)} samples "
        f"with {nWorkers} worker processes"
    )

    ctx = multiprocessing.get_context("spawn")

    with ProcessPoolExecutor(
        max_workers=nWorkers,
        mp_context=ctx
    ) as executor:

        futures = [
            executor.submit(process_sample, job)
            for job in jobs
        ]

        for future in as_completed(futures):
            try:
                future.result()
                print("File created successfully.")
            except Exception as e:
                print("Worker crashed:", e)


if __name__ == "__main__":
    from samples import samples as sample_dict

    start_time = time.time()

    print("\nStarting BDT tree creation...")
    create_BDT_trees(sample_dict)
    print("BDT tree creation completed.")

    elapsed = time.time() - start_time
    print(
        f"\nTotal execution time: "
        f"{elapsed:.2f} s = {elapsed/60:.2f} min"
    )