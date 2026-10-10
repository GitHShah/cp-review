from pathlib import Path

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

ROOT = Path(__file__).resolve().parents[1]
IN_PATH = ROOT / "data" / "processed" / "clean.csv"
OUT_PATH = ROOT / "data" / "processed" / "clean_split.csv"
SEED = 42

df = pd.read_csv(IN_PATH)

# 70% of problems to train, 30% held out
gss = GroupShuffleSplit(n_splits=1, test_size=0.30, random_state=SEED)
train_idx, rest_idx = next(gss.split(df, groups=df["problem_id"]))
train, rest = df.iloc[train_idx], df.iloc[rest_idx]

# split the held-out 30% evenly into validation and test (15% / 15%)
gss2 = GroupShuffleSplit(n_splits=1, test_size=0.50, random_state=SEED)
val_idx, test_idx = next(gss2.split(rest, groups=rest["problem_id"]))
val, test = rest.iloc[val_idx], rest.iloc[test_idx]

df["split"] = ""
df.loc[train.index, "split"] = "train"
df.loc[val.index, "split"] = "val"
df.loc[test.index, "split"] = "test"

# safety checks: no problem may appear in two splits
p_train, p_val, p_test = (set(x["problem_id"]) for x in (train, val, test))
assert not (p_train & p_val), "problem leak: train/val"
assert not (p_train & p_test), "problem leak: train/test"
assert not (p_val & p_test), "problem leak: val/test"
assert (df["split"] != "").all(), "some rows have no split"

print("rows per split:")
print(df["split"].value_counts().to_string())
print("\nproblems per split:")
print(df.groupby("split")["problem_id"].nunique().to_string())
print("\nTLE share per split:")
print(df.assign(tle=df["status"] == "Time Limit Exceeded")
        .groupby("split")["tle"].mean().round(3).to_string())

df.to_csv(OUT_PATH, index=False)
print("\nsaved", OUT_PATH)