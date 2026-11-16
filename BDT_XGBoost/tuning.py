#!/usr/bin/env python
"""
xgb_tune_v2.py -- TPE tuning of the XGBoost BDT, overtraining-aware.

Changes vs xgb_tune.py
  1. No early stopping inside CV: n_estimators is a tuned parameter, so the
     validation-fold score is unbiased.
  2. Loss = -(mean val AUC - K_STD*std over folds) + gap penalty,
     with 5-fold CV -> rejects settings that only work on a lucky fold.
  3. Search space restricted to simpler models (shallow, high min_child_weight).
  4. Optional partial AUC (high-purity region) instead of full AUC.
  5. Optional clipping of extreme training weights.
  6. After the search: retrain best params with several seeds and report
     train/test AUC and train-vs-test KS (signal, background separately).
     The test half is used ONLY here, once, after tuning is finished.
"""
import os
import json
import pickle
import numpy as np
from hyperopt import STATUS_OK, Trials, fmin, hp, tpe
from scipy.stats import ks_2samp
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from xgboost import XGBClassifier

# ---------------- settings ----------------
OUTPUT_DIR = os.environ.get("XGB_OUT", "/eos/user/a/araghav/xgboost/outputs_ml-hep")
DATASET = os.path.join(OUTPUT_DIR, "xgb_Hgg_tuning.npz")
MAX_EVALS = int(os.environ.get("XGB_EVALS", 80))
N_SPLITS = 5
SEED = 0
K_STD = 1.0            # penalise fold-to-fold spread
GAP_TOL = 0.02         # tolerated train-val AUC gap
GAP_PENALTY = 2.0
MAX_FPR = None         # e.g. 0.1 for partial AUC in the high-purity region; None = full AUC
CLIP_PCT = 99.9        # clip training weights per class at this percentile; None = off
N_FINAL_SEEDS = 5
N_JOBS = 4
# ------------------------------------------

d = np.load(DATASET, allow_pickle=True)
X, y, w = d["X_train"], d["y_train"].astype(int), d["w_train"]
X_te, y_te, w_te = d["X_test"], d["y_test"].astype(int), d["w_test"]

# class-normalised training weights (same as xgb_train.py), optional clipping first
w_norm = w.copy()
for cls in (0, 1):
    m = y == cls
    if CLIP_PCT is not None:
        w_norm[m] = np.minimum(w_norm[m], np.percentile(w_norm[m], CLIP_PCT))
    if w_norm[m].sum() > 0:
        w_norm[m] = w_norm[m] / w_norm[m].sum() * m.sum()

print(f"Tuning on {len(y)} events (sig {np.sum(y==1)}, bkg {np.sum(y==0)}), "
      f"{N_SPLITS}-fold CV, {MAX_EVALS} trials")


def auc(yy, s, ww):
    return roc_auc_score(yy, s, sample_weight=ww, max_fpr=MAX_FPR)


space = {
    "max_depth":        hp.quniform("max_depth", 2, 6, 1),
    "n_estimators":     hp.quniform("n_estimators", 50, 600, 25),
    "learning_rate":    hp.loguniform("learning_rate", np.log(0.01), np.log(0.2)),
    "min_child_weight": hp.quniform("min_child_weight", 5, 50, 1),
    "gamma":            hp.uniform("gamma", 0, 5),
    "subsample":        hp.uniform("subsample", 0.5, 1.0),
    "colsample_bytree": hp.uniform("colsample_bytree", 0.4, 1.0),
    "colsample_bynode": hp.uniform("colsample_bynode", 0.5, 1.0),
    "reg_alpha":        hp.loguniform("reg_alpha", np.log(1e-3), np.log(10)),
    "reg_lambda":       hp.loguniform("reg_lambda", np.log(0.5), np.log(30)),
}


def make_model(p, seed=SEED):
    return XGBClassifier(
        n_estimators=int(p["n_estimators"]),
        max_depth=int(p["max_depth"]),
        learning_rate=float(p["learning_rate"]),
        min_child_weight=int(p["min_child_weight"]),
        gamma=float(p["gamma"]),
        subsample=float(p["subsample"]),
        colsample_bytree=float(p["colsample_bytree"]),
        colsample_bynode=float(p["colsample_bynode"]),
        reg_alpha=float(p["reg_alpha"]),
        reg_lambda=float(p["reg_lambda"]),
        tree_method="hist",
        eval_metric="logloss",
        random_state=seed,
        n_jobs=N_JOBS,
    )


skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)
counter = {"i": 0}


def objective(p):
    va_l, tr_l = [], []
    for tr, va in skf.split(X, y):
        clf = make_model(p)
        clf.fit(X[tr], y[tr], sample_weight=w_norm[tr])
        tr_l.append(auc(y[tr], clf.predict_proba(X[tr])[:, 1], w_norm[tr]))
        va_l.append(auc(y[va], clf.predict_proba(X[va])[:, 1], w_norm[va]))

    val, std, trn = np.mean(va_l), np.std(va_l), np.mean(tr_l)
    gap = trn - val
    loss = -(val - K_STD * std) + GAP_PENALTY * max(0.0, gap - GAP_TOL)

    counter["i"] += 1
    print(f"[{counter['i']:3d}] val {val:.4f} +- {std:.4f}  train {trn:.4f}  "
          f"gap {gap:.4f}  loss {loss:.4f}")
    return {"loss": loss, "status": STATUS_OK, "val_auc": val,
            "val_std": std, "train_auc": trn}


trials = Trials()
fmin(fn=objective, space=space, algo=tpe.suggest, max_evals=MAX_EVALS,
     trials=trials, rstate=np.random.default_rng(SEED))

# ---------- best parameters ----------
bt = trials.best_trial
v = {k: x[0] for k, x in bt["misc"]["vals"].items()}
best = {
    "n_estimators": int(v["n_estimators"]),
    "max_depth": int(v["max_depth"]),
    "learning_rate": float(v["learning_rate"]),
    "min_child_weight": int(v["min_child_weight"]),
    "gamma": float(v["gamma"]),
    "subsample": float(v["subsample"]),
    "colsample_bytree": float(v["colsample_bytree"]),
    "colsample_bynode": float(v["colsample_bynode"]),
    "reg_alpha": float(v["reg_alpha"]),
    "reg_lambda": float(v["reg_lambda"]),
}
r = bt["result"]
print(f"\nBest CV: val AUC {r['val_auc']:.4f} +- {r['val_std']:.4f}, "
      f"train AUC {r['train_auc']:.4f}")
print(json.dumps(best, indent=4))

print(f"\nFinal retrain on full train half, {N_FINAL_SEEDS} seeds")
te_aucs, tr_aucs, ks_sig, ks_bkg = [], [], [], []
for s in range(N_FINAL_SEEDS):
    clf = make_model(best, seed=SEED + s)
    clf.fit(X, y, sample_weight=w_norm)
    s_tr, s_te = clf.predict_proba(X)[:, 1], clf.predict_proba(X_te)[:, 1]
    tr_aucs.append(auc(y, s_tr, w))
    te_aucs.append(auc(y_te, s_te, w_te))
    ks_sig.append(ks_2samp(s_tr[y == 1], s_te[y_te == 1]).pvalue)
    ks_bkg.append(ks_2samp(s_tr[y == 0], s_te[y_te == 0]).pvalue)

print(f"Train AUC: {np.mean(tr_aucs):.4f} +- {np.std(tr_aucs):.4f}")
print(f"Test  AUC: {np.mean(te_aucs):.4f} +- {np.std(te_aucs):.4f}")
print(f"Gap      : {np.mean(tr_aucs) - np.mean(te_aucs):.4f}")
print(f"KS p-value train vs test  signal: {np.mean(ks_sig):.3f}  "
      f"background: {np.mean(ks_bkg):.3f}  (small p => overtraining)")

with open(os.path.join(OUTPUT_DIR, "xgb_best_params_v2.json"), "w") as f:
    json.dump(best, f, indent=4)
with open(os.path.join(OUTPUT_DIR, "xgb_hyperopt_trials_v2.pkl"), "wb") as f:
    pickle.dump(trials, f)