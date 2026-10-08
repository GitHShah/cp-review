import ast
import warnings
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
IN_PATH = ROOT / "data" / "processed" / "subset_meta.csv"
OUT_PATH = ROOT / "data" / "processed" / "clean.csv"

MAX_CHARS = 20_000
MIN_PER_CLASS = 5

df = pd.read_csv(IN_PATH)
print("rows in subset:", len(df))

dropped = {"missing": 0, "empty": 0, "too_big": 0, "syntax": 0}
keep_rows, n_lines = [], []

for _, row in df.iterrows():
    p = ROOT / row["path"]
    if not p.exists():
        dropped["missing"] += 1
        continue
    code = p.read_text(encoding="utf-8", errors="ignore")
    if not code.strip():
        dropped["empty"] += 1
        continue
    if len(code) > MAX_CHARS:
        dropped["too_big"] += 1
        continue
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ast.parse(code)
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        dropped["syntax"] += 1
        continue
    keep_rows.append(row)
    n_lines.append(code.count("\n") + 1)

clean = pd.DataFrame(keep_rows).reset_index(drop=True)
clean["n_lines"] = n_lines

print("\ndropped:", dropped)
print("rows kept:", len(clean), "of", len(df))
print("\nstatus counts after cleaning:")
print(clean["status"].value_counts().to_string())

per = clean.groupby(["problem_id", "status"]).size().unstack(fill_value=0)
for col in ["Accepted", "Time Limit Exceeded"]:
    if col not in per.columns:
        per[col] = 0
weak = per[(per["Accepted"] < MIN_PER_CLASS) |
           (per["Time Limit Exceeded"] < MIN_PER_CLASS)]
print(f"\nproblems with fewer than {MIN_PER_CLASS} of either class:", len(weak))
print("problems total:", len(per))

clean.to_csv(OUT_PATH, index=False)
print("saved", OUT_PATH)