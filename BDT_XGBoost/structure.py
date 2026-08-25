# structure configuration for datacard

# structure = {}

# keys here must match keys in samples.py

# =======================================
# ============== Backgrounds =============
# =======================================

structure['DY_train'] = {
    'isSignal': 0,
    'isData': 0
}

structure['DY_test'] = {
    'isSignal': 0,
    'isData': 0
}


# =======================================
# ================ Signals ==============
# =======================================

structure['Hgluglu_train'] = {
    'isSignal': 1,
    'isData': 0
}

structure['qqZHgluglu_train'] = {
    'isSignal': 1,
    'isData': 0
}

structure['ggZHgluglu_test'] = {
    'isSignal': 1,
    'isData': 0
}


# =======================================
# ================ Data =================
# =======================================

# structure['DATA'] = {
#     'isSignal': 0,
#     'isData': 1
# }