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
]

_helpers_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers.h")
ROOT.gInterpreter.Declare(f'#include "{_helpers_path}"')


def build_dataframe(files):
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
    return df


def process_sample(job):
    sampleName, files, outputFile = job

    df = build_dataframe(files)

    nTotal = df.Count()
    report = df.Report()
    df.Snapshot(treeName, outputFile, OUTPUT_COLUMNS)

    print(f"{sampleName}: {nTotal.GetValue()} events passed")
    report.Print()


def create_BDT_trees(samples):
    jobs = []
    for sampleName, sample in samples.items():
        sampleOutputDir = os.path.join(Output_dir, sampleName)
        os.makedirs(sampleOutputDir, exist_ok=True)
        outputFile = os.path.join(sampleOutputDir, f"{sampleName}.root")
        jobs.append((sampleName, sample["name"], outputFile))

    nWorkers = min(len(jobs), multiprocessing.cpu_count())
    print(f"Processing {len(jobs)} samples with {nWorkers} worker processes")

    ctx = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=nWorkers, mp_context=ctx) as executor:
        futures = [executor.submit(process_sample, job) for job in jobs]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print("Worker crashed:", e)


if __name__ == "__main__":
    from samples import samples as sample_dict

    start_time = time.time()
    create_BDT_trees(sample_dict)
    elapsed = time.time() - start_time
    print(f"\nTotal execution time: {elapsed:.2f} s = {elapsed/60:.2f} min")