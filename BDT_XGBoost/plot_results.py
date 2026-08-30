#!/usr/bin/env python
import os
import re
import csv
import glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import kstwobign
from sklearn.metrics import roc_curve, roc_auc_score

INPUT_DIR = "/eos/user/a/araghav/xgb_outputs"
OUTPUT_DIR = "/eos/user/a/araghav/www/BDT/plots_bdt_xgboost"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DATASET_FILE = os.path.join(INPUT_DIR, "xgb_Hgg_dataset.npz")
if not os.path.exists(DATASET_FILE):
    raise RuntimeError(f"Shared dataset file not found: {DATASET_FILE}")

dset = np.load(DATASET_FILE, allow_pickle=True)
X_train, y_train, w_train = dset["X_train"], dset["y_train"], dset["w_train"]
X_test, y_test, w_test = dset["X_test"], dset["y_test"], dset["w_test"]
varnames = list(dset["mvaVariables"])

npz_files = sorted(glob.glob(os.path.join(INPUT_DIR, "xgb_Hgg_scores_*.npz")))
if not npz_files:
    raise RuntimeError(f"No score files found in {INPUT_DIR}")


def config_name_from_path(path):
    m = re.match(r"xgb_Hgg_scores_(.+)\.npz$", os.path.basename(path))
    return m.group(1) if m else os.path.basename(path)


configs = {config_name_from_path(f): f for f in npz_files}
print(f"Found {len(configs)} configurations: {list(configs.keys())}")


def weighted_ecdf(values, weights, eval_points):
    order = np.argsort(values)
    values_sorted = values[order]
    weights_sorted = weights[order]
    cum_w = np.cumsum(weights_sorted)
    cum_w /= cum_w[-1]
    idx = np.searchsorted(values_sorted, eval_points, side="right") - 1
    return np.where(idx >= 0, cum_w[np.clip(idx, 0, len(cum_w) - 1)], 0.0)


def weighted_ks_2samp(x1, w1, x2, w2):
    x_all = np.sort(np.concatenate([x1, x2]))
    cdf1 = weighted_ecdf(x1, w1, x_all)
    cdf2 = weighted_ecdf(x2, w2, x_all)
    ks_stat = np.max(np.abs(cdf1 - cdf2))

    n1_eff = w1.sum() ** 2 / np.sum(w1 ** 2)
    n2_eff = w2.sum() ** 2 / np.sum(w2 ** 2)
    n_e = n1_eff * n2_eff / (n1_eff + n2_eff)
    p = kstwobign.sf(ks_stat * np.sqrt(n_e))
    return ks_stat, p


def weighted_hist_with_err(values, weights, bins):
    hist, _ = np.histogram(values, bins=bins, weights=weights, density=True)
    sumw, _ = np.histogram(values, bins=bins, weights=weights)
    sumw2, _ = np.histogram(values, bins=bins, weights=weights ** 2)
    n_eff = np.divide(sumw ** 2, sumw2, out=np.zeros_like(sumw), where=sumw2 > 0)
    n_eff = np.clip(n_eff, 1, None)
    err = hist / np.sqrt(n_eff)
    return hist, err


def plot_correlation(X, y, label, weights):
    n = len(varnames)
    for cls, name in [(1, "signal"), (0, "background")]:
        mask = y == cls
        Xc = X[mask]
        wc = weights[mask]
        avg = np.average(Xc, axis=0, weights=wc)
        Xc_c = Xc - avg
        cov = np.einsum('i,ij,ik->jk', wc, Xc_c, Xc_c) / wc.sum()
        std = np.sqrt(np.diag(cov))
        corr = cov / np.outer(std, std)

        size = max(6, n * 0.7)
        fig, ax = plt.subplots(figsize=(size, size))
        im = ax.imshow(corr, vmin=-1, vmax=1, cmap="RdBu_r")
        fig.colorbar(im, ax=ax, label="Correlation", fraction=0.046, pad=0.04)
        ax.set_xticks(range(n))
        ax.set_xticklabels(varnames, rotation=90, fontsize=8)
        ax.set_yticks(range(n))
        ax.set_yticklabels(varnames, fontsize=8)
        for i in range(n):
            for j in range(n):
                ax.text(j, i, f"{corr[i, j]:.2f}", ha="center", va="center",
                         fontsize=6, color="black" if abs(corr[i, j]) < 0.7 else "white")
        ax.set_title(f"Correlation matrix ({name}, {label})", pad=20)
        fig.tight_layout()
        fig.savefig(os.path.join(OUTPUT_DIR, f"corr_{name}_{label}.png"), dpi=150)
        plt.close(fig)


plot_correlation(X_train, y_train, "train", w_train)

for i, var in enumerate(varnames):
    plt.figure()
    lo, hi = np.percentile(X_train[:, i], [1, 99])
    bins = np.linspace(lo, hi, 40)
    plt.hist(X_train[y_train == 1, i], bins=bins, weights=w_train[y_train == 1],
              density=True, histtype="step", label="Signal", color="blue")
    plt.hist(X_train[y_train == 0, i], bins=bins, weights=w_train[y_train == 0],
              density=True, histtype="step", label="Background", color="red")
    plt.xlabel(var)
    plt.ylabel("Normalized events")
    plt.legend()
    plt.title(f"{var}: signal vs background")
    safe_var = var.replace("[", "_").replace("]", "")
    plt.savefig(os.path.join(OUTPUT_DIR, f"var_{safe_var}.png"), dpi=150)
    plt.close()

score_bins = np.linspace(0, 1, 41)
bin_centers = 0.5 * (score_bins[:-1] + score_bins[1:])

roc_results = {}     
ks_summary = []      

for name in sorted(configs):
    d = np.load(configs[name], allow_pickle=True)
    s_tr, s_te = d["train_scores"], d["test_scores"]

    # ROC (test set) 
    fpr, tpr, _ = roc_curve(y_test, s_te, sample_weight=w_test)
    auc = roc_auc_score(y_test, s_te, sample_weight=w_test)
    roc_results[name] = (fpr, tpr, auc)

    plt.figure(figsize=(7, 6))
    row = {"config": name}
    for cls, label, color in [(1, "Signal", "blue"), (0, "Background", "red")]:
        tr_mask = y_train == cls
        te_mask = y_test == cls

        plt.hist(s_tr[tr_mask], bins=score_bins, weights=w_train[tr_mask],
                  density=True, histtype="stepfilled", alpha=0.3, color=color,
                  label=f"{label} (train)")

        test_hist, err = weighted_hist_with_err(s_te[te_mask], w_test[te_mask], score_bins)
        plt.errorbar(bin_centers, test_hist, yerr=err, fmt="o", color=color,
                     markersize=4, label=f"{label} (test)")

        ks_stat, ks_p = weighted_ks_2samp(s_tr[tr_mask], w_train[tr_mask], s_te[te_mask], w_test[te_mask])
        row[f"ks_{label.lower()}"] = ks_stat
        row[f"p_{label.lower()}"] = ks_p

    ks_summary.append(row)

    text = "\n".join([
        f"KS (Signal): {row['ks_signal']:.3f} (p={row['p_signal']:.3f})",
        f"KS (Background): {row['ks_background']:.3f} (p={row['p_background']:.3f})",
    ])
    plt.gca().text(0.02, 0.98, text, transform=plt.gca().transAxes,
                    verticalalignment="top", fontsize=9,
                    bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))
    plt.xlabel("BDT score")
    plt.ylabel("Normalized events")
    plt.title(f"Overtraining check: {name}")
    plt.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), borderaxespad=0)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f"overtraining_check_{name}.png"), dpi=150)
    plt.close()

# Combined ROC curve
ordered = sorted(roc_results.items(), key=lambda kv: kv[1][2], reverse=True)
cmap = plt.get_cmap("tab20")

plt.figure(figsize=(8, 7))
for i, (name, (fpr, tpr, auc)) in enumerate(ordered):
    plt.plot(tpr, 1 - fpr, color=cmap(i % 20), label=f"{name} (AUC={auc:.3f})")
plt.xlabel("Signal efficiency")
plt.ylabel("Background rejection")
plt.title("ROC curve: all configurations")
plt.legend(loc="lower left", fontsize=7)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "roc_curve_all_configs.png"), dpi=150)
plt.close()

# KS summary table
print("\n--- KS test summary (weighted, all configs) ---")
header = f"{'Config':<20}{'KS(sig)':>10}{'p(sig)':>10}{'KS(bkg)':>10}{'p(bkg)':>10}  Verdict"
print(header)
print("-" * len(header))
for row in sorted(ks_summary, key=lambda r: r["config"]):
    worst_p = min(row["p_signal"], row["p_background"])
    verdict = "OK" if worst_p > 0.01 else "WARNING: possible overtraining"
    print(f"{row['config']:<20}{row['ks_signal']:>10.4f}{row['p_signal']:>10.4f}"
          f"{row['ks_background']:>10.4f}{row['p_background']:>10.4f}  {verdict}")

csv_path = os.path.join(OUTPUT_DIR, "ks_summary.csv")
with open(csv_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["config", "ks_signal", "p_signal", "ks_background", "p_background"])
    writer.writeheader()
    for row in sorted(ks_summary, key=lambda r: r["config"]):
        writer.writerow(row)

print(f"\nSaved: correlation matrices, roc_curve_all_configs.png, "
      f"per-config overtraining plots, ks_summary.csv, per-variable plots.")
print("Go to: https://araghav.web.cern.ch/?dir=BDT%2Fplots_bdt_xgboost")