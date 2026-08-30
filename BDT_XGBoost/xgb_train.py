#!/usr/bin/env python

import os
import pickle
import numpy as np
import ROOT
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier

ROOT.gErrorIgnoreLevel = ROOT.kError
ROOT.ROOT.EnableImplicitMT()
ROOT.gInterpreter.Declare('using namespace ROOT::VecOps;')

HEADERS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "headers.h"
)

with open(HEADERS_PATH) as f:
    ok = ROOT.gInterpreter.Declare(f.read())
    print("Declared headers.h:", ok)

if not ok:
    raise RuntimeError(
        "Failed to declare headers.h -- check for a compile error above"
    )

# Toggles
NEG_WEIGHT_MODE = "abs"
# NEG_WEIGHT_MODE = "drop"
isDEV = True
# limitFiles = 1
limitFiles = -1

OUTPUT_DIR = "/eos/user/a/araghav/xgb_outputs"

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

# MVA VARIABLES
mvaVariables = [
    'detajj_qgl',
    'drjj_qgl',
    'mjj_qgl',
    'dphijj_qgl',
    'LowestQGLJet_eta1',
    'LowestQGLJet_eta2',
    'LowestQGLJet_pt1',
    'LowestQGLJet_pt2',
    'ptjj_qgl',
    'dphilljetjet_qgl',
    'drjj',
    'detajj',
    'PuppiMET_pt',
    'Lepton_pt[0]',
    'Lepton_pt[1]',
    'ptll',
]

# TRAIN / TEST SAMPLE DEFINITIONS
TRAIN_SAMPLES = [
    'Hgluglu',
    'qqZHgluglu',
    'ggZHgluglu',
    'DY_train'
]

TEST_SAMPLES = [
    'ZH_HToGluGlu_ZToLL-M125',
    'DY_test'
]


if isDEV:
    allowed_samples = set(TRAIN_SAMPLES + TEST_SAMPLES)
    for sampleName in list(samples.keys()):
        if sampleName not in allowed_samples:
            samples.pop(sampleName)


# RDF HELPERS
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
            "Add them to aliases.py, or confirm the exact branch name "
            "in the ntuple."
        )
    return df


def build_dataframe(sampleName, subentry_files, varnames, colmap):

    chain = ROOT.TChain("Events")

    for f in subentry_files:
        chain.Add(f)

    df = ROOT.RDataFrame(chain)

    existing_cols = set(str(c) for c in df.GetColumnNames())

    # Only define aliases that are actually required.
    for aliasName, alias in aliases.items():
        # if aliasName not in REQUIRED_ALIASES:
        #     continue
        if alias_applies(sampleName, alias):
            if aliasName in existing_cols:
                continue
            df = df.Define(
                aliasName,
                alias['expr']
            )
    df = resolve_variables(
        df,
        varnames,
        colmap
    )
    return df.Filter(cut)

# XGBOOST CONFIGURATIONS

XGB_CONFIGS = {
    "xgb_d2_lr001_n200": {"n_estimators": 200, "max_depth": 2, "learning_rate": 0.01, "subsample": 0.5, "min_child_weight": 1},
    "xgb_d2_lr005_n300": {"n_estimators": 300, "max_depth": 2, "learning_rate": 0.05, "subsample": 0.5, "min_child_weight": 1},
    "xgb_d2_lr010_n500": {"n_estimators": 500, "max_depth": 2, "learning_rate": 0.10, "subsample": 0.5, "min_child_weight": 1},

    "xgb_d2_lr005_n200": {"n_estimators": 200, "max_depth": 2, "learning_rate": 0.05, "subsample": 0.5, "min_child_weight": 1},
    # "xgb_d2_lr005_n300": {"n_estimators": 300, "max_depth": 2, "learning_rate": 0.05, "subsample": 0.5, "min_child_weight": 1},
    "xgb_d2_lr005_n500": {"n_estimators": 500, "max_depth": 2, "learning_rate": 0.05, "subsample": 0.5, "min_child_weight": 1},

    "xgb_d4_lr001_n200": {"n_estimators": 200, "max_depth": 4, "learning_rate": 0.01, "subsample": 0.5, "min_child_weight": 1},
    "xgb_d4_lr005_n300": {"n_estimators": 300, "max_depth": 4, "learning_rate": 0.05, "subsample": 0.5, "min_child_weight": 1},
    "xgb_d4_lr010_n500": {"n_estimators": 500, "max_depth": 4, "learning_rate": 0.10, "subsample": 0.5, "min_child_weight": 1},

    "xgb_d4_lr005_n200": {"n_estimators": 200, "max_depth": 4, "learning_rate": 0.05, "subsample": 0.5, "min_child_weight": 1},
    # "xgb_d4_lr005_n300": {"n_estimators": 300, "max_depth": 4, "learning_rate": 0.05, "subsample": 0.5, "min_child_weight": 1},
    "xgb_d4_lr005_n500": {"n_estimators": 500, "max_depth": 4, "learning_rate": 0.05, "subsample": 0.5, "min_child_weight": 1},
}

# MAIN
def runJob():

    colmap = make_valid_column_names(mvaVariables)
    train_X = []
    train_y = []
    train_w = []

    test_X = []
    test_y = []
    test_w = []

    # LOAD EVENTS
    for sampleName, subentries in samples.items():
        if sampleName not in TRAIN_SAMPLES and sampleName not in TEST_SAMPLES:
            print(
                f"WARNING: sample '{sampleName}' is not in "
                "TRAIN_SAMPLES or TEST_SAMPLES, skipping"
            )
            continue

        if structure[sampleName]['isData'] == 1:
            continue

        if sampleName in TRAIN_SAMPLES:
            bucket = "train"
        else:
            bucket = "test"

        isSig = structure[sampleName]['isSignal']

        print(
            f"Processing sample: {sampleName} -> "
            f"{bucket} ({len(subentries)} sub-entries)"
        )

        for sub in subentries:
            tag = sub['tag']
            files = sub['files']
            weight_expr = sub['weight']
            if not files:
                print(
                    f"  [{tag}] -> 0 files, skipping"
                )
                continue

            df = build_dataframe(
                sampleName,
                files,
                mvaVariables,
                colmap
            )
            df = df.Define(
                "eventWeight",
                weight_expr
            )
            cols = (
                list(colmap.values())
                + ["eventWeight"]
            )
            data = df.AsNumpy(
                columns=cols
            )

            n = len(
                data["eventWeight"]
            )

            if n == 0:
                print(
                    f"  [{tag}] -> 0 events passed selection, skipping"
                )
                continue

            X = np.column_stack(
                [
                    data[colmap[v]]
                    for v in mvaVariables
                ]
            )

            w = np.asarray(data["eventWeight"],
                dtype=np.float64
            )

            y = np.full( n, isSig )

            # Negative event weights

            if NEG_WEIGHT_MODE == "abs":
                w = np.abs(w)
            elif NEG_WEIGHT_MODE == "drop":
                keep = w > 0
                X = X[keep]
                y = y[keep]
                w = w[keep]
                n = keep.sum()
            else:
                raise ValueError(
                    f"Unknown NEG_WEIGHT_MODE: {NEG_WEIGHT_MODE}"
                )
            print(
                f"  [{tag}] -> {n} events"
            )

            # Store train/test
            if bucket == "train":
                train_X.append(X)
                train_y.append(y)
                train_w.append(w)
            else:
                test_X.append(X)
                test_y.append(y)
                test_w.append(w)

    # COMBINE TRAINING DATA

    X_train = np.concatenate(train_X)
    y_train = np.concatenate(train_y)
    w_train = np.concatenate(train_w)
    # COMBINE TEST DATA
    X_test = np.concatenate(test_X)
    y_test = np.concatenate(test_y)
    w_test = np.concatenate(test_w)

    print("\nDataset summary")
    print("----------------------------------------")
    print( f"Training events : {len(y_train)}" )
    print( f"Testing events  : {len(y_test)}" )
    print( f"Training signal : {np.sum(y_train == 1)}" )
    print( f"Training bkg    : {np.sum(y_train == 0)}" )
    print( f"Testing signal  : {np.sum(y_test == 1)}" )
    print( f"Testing bkg     : {np.sum(y_test == 0)}" )

    dataset_filename = os.path.join(OUTPUT_DIR, "xgb_Hgg_dataset.npz")
    np.savez(
        dataset_filename,
        y_train=y_train,
        w_train=w_train,
        X_train=X_train,
        y_test=y_test,
        w_test=w_test,
        X_test=X_test,
        mvaVariables=np.array(mvaVariables),
    )
    print(f"Saved shared dataset -> {dataset_filename}")

    # NORMALIZE TRAINING WEIGHTS

    w_train_norm = w_train.copy()
    for cls in [0, 1]:
        mask = y_train == cls
        total = w_train_norm[mask].sum()
        n = mask.sum()

        if total > 0:
            w_train_norm[mask] = (
                w_train_norm[mask]
                / total
                * n
            )
    results = {}
    for config_name, params in XGB_CONFIGS.items():

        print("\n")
        print("=" * 70)
        print( f"Training configuration: {config_name}")
        print("=" * 70)
        print("Parameters:")
        for key, value in params.items():
            print(f"  {key}: {value}")
        # Create classifier

        clf = XGBClassifier(
            **params,
            eval_metric="logloss"
        )
        # Train
        clf.fit(
            X_train,
            y_train,
            sample_weight=w_train_norm
        )
        # BDT scores
        train_scores = (
            clf.predict_proba(X_train)[:, 1]
        )
        test_scores = (
            clf.predict_proba(X_test)[:, 1]
        )
        # AUC
        train_auc = roc_auc_score(
            y_train,
            train_scores,
            sample_weight=w_train
        )
        test_auc = roc_auc_score(
            y_test,
            test_scores,
            sample_weight=w_test
        )
        print(f"\nTrain AUC: {train_auc:.4f}" )
        print(f"Test AUC:  {test_auc:.4f}" )

        # Store results
        results[config_name] = {
            "params": params,
            "train_auc": train_auc,
            "test_auc": test_auc,
        }

        # Save model
        model_filename = os.path.join(
            OUTPUT_DIR, f"xgb_Hgg_{config_name}.pkl"
        )
        with open(model_filename, "wb") as f:
            pickle.dump(
                clf,
                f
            )

        scores_filename = os.path.join(
            OUTPUT_DIR, f"xgb_Hgg_scores_{config_name}.npz"
        )
        np.savez(
            scores_filename,
            train_scores=train_scores,
            test_scores=test_scores,
            train_auc=train_auc,
            test_auc=test_auc,
        )
        # Variable importance

        importance = (
            clf.feature_importances_
        )
        ranking = sorted(
            zip(mvaVariables, importance),
            key=lambda x: x[1],
            reverse=True
        )

        print(f"\nVariable Importance Ranking: {config_name}")
        print("----------------------------------------")


        for rank, (var, imp) in enumerate(
            ranking,
            start=1
        ):

            print(f"{rank:2d} : "
                  f"{var:<25} "
                  f"{imp:.4f}")

        del clf


# SUMMARY
    print("\n")
    print("=" * 90)
    print("XGBoost Configuration Summary")
    print("=" * 90)

    print(
        f"{'Config':<15}"
        f"{'Depth':>8}"
        f"{'Trees':>8}"
        f"{'LR':>10}"
        f"{'Subsample':>12}"
        f"{'MCW':>8}"
        f"{'Train AUC':>12}"
        f"{'Test AUC':>12}"
    )
    print("-" * 90)

    for name, result in results.items():

        p = result["params"]
        print(
            f"{name:<15}"
            f"{p['max_depth']:>8}"
            f"{p['n_estimators']:>8}"
            f"{p['learning_rate']:>10.3f}"
            f"{p['subsample']:>12.2f}"
            f"{p['min_child_weight']:>8}"
            f"{result['train_auc']:>12.4f}"
            f"{result['test_auc']:>12.4f}"
        )
# MAIN
if __name__ == "__main__":
    runJob()