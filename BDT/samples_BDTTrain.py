import os
import glob

BDT_TREES_DIR = "/eos/user/a/araghav/BDT_Trees"

limitFiles = -1
# limitFiles = 1

STALE_FILES = []


def get_files(sampleName):
    pattern = os.path.join(BDT_TREES_DIR, sampleName, "*.root")
    files = [f for f in glob.glob(pattern) if os.path.basename(f) not in STALE_FILES]
    if limitFiles != -1:
        files = files[:limitFiles]
    return [(sampleName, files)]


samples = {}
for name in ["DY", "Hgluglu", "qqZHgluglu", "ggZHgluglu"]:
    samples[name] = {"name": get_files(name)}


if __name__ == "__main__":
    from ROOT import TChain

    for sampleName, sample in samples.items():
        sample['tree'] = TChain("Events")
        for tag, filelist, *rest in sample['name']:
            for f in filelist:
                sample['tree'].Add(f)
        print(f"{sampleName}: {sample['tree'].GetEntries()} entries, "
              f"{len(filelist) if filelist else 0} files")