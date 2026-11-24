#!/usr/bin/env python
import os
import re
import csv
import glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import xgboost as xgb
from scipy.stats import kstwobign
from sklearn.metrics import roc_curve, roc_auc_score

N_FOLDS = 10   # must match the training script
INPUT_DIR = "/eos/user/a/araghav/xgboost_ml-hep"
OUTPUT_DIR = "/eos/user/a/araghav/www/BDT/plots_bdt_xgboost"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ------------------------------------------------------------------ inputs
DATASET_FILE = os.path.join(INPUT_DIR, f"xgb_Hgg_kfold{N_FOLDS}_dataset.npz")
if not os.path.exists(DATASET_FILE):
    raise RuntimeError(f"Dataset file not found: {DATASET_FILE}")

dset = np.load(DATASET_FILE, allow_pickle=True)
X, y, w, fold = dset["X"], dset["y"], dset["w"], dset["fold"]   # w = raw physical weights
varnames = [str(v) for v in dset["mvaVariables"]]
X32 = X.astype(np.float32)
print(f"Loaded {len(y)} events, {len(varnames)} variables, {N_FOLDS} folds")

npz_files = sorted(glob.glob(os.path.join(INPUT_DIR, f"xgb_Hgg_scores_*_kfold{N_FOLDS}.npz")))
if not npz_files:
    raise RuntimeError(f"No score files found in {INPUT_DIR}")


def config_name_from_path(path):
    m = re.match(rf"xgb_Hgg_scores_(.+)_kfold{N_FOLDS}\.npz$", os.path.basename(path))
    return m.group(1) if m else os.path.basename(path)


configs = {config_name_from_path(f): f for f in npz_files}
print(f"Found {len(configs)} configurations: {list(configs.keys())}")


# ------------------------------------------------------------------ helpers
def weighted_ecdf(values, weights, eval_points):
    order = np.argsort(values)
    values_sorted = values[order]
    cum_w = np.cumsum(weights[order])
    cum_w /= cum_w[-1]
    idx = np.searchsorted(values_sorted, eval_points, side="right") - 1
    return np.where(idx >= 0, cum_w[np.clip(idx, 0, len(cum_w) - 1)], 0.0)


def weighted_ks_2samp(x1, w1, x2, w2):
    x_all = np.sort(np.concatenate([x1, x2]))
    ks_stat = np.max(np.abs(weighted_ecdf(x1, w1, x_all) - weighted_ecdf(x2, w2, x_all)))
    n1_eff = w1.sum() ** 2 / np.sum(w1 ** 2)
    n2_eff = w2.sum() ** 2 / np.sum(w2 ** 2)
    n_e = n1_eff * n2_eff / (n1_eff + n2_eff)
    return ks_stat, kstwobign.sf(ks_stat * np.sqrt(n_e))


def weighted_hist_with_err(values, weights, bins):
    hist, _ = np.histogram(values, bins=bins, weights=weights, density=True)
    sumw, _ = np.histogram(values, bins=bins, weights=weights)
    sumw2, _ = np.histogram(values, bins=bins, weights=weights ** 2)
    n_eff = np.divide(sumw ** 2, sumw2, out=np.zeros_like(sumw), where=sumw2 > 0)
    n_eff = np.clip(n_eff, 1, None)
    return hist, hist / np.sqrt(n_eff)


def plot_correlation(X, y, weights, label):
    n = len(varnames)
    for cls, name in [(1, "signal"), (0, "background")]:
        mask = y == cls
        Xc, wc = X[mask], weights[mask]
        avg = np.average(Xc, axis=0, weights=wc)
        Xc_c = Xc - avg
        cov = np.einsum('i,ij,ik->jk', wc, Xc_c, Xc_c) / wc.sum()
        std = np.sqrt(np.diag(cov))
        corr = cov / np.outer(std, std)

        size = max(6, n * 0.7)
        fig, ax = plt.subplots(figsize=(size, size))
        im = ax.imshow(corr, vmin=-1, vmax=1, cmap="RdBu_r")
        fig.colorbar(im, ax=ax, label="Correlation", fraction=0.046, pad=0.04)
        ax.set_xticks(range(n)); ax.set_xticklabels(varnames, rotation=90, fontsize=8)
        ax.set_yticks(range(n)); ax.set_yticklabels(varnames, fontsize=8)
        for i in range(n):
            for j in range(n):
                ax.text(j, i, f"{corr[i, j]:.2f}", ha="center", va="center", fontsize=6,
                        color="black" if abs(corr[i, j]) < 0.7 else "white")
        ax.set_title(f"Correlation matrix ({name}, {label})", pad=20)
        fig.tight_layout()
        fig.savefig(os.path.join(OUTPUT_DIR, f"corr_{name}_{label}.png"), dpi=150)
        plt.close(fig)


def fold_train_scores(config, k):
    """Reload fold-k model from JSON and score the events it was trained on (fold != k)."""
    path = os.path.join(INPUT_DIR, f"xgb_Hgg_{config}_kfold{N_FOLDS}_fold{k}.json")
    booster = xgb.Booster()
    booster.load_model(path)
    m = fold != k
    return m, booster.predict(xgb.DMatrix(X32[m]))


# ------------------------------------------------------------------ input variables + correlations
plot_correlation(X, y, w, "all")

for i, var in enumerate(varnames):
    plt.figure()
    lo, hi = np.percentile(X[:, i], [1, 99])
    bins = np.linspace(lo, hi, 40)
    for cls, label, color in [(1, "Signal", "blue"), (0, "Background", "red")]:
        plt.hist(X[y == cls, i], bins=bins, weights=w[y == cls], density=True,
                 histtype="step", label=label, color=color)
    plt.xlabel(var)
    plt.ylabel("Normalized events")
    plt.legend()
    plt.title(f"{var}: signal vs background")
    safe_var = re.sub(r"\W+", "_", var).strip("_")
    plt.savefig(os.path.join(OUTPUT_DIR, f"var_{safe_var}.png"), dpi=150)
    plt.close()

# ------------------------------------------------------------------ per config
score_bins = np.linspace(0, 1, 41)
bin_centers = 0.5 * (score_bins[:-1] + score_bins[1:])

roc_results = {}
importance_results = {}   # config -> (mean over folds, std over folds)
ks_summary = []
auc_summary = []

for name in sorted(configs):
    d = np.load(configs[name], allow_pickle=True)
    oof = d["oof_scores"]
    train_aucs, test_aucs = d["train_aucs"], d["test_aucs"]
    auc_summary.append(dict(config=name,
                            train_mean=train_aucs.mean(), train_std=train_aucs.std(ddof=1),
                            test_mean=test_aucs.mean(), test_std=test_aucs.std(ddof=1),
                            oof=float(d["oof_auc"])))

    # ---- feature importance: mean +/- std over folds
    imp_folds = np.asarray(d["feature_importances"], dtype=float)   # (n_folds, n_vars)
    fnames = [str(v) for v in d["feature_names"]]
    imp_mean, imp_std = imp_folds.mean(axis=0), imp_folds.std(axis=0, ddof=1)
    importance_results[name] = dict(zip(fnames, zip(imp_mean, imp_std)))

    order = np.argsort(imp_mean)
    fig, ax = plt.subplots(figsize=(7, max(4, 0.3 * len(fnames))))
    ax.barh(np.array(fnames)[order], imp_mean[order], xerr=imp_std[order],
            color="steelblue", ecolor="black", capsize=2)
    ax.set_xlabel("Feature importance (mean ± std over folds)")
    ax.set_title(f"Variable importance: {name}")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, f"feature_importance_{name}.png"), dpi=150)
    plt.close(fig)

    # ---- ROC on out-of-fold scores (every event scored by a model that did not train on it)
    fpr, tpr, _ = roc_curve(y, oof, sample_weight=w)
    auc = roc_auc_score(y, oof, sample_weight=w)
    roc_results[name] = (fpr, tpr, auc, test_aucs.mean(), test_aucs.std(ddof=1))

    # ---- overtraining check: pooled train vs out-of-fold test, KS per fold
    tr_scores, tr_y, tr_w = [], [], []
    ks_rows = {1: [], 0: []}
    for k in range(N_FOLDS):
        m_tr, s_tr_k = fold_train_scores(name, k)
        m_te = fold == k
        tr_scores.append(s_tr_k); tr_y.append(y[m_tr]); tr_w.append(w[m_tr])
        for cls in (1, 0):
            a, b = tr_y[-1] == cls, y[m_te] == cls
            ks_rows[cls].append(weighted_ks_2samp(s_tr_k[a], tr_w[-1][a],
                                                  oof[m_te][b], w[m_te][b]))
    tr_scores = np.concatenate(tr_scores); tr_y = np.concatenate(tr_y); tr_w = np.concatenate(tr_w)

    plt.figure(figsize=(7, 6))
    row = {"config": name}
    for cls, label, color in [(1, "Signal", "blue"), (0, "Background", "red")]:
        a, b = tr_y == cls, y == cls
        plt.hist(tr_scores[a], bins=score_bins, weights=tr_w[a], density=True,
                 histtype="stepfilled", alpha=0.3, color=color, label=f"{label} (train, pooled)")
        test_hist, err = weighted_hist_with_err(oof[b], w[b], score_bins)
        plt.errorbar(bin_centers, test_hist, yerr=err, fmt="o", color=color,
                     markersize=4, label=f"{label} (test, out-of-fold)")
        ks = np.array(ks_rows[cls])      # (n_folds, 2): ks, p
        row[f"ks_{label.lower()}"] = ks[:, 0].mean()
        row[f"pmin_{label.lower()}"] = ks[:, 1].min()
    ks_summary.append(row)

    text = "\n".join([
        f"KS (Signal): mean {row['ks_signal']:.3f}, min p={row['pmin_signal']:.3f}",
        f"KS (Background): mean {row['ks_background']:.3f}, min p={row['pmin_background']:.3f}",
        f"(KS computed per fold, {N_FOLDS} folds)",
    ])
    plt.gca().text(0.02, 0.98, text, transform=plt.gca().transAxes, verticalalignment="top",
                   fontsize=8, bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))
    plt.xlabel("BDT score")
    plt.ylabel("Normalized events")
    plt.title(f"Overtraining check: {name}")
    plt.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), borderaxespad=0)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f"overtraining_check_{name}.png"), dpi=150)
    plt.close()

# ------------------------------------------------------------------ combined ROC
ordered = sorted(roc_results.items(), key=lambda kv: kv[1][2], reverse=True)
cmap = plt.get_cmap("tab20")
plt.figure(figsize=(8, 7))
for i, (name, (fpr, tpr, auc, te_m, te_s)) in enumerate(ordered):
    plt.plot(tpr, 1 - fpr, color=cmap(i % 20),
             label=f"{name} (OOF AUC={auc:.4f}, fold AUC={te_m:.4f}±{te_s:.4f})")
plt.xlabel("Signal efficiency")
plt.ylabel("Background rejection")
plt.title(f"ROC curve (out-of-fold, {N_FOLDS}-fold): all configurations")
plt.legend(loc="lower left", fontsize=7)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "roc_curve_all_configs.png"), dpi=150)
plt.close()

# ------------------------------------------------------------------ combined feature importance
all_vars = sorted({v for r in importance_results.values() for v in r})
mat = np.array([[r[v][0] if v in r else np.nan for v in all_vars] for r in importance_results.values()])
mean, std = np.nanmean(mat, axis=0), np.nanstd(mat, axis=0)
order = np.argsort(mean)
fig, ax = plt.subplots(figsize=(8, max(4, 0.3 * len(all_vars))))
ax.barh(np.array(all_vars)[order], mean[order], xerr=std[order],
        color="steelblue", ecolor="black", capsize=2)
ax.set_xlabel("Feature importance (fold-mean, mean ± std over configs)")
ax.set_title("Variable importance: all configurations")
fig.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "feature_importance_all_configs.png"), dpi=150)
plt.close(fig)

cfgs = list(importance_results.keys())
with open(os.path.join(OUTPUT_DIR, "feature_importance.csv"), "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["variable"] + [f"{c}_mean" for c in cfgs] + [f"{c}_std" for c in cfgs])
    for v in all_vars:
        writer.writerow([v]
                        + [importance_results[c][v][0] if v in importance_results[c] else "" for c in cfgs]
                        + [importance_results[c][v][1] if v in importance_results[c] else "" for c in cfgs])

# ------------------------------------------------------------------ summaries
print(f"\n--- {N_FOLDS}-fold AUC summary (weighted) ---")
header = f"{'Config':<20}{'Train AUC':>20}{'Test AUC':>20}{'OOF AUC':>10}{'Diff':>8}"
print(header); print("-" * len(header))
for r in auc_summary:
    print(f"{r['config']:<20}{r['train_mean']:>12.4f} ±{r['train_std']:.4f}"
          f"{r['test_mean']:>12.4f} ±{r['test_std']:.4f}{r['oof']:>10.4f}"
          f"{r['train_mean'] - r['test_mean']:>8.4f}")

# Bonferroni-style threshold: 2 classes x N_FOLDS KS tests per config
p_thr = 0.05 / (2 * N_FOLDS)
print(f"\n--- KS test summary (weighted, per fold; flag if min p < {p_thr:.4f}) ---")
header = f"{'Config':<20}{'KS(sig)':>10}{'minp(sig)':>11}{'KS(bkg)':>10}{'minp(bkg)':>11}  Verdict"
print(header); print("-" * len(header))
for row in sorted(ks_summary, key=lambda r: r["config"]):
    worst_p = min(row["pmin_signal"], row["pmin_background"])
    verdict = "OK" if worst_p > p_thr else "WARNING: possible overtraining"
    print(f"{row['config']:<20}{row['ks_signal']:>10.4f}{row['pmin_signal']:>11.4f}"
          f"{row['ks_background']:>10.4f}{row['pmin_background']:>11.4f}  {verdict}")

with open(os.path.join(OUTPUT_DIR, "ks_summary.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["config", "ks_signal", "pmin_signal",
                                           "ks_background", "pmin_background"])
    writer.writeheader()
    for row in sorted(ks_summary, key=lambda r: r["config"]):
        writer.writerow(row)

print("\nSaved: correlation matrices, per-variable plots, roc_curve_all_configs.png, "
      "per-config overtraining and importance plots, feature_importance.csv, ks_summary.csv.")