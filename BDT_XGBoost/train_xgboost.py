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

HEADERS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "headers.h")
with open(HEADERS_PATH) as f:
    ok = ROOT.gInterpreter.Declare(f.read())
    print("Declared headers.h:", ok)
if not ok:
    raise RuntimeError("Failed to declare headers.h -- check for a compile error above")

NEG_WEIGHT_MODE = "abs"
isDEV = False

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

cut = preselections

mvaVariables = [
    'detajj_qgl', 'drjj_qgl', 'mjj_qgl', 'dphijj_qgl',
    'LowestQGLJet_eta1', 'LowestQGLJet_eta2',
    'LowestQGLJet_pt1', 'LowestQGLJet_pt2', 'ptjj_qgl',
    'dphilljetjet_qgl', 'drjj', 'detajj',
    'PuppiMET_pt', 'Lepton_pt[0]', 'Lepton_pt[1]', 'ptll',
]

TRAIN_SAMPLES = ['Hgluglu_train', 'qqZHgluglu_train', 'DY_train']
TEST_SAMPLES = ['ggZHgluglu_test', 'DY_test']

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


def make_valid_column_names(varnames):
    mapping = {}
    for v in varnames:
        if any(c in v for c in "[]"):
            mapping[v] = v.replace("[", "_").replace("]", "")
        else:
            mapping[v] = v
    return mapping


def resolve_variables(df, varnames, colmap):
    
    available = set(str(c) for c in df.GetColumnNames())
    missing = []

    for orig, safe in colmap.items():
        if orig in available:
            if orig != safe:
                df = df.Define(safe, orig)
        elif "[" in orig:
            df = df.Define(safe, orig)
        else:
            missing.append(orig)

    if missing:
        raise RuntimeError(
            "The following mvaVariables are neither a defined alias nor a "
            f"real branch on this sample's tree: {missing}\n"
            "Add them to aliases.py, or confirm the exact branch name in the ntuple."
        )

    return df


def build_dataframe(sampleName, subentry_files, varnames, colmap):
    chain = ROOT.TChain("Events")
    for f in subentry_files:
        chain.Add(f)

    df = ROOT.RDataFrame(chain)
    existing_cols = set(str(c) for c in df.GetColumnNames())

    for aliasName, alias in aliases.items():
        if alias_applies(sampleName, alias):
            if aliasName in existing_cols:
                continue
            df = df.Define(aliasName, alias['expr'])

    df = resolve_variables(df, varnames, colmap)
    return df.Filter(cut)


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def runJob():
    colmap = make_valid_column_names(mvaVariables)

    # all_X, all_y, all_w = [], [], []
    train_X, train_y, train_w = [], [], []
    test_X, test_y, test_w = [], [], []

    for sampleName, subentries in samples.items():
        if structure[sampleName]['isData'] == 1:
            continue

        if sampleName in TRAIN_SAMPLES:
            bucket = "train"
        elif sampleName in TEST_SAMPLES:
            bucket = "test"
        else: 
            print(f"WARNING: sample '{sampleName}' is not in TRAIN_SAMPLES or TEST_SAMPLES, skipping")
            continue

        isSig = structure[sampleName]['isSignal']
        print(f"Processing sample: {sampleName} -> {bucket} ({len(subentries)} sub-entries)")

        for sub in subentries:
            tag = sub['tag']
            files = sub['files']
            weight_expr = sub['weight']

            if not files:
                print(f"  [{tag}] -> 0 files, skipping")
                continue

            df = build_dataframe(sampleName, files, mvaVariables, colmap)
            df = df.Define("eventWeight", weight_expr)

            cols = list(colmap.values()) + ["eventWeight"]
            data = df.AsNumpy(columns=cols)

            n = len(data["eventWeight"])
            if n == 0:
                print(f"  [{tag}] -> 0 events passed selection, skipping")
                continue

            X = np.column_stack([data[colmap[v]] for v in mvaVariables])
            w = np.asarray(data["eventWeight"], dtype=np.float64)
            y = np.full(n, isSig)

            if NEG_WEIGHT_MODE == "abs":
                w = np.abs(w)
            elif NEG_WEIGHT_MODE == "drop":
                keep = w > 0
                X, y, w = X[keep], y[keep], w[keep]
                n = keep.sum()
            else:
                raise ValueError(f"Unknown NEG_WEIGHT_MODE: {NEG_WEIGHT_MODE}")

            print(f"  [{tag}] -> {n} events")

            if bucket == "train":
                train_X.append(X)
                train_y.append(y)
                train_w.append(w)
            else:
                test_X.append(X)
                test_y.append(y)
                test_w.append(w)
            # all_X.append(X)
            # all_y.append(y)
            # all_w.append(w)

    # X = np.concatenate(train_X)
    # y = np.concatenate(train_y)
    # w = np.concatenate(train_w)

    X_train = np.concatenate(train_X)
    y_train = np.concatenate(train_y)
    w_train = np.concatenate(train_w)

    X_test = np.concatenate(test_X)
    y_test = np.concatenate(test_y) 
    w_test = np.concatenate(test_w)

    # X_train, X_test, y_train, y_test, w_train, w_test = train_test_split(
    #     X, y, w, test_size=0.5, random_state=42, stratify=y
    # )
    w_train_norm = w_train.copy()
    for cls in [0, 1]:
        mask = y_train == cls
        total = w_train_norm[mask].sum()
        n = mask.sum()
        if total > 0:
            w_train_norm[mask] = w_train_norm[mask] / total * n

    clf = XGBClassifier(
        n_estimators=500, max_depth=2, learning_rate=0.05,
        subsample=0.5, eval_metric="logloss", 
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
        y_train=y_train, train_scores=train_scores, w_train=w_train, X_train=X_train,
        y_test=y_test, test_scores=test_scores, w_test=w_test, X_test=X_test,
        mvaVariables=np.array(mvaVariables),
    )

    for var, imp in zip(mvaVariables, clf.feature_importances_):
        print(f"{var}: {imp:.4f}")


if __name__ == "__main__":
    runJob()