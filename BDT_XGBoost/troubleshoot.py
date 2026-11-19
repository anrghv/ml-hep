import numpy as np
d = np.load("/eos/user/a/araghav/xgboost/outputs_ml-hep/xgb_Hgg_tuning.npz")
s = np.load("/eos/user/a/araghav/xgboost/outputs_ml-hep/xgb_Hgg_scores_xgb_tuned_2.npz")
y, sc = d["y_test"], s["test_scores"]
print("signal mean:", sc[y==1].mean(), " bkg mean:", sc[y==0].mean())

import ROOT, pickle, numpy as np
X = d["X_test"][:2000].astype("float32")
clf = pickle.load(open("/eos/user/a/araghav/xgboost/outputs_ml-hep/xgb_Hgg_xgb_tuned_2.pkl","rb"))
py = clf.predict_proba(X)[:,1]
bdt = ROOT.TMVA.Experimental.RBDT("bdt_model", "/eos/user/a/araghav/xgboost/inputs_plot-config/xgb_Hgg_xgb_tuned_2.root")
rt = np.array([bdt.Compute(x.tolist())[0] for x in X])
print("max |py - root|     :", np.abs(py - rt).max())
print("max |py - (1-root)| :", np.abs(py - (1 - rt)).max())