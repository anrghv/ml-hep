import ROOT
import os
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

ROOT.gErrorIgnoreLevel = ROOT.kFatal
ROOT.ROOT.EnableImplicitMT()

treeName = "Events"
Output_dir = "/eos/user/a/araghav/BDT_Trees"

OUTPUT_COLUMNS = [
    "mll", "lep_pt1", "lep_pt2",
    "LowestQGLJet_pt1", "LowestQGLJet_pt2", "LowestQGLJet_pt3",
    "LowestQGLJet_eta1", "LowestQGLJet_eta2",
    "LowestQGLJet_phi1", "LowestQGLJet_phi2",
    "LowestQGLJet_mass1", "LowestQGLJet_mass2",
    "mjj_qgl", "ptjj_qgl", "detajj_qgl", "drjj_qgl",
    "eventWeight",
]


_helpers_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers.h")
ROOT.gInterpreter.Declare(f'#include "{_helpers_path}"')

_LEP_CUT_BRANCH = "LepCut2l__ele_mvaFall17V2Iso_WP90__mu_cut_Tight_HWWW"
_LEP_SF_BRANCH = "LepSF2l__ele_mvaFall17V2Iso_WP90__mu_cut_Tight_HWWW"


def build_dataframe(files, weight_expr, is_signal):
    df = ROOT.RDataFrame(treeName, files)

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
    )
    if is_signal:
        # signal weight formulas are self-contained (genWeight*xsec*BR), no SF chain needed
        df = df.Define("eventWeight", weight_expr)
    else:
        # full background SF chain -- only computed for background samples
        df = (
            df
            .Define("zeroJet", "Alt(CleanJet_pt, (size_t)0, 0.f) < 30.")
            .Define("bVeto", "bveto(CleanJet_pt, CleanJet_eta, CleanJet_jetIdx, Jet_btagDeepB)")
            .Define("bReq", "breq(CleanJet_pt, CleanJet_eta, CleanJet_jetIdx, Jet_btagDeepB)")
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
            .Define("eventWeight", weight_expr)
        )
 
    return df


 
def process_sample(job):
    sampleName, files, weight_expr, is_signal, outputFile = job
 
    df = build_dataframe(files, weight_expr, is_signal)
 
    nTotal = df.Count()
    report = df.Report()
    df.Snapshot(treeName, outputFile, OUTPUT_COLUMNS)
 
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
            is_signal = sample["isSignal"]

            outputFile = os.path.join(
                sampleOutputDir,
                f"{tag}.root"
            )

            jobs.append((
                tag,
                files,
                weight_expr,
                is_signal,
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


