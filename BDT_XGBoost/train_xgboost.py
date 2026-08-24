#!/usr/bin/env python
import os
import pickle
import numpy as np
import ROOT

from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier

ROOT.gErrorIgnoreLevel = ROOT.kError
ROOT.ROOT.EnableImplicitMT()
ROOT.gInterpreter.Declare('using namespace ROOT::VecOps;')

# --- custom header (Alt, LogVec, etc.) -- same one aliases.py depends on ---
import mkShapesRDF
HEADERS_PATH = os.path.join(os.path.dirname(mkShapesRDF.__file__), "include", "headers.h")
with open(HEADERS_PATH) as f:
    ROOT.gInterpreter.Declare(f.read())

# --- weight-handling strategy ---
NEG_WEIGHT_MODE = "abs"   # "abs" -> take abs(weight); "drop" -> discard negative-weight events

isDEV = False


# -----------------------------------------------------------------------
# Load configuration (same exec-chain pattern as configHgg_cfg.py)
# -----------------------------------------------------------------------

with open("configuration.py") as handle:
    exec(handle.read())

samples = {}
structure = {}
cuts = {}
for f in [samplesFile, structureFile, cutsFile]:
    with open(f) as handle:
        exec(handle.read())

aliases = {}
with open("aliases.py") as handle:
    exec(handle.read())

with open("preselections.py") as handle:
    exec(handle.read())

cut = "(({0}) && ({1}))".format(supercut, preselections)

mvaVariables = [
    'detajj_qgl', 'drjj_qgl', 'mjj_qgl', 'dphijj_qgl',
    'LowestQGLJet_eta1', 'LowestQGLJet_eta2',
    'LowestQGLJet_pt1', 'LowestQGLJet_pt2', 'ptjj_qgl',
    'dphilljetjet_qgl', 'drjj',
    'detajj', 'PuppiMET_pt', 'Lepton_pt[0]', 'Lepton_pt[1]', 'ptll',
]

if isDEV:
    for sampleName in list(samples.keys()):
        if sampleName not in ['Hgluglu', 'DY']:
            samples.pop(sampleName)


# -----------------------------------------------------------------------
# RDF helpers
# -----------------------------------------------------------------------

def alias_applies(sampleName, alias):
    if 'samples' not in alias:
        return True
    scope = alias['samples']
    if isinstance(scope, str):
        return sampleName == scope
    return sampleName in scope


def build_dataframe(sampleName, sample):
    chain = ROOT.TChain("Events")
    for tag, filelist, *rest in sample['name']:
        for f in filelist:
            chain.Add(f)

    df = ROOT.RDataFrame(chain)
    for aliasName, alias in aliases.items():
        if alias_applies(sampleName, alias):
            df = df.Define(aliasName, alias['expr'])

    return df.Filter(cut)


def make_valid_column_names(varnames):
    # RDF column names can't contain '[' or ']' -- alias any raw branch
    # array-index expressions ("Lepton_pt[0]") to a plain identifier.
    mapping = {}
    for v in varnames:
        if any(c in v for c in "[]"):
            safe = v.replace("[", "_").replace("]", "")
            mapping[v] = safe
        else:
            mapping[v] = v
    return mapping


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def runJob():
    colmap = make_valid_column_names(mvaVariables)

    all_X, all_y, all_w = [], [], []

    for sampleName, sample in samples.items():
        if structure[sampleName]['isData'] == 1:
            continue

        print("Processing sample:", sampleName)
        df = build_dataframe(sampleName, sample)

        # alias any raw-branch expressions that AsNumpy can't use as column names
        for orig, safe in colmap.items():
            if orig != safe:
                df = df.Define(safe, orig)

        weight_expr = sample['weight']
        df = df.Define("eventWeight", weight_expr)

        cols = list(colmap.values()) + ["eventWeight"]
        data = df.AsNumpy(columns=cols)

        n = len(data["eventWeight"])
        if n == 0:
            print(f"  -> 0 events passed selection, skipping")
            continue

        X = np.column_stack([data[colmap[v]] for v in mvaVariables])
        w = np.asarray(data["eventWeight"], dtype=np.float64)
        isSig = structure[sampleName]['isSignal']
        y = np.full(n, isSig)

        if NEG_WEIGHT_MODE == "abs":
            w = np.abs(w)
        elif NEG_WEIGHT_MODE == "drop":
            keep = w > 0
            X, y, w = X[keep], y[keep], w[keep]
            n = keep.sum()
        else:
            raise ValueError(f"Unknown NEG_WEIGHT_MODE: {NEG_WEIGHT_MODE}")

        print(f"  -> {n} events, {n if isSig else 0} signal")
        all_X.append(X)
        all_y.append(y)
        all_w.append(w)

    X = np.concatenate(all_X)
    y = np.concatenate(all_y)
    w = np.concatenate(all_w)

    X_train, X_test, y_train, y_test, w_train, w_test = train_test_split(
        X, y, w, test_size=0.5, random_state=42, stratify=y
    )

    # per-class weight normalization -- avoids the AUC=0.5 collapse from
    # raw physical weights swamping the loss
    w_train_norm = w_train.copy()
    for cls in [0, 1]:
        mask = y_train == cls
        total = w_train_norm[mask].sum()
        if total > 0:
            w_train_norm[mask] = w_train_norm[mask] / total

    clf = XGBClassifier(
        n_estimators=500,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.5,
        eval_metric="logloss",
    )
    clf.fit(X_train, y_train, sample_weight=w_train_norm)

    train_scores = clf.predict_proba(X_train)[:, 1]
    test_scores = clf.predict_proba(X_test)[:, 1]

    print("Train AUC:", roc_auc_score(y_train, train_scores, sample_weight=w_train))
    print("Test AUC:", roc_auc_score(y_test, test_scores, sample_weight=w_test))

    with open("xgb_Hgg.pkl", "wb") as f:
        pickle.dump(clf, f)

    np.savez(
        "xgb_Hgg_scores.npz",
        y_train=y_train, train_scores=train_scores, w_train=w_train,
        y_test=y_test, test_scores=test_scores, w_test=w_test,
    )

    for var, imp in zip(mvaVariables, clf.feature_importances_):
        print(f"{var}: {imp:.4f}")


if __name__ == "__main__":
    runJob()