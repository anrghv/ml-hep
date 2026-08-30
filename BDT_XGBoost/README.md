# BDT_XGBoost

XGBoost-based BDT training for the Hgg analysis.

<!-- ## Files

| File                  | Description                                                         |
| --------------------- | ------------------------------------------------------------------- |
| `train_xgboost.py`    | Main script for preparing the dataset and training the XGBoost BDTs |
| `xgb_engine.py`       | XGBoost training/helper code                                        |
| `plot_results.py`     | Produces ROC/AUC, BDT-score, correlation and overtraining plots     |
| `configuration.py`    | Main configuration and input file setup                             |
| `configHgg_cfg.py`    | Hgg analysis configuration                                          |
| `samples_BDTTrain.py` | Defines the input samples/files                                     |
| `structure.py`        | Defines sample properties, including signal/background              |
| `aliases.py`          | Defines aliases/derived variables used in the BDT                   |
| `preselections.py`    | Event preselection                                                  |
| `cuts_BDTTrain.py`    | BDT training cuts                                                   |
| `headers.h`           | C++ helper functions used by ROOT                                   |
| `run_bdt.sh`          | Script for running the BDT training                                 |
| `submit.sub`          | HTCondor submission file                                            |
| `README.md`           | Documentation                                                       | -->

## Running locally

Run the training with:

```bash
python train_xgboost.py
```

or using the provided script:

```bash
./run_bdt.sh
```

Generated files and plots are stored on EOS and are not kept in the Git repository.
To see the outputs, follow [this link](https://araghav.web.cern.ch/?dir=BDT%2Fplots_bdt_xgboost).

## Plotting

After training, run:

```bash
python plot_results.py
```

This produces the main BDT performance plots, including:

* ROC curves and AUC
* BDT-score distributions
* Training vs. testing distributions
* Overtraining/KS checks
* Variable correlations

## HTCondor

To submit the training job to HTCondor:

```bash
condor_submit submit.sub
```

Check the submitted jobs with:

```bash
condor_q
```

To see the output/error files:

```bash
ls output/
ls error/
```

The Condor configuration is in:

```text
submit.sub
```

and the executable/wrapper used by the job is:

```text
run_bdt.sh
```

To remove a submitted job:

```bash
condor_rm <JOB_ID>
```

For example:

```bash
condor_rm 123456
```

The input ROOT files and generated outputs are kept on EOS; only the code and configuration files are tracked in Git.
