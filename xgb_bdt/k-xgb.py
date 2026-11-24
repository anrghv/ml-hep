import os
import pickle
import re
import numpy as np
import ROOT
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier

ROOT.gErrorIgnoreLevel = ROOT.kError 
ROOT.ROOT.EnableImplicitMT()
ROOT.gInterpreter.Declare('using namespace ROOT::VecOps;')

HEADERS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "headers.h")

with open(HEADERS_PATH) as f:
    ok = ROOT.gInterpreter.Declare(f.read())
    print("Declared headers.h", ok)
if not ok:
    raise RuntimeError("Failed to declare headers.h")

#-----------------------------------------------toggles
NEG_WEIGHT_MODE = "abs"
# NEG_WEIGHT_MODE = "drop"
N_FOLDS = 3
SEED = 42
OUTPUT_DIR = "/eos/user/a/araghav/xgboost_ml-hep"
os.makedirs(OUTPUT_DIR, exist_ok=True)
limitFiles = -1  # -1 for all files, 1 for testing
# limitFiles = 1  

with open("configuration.py") as handles:
    exec(handles.read())

samples = {}
structure = {}
cuts = {}
for f in [samplesFile, structureFile, cutsFile]:
    with open(f) as handles:
        exec(handles.read())

aliases = {}
with open("aliases.py") as handles:
    exec(handles.read())
with open("preselections.py") as handles:
    exec(handles.read())

cut = preselections

#----------------------------------------------MVA variables

mvaVariables = [
    'Lepton_pt[1]',
    'ptll',
    'mll',
    'LowestQGLJet_pt1',
    'LowestQGLJet_mass1',
    'qgl_j1_lowestqgl',
    'mjj',
    'mjj_qgl',
    'detajj',
    'detajj_qgl',
    'drjj',
    'Alt(CleanJet_pt,0,0)',
    'Alt(CleanJet_pt,1,0)',
]

# ----------------------------------------------RDF helpers
def aliases_applies(sampleName, aliases):
    if 'samples' not in aliases:
        return True
    scope = aliases['samples']
    if isinstance(scope, str):
        return sampleName == scope
    return sampleName in scope

def make_valid_column_names(varnames):
    return  {v: re.sub(r'\W+', '_', v).strip('_') for v in varnames}

def resolve_variables(df, varnames, colmap):
    available = set(str(c) for c in df.GetColumnNames())
    for orig, safe in colmap.items():
        if orig == safe and orig in available:
            continue
        df = df.Define(safe, orig)
    return df

def required_aliases(sampleName, exprs):
    applicable = {n: a for n, a in aliases.items() if aliases_applies(sampleName, a)}
    needed, stack = set(), list(exprs)
    while stack:
        e = stack.pop()
        for tok in set(re.findall(r'[A-Za-z_]\w*', e)):
            if tok in applicable and tok not in needed:
                needed.add(tok)
                stack.append(applicable[tok]['expr'])
    return needed
 
def build_dataframe(sampleName, subentry_files, varnames, colmap, weight_expr):
    chain = ROOT.TChain("Events")
    for f in subentry_files:
        chain.Add(f)
    df = ROOT.RDataFrame(chain)
    existing_cols = set(str(c) for c in df.GetColumnNames())
    needed = required_aliases(sampleName, list(varnames) + [cut, weight_expr])
    print(f"  [{sampleName}] aliases used: {sorted(needed)}")
    for aliasName, alias in aliases.items():
        if aliasName in needed and aliasName not in existing_cols:
            df = df.Define(aliasName, alias['expr'])
    df = resolve_variables(df, varnames, colmap)
    return df.Filter(cut)

# ---------------------------------------------------------------- XGBoost configs
XGB_CONFIGS = {
    # "xgb_config_1": {
    #     "n_estimators": 100, "max_depth": 3,
    #     "learning_rate": 0.05008107160377287, "min_child_weight": 41,
    #     "gamma": 0.01864371812614296, "subsample": 0.5951099240132968,
    #     "colsample_bytree": 0.9111947557404338, "colsample_bynode": 0.9805630111435243,
    #     "reg_alpha": 0.03463365205516163, "reg_lambda": 2.84898057839644,
    # },
    "xgb_config_2": {
        "n_estimators": 200, "max_depth": 3,
        "learning_rate": 0.05008107160377287, "min_child_weight": 41,
        "gamma": 0.01864371812614296, "subsample": 0.5951099240132968,
        "colsample_bytree": 0.9111947557404338, "colsample_bynode": 0.9805630111435243,
        "reg_alpha": 0.03463365205516163, "reg_lambda": 2.84898057839644,
    },
    # "xgb_config_3": {
    #     "n_estimators": 300, "max_depth": 3,
    #     "learning_rate": 0.05008107160377287, "min_child_weight": 20,
    #     "subsample": 0.5951099240132968,
    #     "colsample_bytree": 0.9111947557404338, "colsample_bynode": 0.9805630111435243,
    #     "reg_alpha": 0.03463365205516163, "reg_lambda": 2.84898057839644,
    # },
}

# -------------------------------------------------------------- data training

def load_dataset():
    """Load all the MC events once, assign each event a fold id in [0, N_FOLDS-1] """
    colmap =make_valid_column_names(mvaVariables)
    rng = np.random.default_rng(SEED)
    Xs, ys, ws, folds = [], [], [], []

    for sampleName, subentries in samples.items():
        if structure[sampleName]['isData'] == 1:
            continue
        isSig = int(structure[sampleName]['isSignal'])
        print(f"Loading sample {sampleName}")

        for sub in subentries:
            tag, files, weight_expr = sub['tag'], sub['files'], sub['weight']
            if not files:
                print(f" [{tag}] -> 0 files, skipping")
                continue

            df = build_dataframe(sampleName, files, mvaVariables, colmap, weight_expr)
            df = df.Define("eventWeight", weight_expr)
            has_event = "event" in [str(c) for c in df.GetColumnNames()]
            # print(f" [{tag}] -> {df.Count().value} events")
            cols = list(colmap.values()) + ["eventWeight"]+(["event"] if has_event else [])
            data = df.AsNumpy(columns=cols)

            n = len(data["eventWeight"])
            if n == 0:
                print(f" [{tag}] -> 0 events after preselection, skipping")
                continue
            
            X = np.column_stack([data[colmap[v]] for v in mvaVariables])
            w = np.asarray(data["eventWeight"], dtype=np.float64)
            y = np.full(n, isSig, dtype=np.int32)

            # fold assignment: event number and k
            if has_event:
                fold = (np.asarray(data["event"]).astype(np.int64) % N_FOLDS).astype(np.int32)
            else:
                fold = rng.integers(0, N_FOLDS, size=n).astype(np.int32)

            # -------------Negative weight handling------------------------------------
            if NEG_WEIGHT_MODE == "abs":
                w = np.abs(w)
            elif NEG_WEIGHT_MODE == "drop":
                keep = w > 0
                X, y, w, fold = X[keep], y[keep], w[keep], fold[keep]
            else:
                raise ValueError(f"Unknown NEG_WEIGHT_MODE: {NEG_WEIGHT_MODE}")
            # --------------------------------------------------------------------------

            Xs.append(X)
            ys.append(y)
            ws.append(w)
            folds.append(fold)  
            print(f" [{tag}] -> {n} events, {np.sum(w)} weighted events, fold distribution: {np.bincount(fold)}")

    return (np.concatenate(Xs),
            np.concatenate(ys),
            np.concatenate(ws),
            np.concatenate(folds))

def normalize_class_weights(y, w):
    """Rescale so each class has total weight = number of events in that class."""
    w = w.copy()
    for cls in [0, 1]:
        m = y == cls
        tot = w[m].sum()
        if tot > 0:
            w[m] = w[m] / tot * m.sum()
    return w

 
# ---------------------------------------------------------------- main
def runJob():
    X, y, w, fold = load_dataset()
 
    print("\nDataset summary")
    print("----------------------------------------")
    print(f"Total events: {len(y)}  (signal {np.sum(y == 1)}, bkg {np.sum(y == 0)})")
    for k in range(N_FOLDS):
        m = fold == k
        print(f"  fold {k}: {m.sum():>9} events  (sig {np.sum(y[m] == 1)}, bkg {np.sum(y[m] == 0)})")
 
    np.savez(os.path.join(OUTPUT_DIR, f"xgb_Hgg_kfold{N_FOLDS}_dataset.npz"),
             X=X, y=y, w=w, fold=fold, mvaVariables=np.array(mvaVariables))
 
    results = {}
    for config_name, params in XGB_CONFIGS.items():
        print("\n" + "+" * 70)
        print(f"Config: {config_name}  ({N_FOLDS}-fold CV)")
 
        oof_scores = np.zeros(len(y))   # out-of-fold predictions (each event scored by the model that didn't train on it)
        train_aucs, test_aucs, importances = [], [], []
 
        for k in range(N_FOLDS):
            test_mask = fold == k
            train_mask = ~test_mask
 
            X_tr, y_tr, w_tr = X[train_mask], y[train_mask], w[train_mask]
            X_te, y_te, w_te = X[test_mask], y[test_mask], w[test_mask]
 
            clf = XGBClassifier(**params, eval_metric="logloss")
            clf.fit(X_tr, y_tr, sample_weight=normalize_class_weights(y_tr, w_tr))
 
            s_tr = clf.predict_proba(X_tr)[:, 1]
            s_te = clf.predict_proba(X_te)[:, 1]
            oof_scores[test_mask] = s_te
 
            tr_auc = roc_auc_score(y_tr, s_tr, sample_weight=w_tr)
            te_auc = roc_auc_score(y_te, s_te, sample_weight=w_te)
            train_aucs.append(tr_auc)
            test_aucs.append(te_auc)
            importances.append(clf.feature_importances_)
 
            print(f"  fold {k}: train AUC {tr_auc:.4f} | test AUC {te_auc:.4f} | diff {tr_auc - te_auc:.4f}")
 
            with open(os.path.join(OUTPUT_DIR, f"xgb_Hgg_{config_name}_kfold{N_FOLDS}_fold{k}.pkl"), "wb") as f:
                pickle.dump(clf, f)
            del clf
 
        train_aucs, test_aucs = np.array(train_aucs), np.array(test_aucs)
        mean_imp = np.mean(importances, axis=0)
        oof_auc = roc_auc_score(y, oof_scores, sample_weight=w)
 
        results[config_name] = dict(
            params=params,
            train_mean=train_aucs.mean(), train_std=train_aucs.std(ddof=1),
            test_mean=test_aucs.mean(), test_std=test_aucs.std(ddof=1),
            oof_auc=oof_auc,
        )
 
        np.savez(os.path.join(OUTPUT_DIR, f"xgb_Hgg_scores_{config_name}_kfold{N_FOLDS}.npz"),
                 oof_scores=oof_scores, y=y, w=w, fold=fold,
                 train_aucs=train_aucs, test_aucs=test_aucs, oof_auc=oof_auc,
                 feature_importances=np.array(importances),
                 feature_names=np.array(mvaVariables))
 
        print(f"\nVariable importance (mean over folds): {config_name}")
        for rank, (var, imp) in enumerate(
                sorted(zip(mvaVariables, mean_imp), key=lambda x: x[1], reverse=True), start=1):
            print(f"{rank:2d} : {var:<25} {imp:.4f}")
 
    # summary
    print("\n" + "=" * 100)
    print(f"{N_FOLDS}-fold CV summary")
    print("=" * 100)
    print(f"{'Config':<16}{'Depth':>6}{'Trees':>7}{'LR':>8}{'MCW':>6}"
          f"{'Train AUC':>20}{'Test AUC':>20}{'OOF AUC':>10}{'Diff':>8}")
    print("-" * 100)
    for name, r in results.items():
        p = r["params"]
        print(f"{name:<16}{p['max_depth']:>6}{p['n_estimators']:>7}{p['learning_rate']:>8.3f}"
              f"{p['min_child_weight']:>6}"
              f"{r['train_mean']:>12.4f} ±{r['train_std']:.4f}"
              f"{r['test_mean']:>12.4f} ±{r['test_std']:.4f}"
              f"{r['oof_auc']:>10.4f}{r['train_mean'] - r['test_mean']:>8.4f}")
 
 
if __name__ == "__main__":
    runJob()