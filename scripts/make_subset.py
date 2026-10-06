from pathlib import Path
import re

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
METADATA_DIR = ROOT / "data" / "raw" / "Project_CodeNet" / "metadata"
DATA_DIR = ROOT / "data" / "raw" / "Project_CodeNet" / "data"
OUTPUT_PATH = ROOT / "data" / "processed" / "subset_meta.csv"

ACCEPTED = "Accepted"
TLE = "Time Limit Exceeded"
KEEP_STATUSES = [ACCEPTED, TLE]

SEED = 42
MIN_ACCEPTED = 20
MIN_TLE = 10
FALLBACK_MIN_ACCEPTED = 10
FALLBACK_MIN_TLE = 5
MIN_PROBLEMS = 60
MAX_PROBLEMS = 100
MAX_PER_STATUS = 40


def get_problem_files():
    return sorted(
        path
        for path in METADATA_DIR.glob("p*.csv")
        if re.fullmatch(r"p\d{5}", path.stem)
    )


def find_eligible_problems(problem_files, min_accepted, min_tle):
    eligible = []

    for path in problem_files:
        df = pd.read_csv(path, usecols=["language", "status"])
        python_rows = df.loc[
            (df["language"] == "Python")
            & (df["status"].isin(KEEP_STATUSES))
        ]
        counts = python_rows["status"].value_counts()

        accepted_count = int(counts.get(ACCEPTED, 0))
        tle_count = int(counts.get(TLE, 0))

        if accepted_count >= min_accepted and tle_count >= min_tle:
            eligible.append(path.stem)

    return eligible


def main():
    problem_files = get_problem_files()
    if not problem_files:
        raise FileNotFoundError(
            f"No per-problem metadata CSV files found in {METADATA_DIR}"
        )

    min_accepted = MIN_ACCEPTED
    min_tle = MIN_TLE
    eligible = find_eligible_problems(
        problem_files, min_accepted, min_tle
    )
    used_fallback = False

    if len(eligible) < MIN_PROBLEMS:
        min_accepted = FALLBACK_MIN_ACCEPTED
        min_tle = FALLBACK_MIN_TLE
        eligible = find_eligible_problems(
            problem_files, min_accepted, min_tle
        )
        used_fallback = True

    if not eligible:
        raise ValueError("No problems meet the Accepted/TLE thresholds.")

    problem_count = min(MAX_PROBLEMS, len(eligible))
    selected_problems = (
        pd.Series(eligible)
        .sample(n=problem_count, random_state=SEED)
        .tolist()
    )

    columns_to_read = [
        "submission_id",
        "problem_id",
        "language",
        "status",
        "cpu_time",
        "code_size",
        "filename_ext",
    ]
    sampled_groups = []

    # Load submission details only for the selected problem files.
    for problem_id in selected_problems:
        metadata_path = METADATA_DIR / f"{problem_id}.csv"
        df = pd.read_csv(metadata_path, usecols=columns_to_read)
        df = df.loc[
            (df["language"] == "Python")
            & (df["status"].isin(KEEP_STATUSES))
        ]

        # Sample each verdict independently so both classes are represented.
        for status in KEEP_STATUSES:
            candidates = df.loc[df["status"] == status]
            sample_count = min(MAX_PER_STATUS, len(candidates))
            sampled_groups.append(
                candidates.sample(n=sample_count, random_state=SEED)
            )

    subset = pd.concat(sampled_groups, ignore_index=True)

    # CodeNet paths use the language folder and extension recorded in metadata.
    subset["path"] = [
        str(
            (DATA_DIR / problem_id / "Python" / f"{submission_id}.{extension}")
            .relative_to(ROOT)
        )
        for problem_id, submission_id, extension in zip(
            subset["problem_id"],
            subset["submission_id"],
            subset["filename_ext"],
        )
    ]

    output_columns = [
        "problem_id",
        "submission_id",
        "status",
        "cpu_time",
        "code_size",
        "path",
    ]
    subset = subset[output_columns].sort_values(
        ["problem_id", "status", "submission_id"]
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    subset.to_csv(OUTPUT_PATH, index=False)

    print(f"Metadata files found: {len(problem_files):,}")
    print(f"Thresholds used: {min_accepted} Accepted / {min_tle} TLE")
    print(f"Threshold fallback used: {used_fallback}")
    print(f"Eligible problems: {len(eligible):,}")
    print(f"Selected problems: {subset['problem_id'].nunique():,}")
    print(f"Rows written: {len(subset):,}")
    print("Rows by status:")
    print(subset["status"].value_counts().to_string())
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
