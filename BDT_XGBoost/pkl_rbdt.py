import pickle
import ROOT

# Path to your pickled model
pkl_path = "/eos/user/a/araghav/xgb_outputs/xgb_Hgg_xgb_d5_lr03_n700_dense.pkl"
output_root = "/eos/user/a/araghav/XGBoost/xgb_model.root"

with open(pkl_path, "rb") as f:
    model = pickle.load(f)

# Ensure objective attribute is present for ROOT TMVA parser
if not hasattr(model, "objective") or model.objective is None:
    model.objective = "binary:logistic"

num_features = 16  # Must match the length of mvaVariables exactly

# Pass `model` directly (DO NOT extract booster)
ROOT.TMVA.Experimental.SaveXGBoost(
    model,
    "bdt_model",
    output_root,
    num_inputs=num_features
)

print(f"Model successfully converted and saved to -> {output_root}")