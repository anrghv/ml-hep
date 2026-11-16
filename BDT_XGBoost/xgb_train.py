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
isDEV = False
# limitFiles = 1
limitFiles = -1

OUTPUT_DIR = "/eos/user/a/araghav/xgboost/outputs_ml-hep"

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
    # Lepton kinematics
    'Lepton_pt[0]',
    'Lepton_pt[1]',
    'ptll',
    'mll',

    # Missing transverse energy
    # 'PuppiMET_pt',

    # Jet kinematics
    # 'Alt(CleanJet_pt,0,0)',
    # 'Alt(CleanJet_pt,1,0)',
    # 'Alt(CleanJet_eta,0,0)',
    # 'Alt(CleanJet_eta,1,0)',

    # Lowest-QGL jet kinematics
    'LowestQGLJet_pt1',
    'LowestQGLJet_pt2',
    'LowestQGLJet_pt3',
    # 'LowestQGLJet_eta1',
    # 'LowestQGLJet_eta2',
    # 'LowestQGLJet_phi1',
    # 'LowestQGLJet_phi2',
    'LowestQGLJet_mass1',
    'LowestQGLJet_mass2',

    # Jet QGL information
    'qgl_j1_lowestqgl',

    # Jet b-tagging information
    'btagDeepBj1_lowestqgl',
    'btagDeepBj2_lowestqgl',
    'btagCSVV2j1_lowestqgl',
    # 'btagCSVV2j2_lowestqgl',

    # Dijet kinematics
    'mjj',
    'mjj_qgl',
    # 'mjj_qgl_cc',
    # 'ptjj',
    'ptjj_qgl',
    'detajj',
    'detajj_qgl',
    'dphijj',
    'dphijj_qgl',
    'drjj',
    'drjj_qgl',

    # Lepton-jet angular variables
    'dphilljet',
    # 'dphilljet_qgl',
    'dphilljetjet',
    'dphilljetjet_qgl',

    # Jet multiplicity / QGL information
    # 'CleanJet_qgl_valid.size()',
]


PROCESS_SAMPLES = ["DY", "ZH_HToGluGlu_ZToLL-M125"]

# # TRAIN / TEST SAMPLE DEFINITIONS
# TRAIN_SAMPLES = [ 
#     # 'Hgluglu',
#     # 'qqZHgluglu',
#     # 'ggZHgluglu',
#     'DY',
#     'ZH_HToGluGlu_ZToLL-M125'
# ]

# TEST_SAMPLES = [
#     'ZH_HToGluGlu_ZToLL-M125',
#     # 'DY_test'
#     # 'Hgluglu',
#     # 'qqZHgluglu',
#     # 'ggZHgluglu',
#     'DY'
# ]


if isDEV:
    # allowed_samples = set(TRAIN_SAMPLES + TEST_SAMPLES)
    allowed_samples = set(PROCESS_SAMPLES)
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

    # "xgb_tuned_1": {
    # "n_estimators": 600,
    # "max_depth": 5,
    # "learning_rate": 0.12154323374774018,
    # "min_child_weight": 15,
    # "gamma": 2.8567812963999484,
    # "subsample": 0.6907226513881366,
    # "colsample_bytree": 0.5535883729682609,
    # "colsample_bynode": 0.6615567046239513,
    # "reg_alpha": 0.31352699641664766,
    # "reg_lambda": 2.761264429359447
    # },

    "xgb_tuned_2": {
        "n_estimators": 600,
        "max_depth": 3,
        "learning_rate": 0.12154323374774018,
        "min_child_weight": 15,
        "gamma": 2.8567812963999484,
        "subsample": 0.6907226513881366,
        "colsample_bytree": 0.5535883729682609,
        "colsample_bynode": 0.6615567046239513,
        "reg_alpha": 0.31352699641664766,
        "reg_lambda": 2.761264429359447
        },

    #     "xgb_tuned_3": {
    #         "n_estimators": 600,
    #         "max_depth": 3,
    #         "learning_rate": 0.12154323374774018,
    #         "min_child_weight": 10,
    #         "gamma": 2.8567812963999484,
    #         "subsample": 0.6907226513881366,
    #         "colsample_bytree": 0.5535883729682609,
    #         "colsample_bynode": 0.6615567046239513,
    #         "reg_alpha": 0.31352699641664766,
    #         "reg_lambda": 2.761264429359447
    #         },

    #         "xgb_tuned_4": {
    #             "n_estimators": 600,
    #             "max_depth": 3,
    #             "learning_rate": 0.12154323374774018,
    #             "min_child_weight": 8,
    #             "gamma": 2.8567812963999484,
    #             "subsample": 0.6907226513881366,
    #             "colsample_bytree": 0.5535883729682609,
    #             "colsample_bynode": 0.6615567046239513,
    #             "reg_alpha": 0.31352699641664766,
    #             "reg_lambda": 2.761264429359447
    #             },






    # 1. Depth 6 with tuned L1/L2 regularization (building on d6_reg)
    # "xgb_d6_lr03_n600_l2": {"n_estimators": 600, "max_depth": 6, "learning_rate": 0.03, "subsample": 0.8, "colsample_bytree": 0.7,
    #                          "min_child_weight": 8,"reg_lambda": 3.0, "gamma": 1.5
    # },
    # "xgb_d6_lr03_n700_l1l2": { "n_estimators": 700, "max_depth": 6, "learning_rate": 0.03, "subsample": 0.8, "colsample_bytree": 0.7,
    #                            "min_child_weight": 10, "reg_alpha": 0.5, "reg_lambda": 2.0, "gamma": 1.0
    # },

    # 3. Depth 5 deeper optimization (highly robust against overtraining)
    # "xgb_d5_lr03_n700_dense": {"n_estimators": 200, "max_depth": 3, "learning_rate": 0.03, "subsample": 0.85, "colsample_bytree": 0.75,
    #                             "min_child_weight": 5, "reg_lambda": 2.0, "gamma": 0.5
    # },
    # "xgb_d5_lr04_n600_l1": {"n_estimators": 600, "max_depth": 5, "learning_rate": 0.04, "subsample": 0.8, "colsample_bytree": 0.7, 
    #                          "min_child_weight": 6, "reg_alpha": 0.2, "reg_lambda": 1.0
    # },
    # 2. Depth 6 with node-level subsampling (forces orthogonal kinematic splits)
    # "xgb_d6_lr04_n600_node": { "n_estimators": 600, "max_depth": 6, "learning_rate": 0.04, "subsample": 0.8, "colsample_bytree": 0.8,
    #                            "colsample_bynode": 0.7, "min_child_weight": 8, "reg_lambda": 1.5
    # },


    # 4. Depth 7 with heavy regularization (curbing the overtraining seen in d7/d8)
    # "xgb_d7_lr02_n800_heavyreg": { "n_estimators": 800, "max_depth": 7, "learning_rate": 0.02, "subsample": 0.8, "colsample_bytree": 0.65,
    #                                "min_child_weight": 12, "reg_alpha": 1.0, "reg_lambda": 5.0, "gamma": 2.0
    # },
    # "xgb_d7_lr02_n700_mcw15": { "n_estimators": 700, "max_depth": 7, "learning_rate": 0.02, "subsample": 0.8, "colsample_bytree": 0.6,
    #                             "min_child_weight": 15, "reg_lambda": 3.0, "gamma": 1.5
    # },

    # 5. Fast convergence checks (moderate trees, slightly higher LR)
    # "xgb_d6_lr06_n500_reg": { "n_estimators": 500, "max_depth": 6, "learning_rate": 0.06, "subsample": 0.8, "colsample_bytree": 0.7,
    #                         "min_child_weight": 10, "reg_alpha": 0.2, "reg_lambda": 2.0, "gamma": 1.0
    # },
}

# MAIN
def runJob():

    colmap = make_valid_column_names(mvaVariables)
    train_X, train_y, train_w = [], [], []
    test_X, test_y, test_w = [], [], []

    # LOAD EVENTS
    for sampleName, subentries in samples.items():
        # if sampleName not in TRAIN_SAMPLES and sampleName not in TEST_SAMPLES:
        if sampleName not in PROCESS_SAMPLES:
            print(
                f"WARNING: sample '{sampleName}' is not in "
                "TRAIN_SAMPLES or TEST_SAMPLES, skipping"
            )
            continue

        if structure[sampleName]['isData'] == 1:
            continue

        # if sampleName in TRAIN_SAMPLES:
        #     bucket = "train"
        # else:
        #     bucket = "test"

        isSig = structure[sampleName]['isSignal']

        # print(
        #     f"Processing sample: {sampleName} -> "
        #     f"{bucket} ({len(subentries)} sub-entries)"
        # )
        print(f"Processing sample: {sampleName} (Splitting even/odds events)")

        for sub in subentries:
            tag = sub['tag']
            files = sub['files']
            weight_expr = sub['weight']
            if not files:
                print(f"  [{tag}] -> 0 files, skipping")
                continue

            df = build_dataframe(
                sampleName,
                files,
                mvaVariables,
                colmap
            )
            df = df.Define("eventWeight", weight_expr)
            has_event_branch = "event" in [str(c) for c in df.GetColumnNames()]
            cols = (list(colmap.values())+ ["eventWeight"])
            if has_event_branch:
                cols.append("event")

            data = df.AsNumpy(columns=cols)

            n = len(data["eventWeight"])

            if n ==0:
                print(f"  [{tag}] -> 0 events after preselections, skipping")
                continue

            X = np.column_stack([data[colmap[v]] for v in mvaVariables])
            w = np.asarray(data["eventWeight"], dtype=np.float64)
            y = np.full(n, isSig)

            if NEG_WEIGHT_MODE == "abs":
                w = np.abs(w)
            elif NEG_WEIGHT_MODE == "drop":
                keep = w > 0
                X = X[keep], y = y[keep], w = w[keep]
                if has_event_branch: 
                    data["event"] = data["event"][keep]
                n = keep.sum()
            else: 
                raise ValueError(f"Unknown NEG_WEIGHT_MODE: {NEG_WEIGHT_MODE}")

                # Defining alternating split (even = trian; odd = test)
            if has_event_branch:
                train_mask = (data["event"] % 2 == 0)  # what does this do? It creates a boolean mask where events with even event numbers are marked as True (for training) and odd event numbers are marked as False (for testing). This is a way to split the dataset into training and testing sets based on the event number.
            else: 
                train_mask = np.arange(n) % 2 == 0      # If the "event" branch is not available, it creates a boolean mask based on the index of the events. Events with even indices are marked as True (for training) and odd indices are marked as False (for testing). This is another way to split the dataset into training and testing sets based on the order of the events in the dataset.

            test_mask = ~train_mask 

            # Append alternating split to train/test lists
            train_X.append(X[train_mask])
            train_y.append(y[train_mask])
            train_w.append(w[train_mask])

            test_X.append(X[test_mask])
            test_y.append(y[test_mask])
            test_w.append(w[test_mask])

            print(f"  [{tag}] -> {n} total events ({train_mask.sum()} train, {test_mask.sum()} test)")

    X_train = np.concatenate(train_X)
    y_train = np.concatenate(train_y)
    w_train = np.concatenate(train_w)
    X_test = np.concatenate(test_X)
    y_test = np.concatenate(test_y)
    w_test = np.concatenate(test_w)

    print("\nDataset summary")
    print("----------------------------------------")
    print(f"Training events : {len(y_train)}")
    print(f"Testing events  : {len(y_test)}")
    print(f"Training signal : {np.sum(y_train == 1)}")
    print(f"Training bkg    : {np.sum(y_train == 0)}")
    print(f"Testing signal  : {np.sum(y_test == 1)}")
    print(f"Testing bkg     : {np.sum(y_test == 0)}")

    dataset_filename = os.path.join(OUTPUT_DIR, "xgb_Hgg_tuning.npz")
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

    #Normalize training weights
    w_train_norm = w_train.copy()
    for cls in [0, 1]:
        mask = y_train == cls
        total = w_train_norm[mask].sum()
        n_cls = mask.sum()

        if total > 0:
            w_train_norm[mask] = (w_train_norm[mask]/ total* n_cls)

    results = {}
    for config_name, params in XGB_CONFIGS.items():

        print("\n" + "+" * 70)
        print(f"Training configuration: {config_name}")
        print("Parameters:")
        for key, value in params.items():
            print(f"  {key}: {value}")
        
        clf = XGBClassifier(**params, eval_metric="logloss")

        # clf.fit(X_train, y_train, sample_weight=None)
        clf.fit(X_train, y_train, sample_weight=w_train_norm)

        train_scores = clf.predict_proba(X_train)[:, 1]
        test_scores = clf.predict_proba(X_test)[:, 1]

        train_auc = roc_auc_score(y_train, train_scores, sample_weight=w_train)
        test_auc = roc_auc_score(y_test, test_scores, sample_weight=w_test)

        print(f"\nTrain AUC: {train_auc:.4f}")
        print(f"Test AUC:  {test_auc:.4f}")

        results[config_name] = {
            "params": params,
            "train_auc": train_auc,
            "test_auc": test_auc,
        }

        model_filename = os.path.join(OUTPUT_DIR, f"xgb_Hgg_{config_name}.pkl")
        with open(model_filename, "wb") as f:
            pickle.dump(clf, f)

        importance = clf.feature_importances_

        scores_filename = os.path.join(OUTPUT_DIR, f"xgb_Hgg_scores_{config_name}.npz")
        np.savez(
            scores_filename,
            train_scores=train_scores,
            test_scores=test_scores,
            train_auc=train_auc,
            test_auc=test_auc,
            feature_importances=importance,
            feature_names=np.array(mvaVariables),
        )

        # importance = clf.feature_importances_
        ranking = sorted(zip(mvaVariables, importance), key=lambda x: x[1], reverse=True)

        print(f"\nVariable Importance Ranking: {config_name}")
        print("----------------------------------------")
        for rank, (var, imp) in enumerate(ranking, start=1):
            print(f"{rank:2d} : {var:<25} {imp:.4f}")

        del clf

    print("\n" + "=" * 90)
    print("XGBoost Configuration Summary")
    print("=" * 90)
    print(
        f"{'Config':<20}"
        f"{'Depth':>8}"
        f"{'Trees':>8}"
        f"{'LR':>10}"
        f"{'Subsample':>12}"
        f"{'MCW':>8}"
        f"{'Train AUC':>12}"
        f"{'Test AUC':>12}"
        f"{'Difference':>12}"
    )
    print("-" * 90)

    for name, result in results.items():
        p = result["params"]
        print(
            f"{name:<20}"
            f"{p['max_depth']:>8}"
            f"{p['n_estimators']:>8}"
            f"{p['learning_rate']:>10.3f}"
            f"{p['subsample']:>12.2f}"
            f"{p['min_child_weight']:>8}"
            f"{result['train_auc']:>12.4f}"
            f"{result['test_auc']:>12.4f}"
            f"{result['train_auc'] - result['test_auc']:>12.4f}"
        )


    # print("Train signal weight:", w_train[y_train == 1].sum())
    # print("Train background weight:", w_train[y_train == 0].sum())

    # print("Test signal weight:", w_test[y_test == 1].sum())
    # print("Test background weight:", w_test[y_test == 0].sum())
if __name__ == "__main__":
    runJob()
    # print(samples.keys())
