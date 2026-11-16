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



# pkl_path = os.path.join(pkl_dir, pkl_file)

# output_root_name = pkl_file.replace("pkl", "root")
# output_root = os.path.join(output_dir, output_root_name)

# # print(f"\nLoading model from -> {pkl_dir}")
# # print(f"\nPickle file: {pkl_file}")
# # print(f"\nPickle path: {pkl_path}")
# # print(f"\nOutput ROOT file will be saved to -> {output_dir}")
# # print(f"\nOutput ROOT file Name: {output_root_name}\n")
# # print(f"\nOutput ROOT file Path: {output_root}\n")


# with open(pkl_path, "rb") as f:
#     model = pickle.load(f)

# # Ensure objective attribute is present for ROOT TMVA parser
# if not hasattr(model, "objective") or model.objective is None:
#     model.objective = "binary:logistic"

# num_features = 25  # Must match the length of mvaVariables exactly

# # Pass `model` directly (DO NOT extract booster)
# ROOT.TMVA.Experimental.SaveXGBoost(
#     model,
#     "bdt_model",
#     output_root,
#     num_inputs=num_features
# )

# print(f"Model successfully converted and saved to -> {output_root}")