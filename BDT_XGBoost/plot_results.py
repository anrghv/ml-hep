#!/usr/bin/env python
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import ks_2samp
from sklearn.metrics import roc_curve, roc_auc_score

data = np.load("xgb_Hgg_scores.npz", allow_pickle=True)
y_train, train_scores, w_train, X_train = data["y_train"], data["train_scores"], data["w_train"], data["X_train"]
y_test, test_scores, w_test, X_test = data["y_test"], data["test_scores"], data["w_test"], data["X_test"]
varnames = list(data["mvaVariables"])

# Correlation matrices 
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

        # scale figure size with the number of variables
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
                # skip text if the cell is too small to read anyway, or
                # just shrink it -- shrinking is usually enough
                ax.text(j, i, f"{corr[i, j]:.2f}", ha="center", va="center",
                         fontsize=6, color="black" if abs(corr[i, j]) < 0.7 else "white")

        ax.set_title(f"Correlation matrix ({name}, {label})", pad=20)
        fig.tight_layout()
        fig.savefig(
            f"/eos/user/a/araghav/www/BDT/plots_bdt_xgboost/corr_{name}_{label}.png",
            dpi=150
        )
        plt.close(fig)

plot_correlation(X_train, y_train, "train", w_train)

# Overtraining check plot
plt.figure(figsize=(7, 6))
bins = np.linspace(0, 1, 41)
bin_centers = 0.5 * (bins[:-1] + bins[1:])

ks_results = {}

for cls, name, color in [(1, "Signal", "blue"), (0, "Background", "red")]:
    train_mask = y_train == cls
    test_mask = y_test == cls

    # filled histogram = train
    plt.hist(train_scores[train_mask], bins=bins, weights=w_train[train_mask],
              density=True, histtype="stepfilled", alpha=0.3, color=color,
              label=f"{name} (train)")

    # points with error bars = test
    test_hist, _ = np.histogram(test_scores[test_mask], bins=bins,
                                  weights=w_test[test_mask], density=True)
    test_hist_raw, _ = np.histogram(test_scores[test_mask], bins=bins)
    # simple sqrt(N) scaled error, approximate
    bin_width = bins[1] - bins[0]
    n_eff = test_hist_raw.clip(min=1)
    err = test_hist / np.sqrt(n_eff)
    plt.errorbar(bin_centers, test_hist, yerr=err, fmt="o", color=color,
                 markersize=4, label=f"{name} (test)")

    ks_stat, ks_p = ks_2samp(train_scores[train_mask], test_scores[test_mask])
    ks_results[name] = (ks_stat, ks_p)

# annotate KS results directly on the plot 
text = "\n".join([f"KS ({name}): {stat:.3f}  (p={p:.3f})"
                   for name, (stat, p) in ks_results.items()])
plt.gca().text(0.02, 0.98, text, transform=plt.gca().transAxes,
                verticalalignment="top", fontsize=9,
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

plt.xlabel("BDT score")
plt.ylabel("Normalized events")
plt.title("Overtraining check: train vs test")
plt.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), borderaxespad=0)
plt.tight_layout()
plt.savefig("/eos/user/a/araghav/www/BDT/plots_bdt_xgboost/overtraining_check.png", dpi=150)
plt.close()

print("\n--- KS test summary ---")
for name, (stat, p) in ks_results.items():
    verdict = "OK (no strong evidence of overtraining)" if p > 0.01 else "WARNING: possible overtraining"
    print(f"{name}: KS={stat:.4f}, p-value={p:.4f} -> {verdict}")

# -------------------------------------------------------------------
# ROC curve
# -------------------------------------------------------------------
fpr, tpr, _ = roc_curve(y_test, test_scores, sample_weight=w_test)
auc = roc_auc_score(y_test, test_scores, sample_weight=w_test)
plt.figure()
plt.plot(tpr, 1 - fpr, label=f"AUC = {auc:.3f}")
plt.xlabel("Signal efficiency")
plt.ylabel("Background rejection")
plt.legend()
plt.title("ROC curve")
plt.savefig("/eos/user/a/araghav/www/BDT/plots_bdt_xgboost/roc_curve.png", dpi=150)
plt.close()

# -------------------------------------------------------------------
# Per-variable signal vs background distributions
# -------------------------------------------------------------------
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
    plt.savefig(f"/eos/user/a/araghav/www/BDT/plots_bdt_xgboost/var_{var.replace('[','_').replace(']','')}.png", dpi=150)
    plt.close()

print("\nSaved: correlation matrices, roc_curve.png, per-variable plots")