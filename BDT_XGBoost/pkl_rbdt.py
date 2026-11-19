import pickle
import ROOT
import os

# Path to your pickled model
pkl_dir = "/eos/user/a/araghav/xgboost/outputs_ml-hep"
output_dir = "/eos/user/a/araghav/xgboost/inputs_plot-config"


pkl_files = [f for f in os.listdir(pkl_dir) if f.endswith(".pkl")]
# pkl_file = "xgb_Hgg_xgb_tuned_2.pkl" # Adjust the filename

for i, pkl_file in enumerate(pkl_files):
    print(f"\nProcessing model {i+1}/{len(pkl_files)}: {pkl_file}")

    pkl_path = os.path.join(pkl_dir, pkl_file)

    output_root_name = pkl_file.replace("pkl", "root")
    output_root = os.path.join(output_dir, output_root_name)

    with open(pkl_path, "rb") as f:
        model = pickle.load(f)

    if not hasattr(model, "objective") or model.objective is None:
        model.objective = "binary:logistic"

    num_features = model.n_features_in_  # Must match the length of mvaVariables exactly

    ROOT.TMVA.Experimental.SaveXGBoost(
        model,
        "bdt_model",
        output_root,
        num_inputs=num_features
    )
    print(f"num_features: {num_features}")

    print(f"Model successfully converted and saved to -> {output_root}")

import numpy as np
X = np.random.rand(1000, num_features).astype("float32")
py_scores = model.predict_proba(X)[:, 1]

bdt = ROOT.TMVA.Experimental.RBDT("bdt_model", output_root)
root_scores = np.array([bdt.Compute(x.tolist())[0] for x in X])

print(np.max(np.abs(py_scores - root_scores)))  # should be ~1e-6
