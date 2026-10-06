from pathlib import Path
import re

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
METADATA_DIR = ROOT / "data" / "raw" / "Project_CodeNet" / "metadata"

ACCEPTED = "Accepted"
TLE = "Time Limit Exceeded"


def main():
    problem_files = sorted(
        path
        for path in METADATA_DIR.glob("p*.csv")
        if re.fullmatch(r"p\d{5}", path.stem)
    )

    if not problem_files:
        raise FileNotFoundError(
            f"No per-problem CSV files found in {METADATA_DIR}"
        )

    python_submissions = 0
    status_counts = {}
    per_problem = {}

    for path in problem_files:
        df = pd.read_csv(path)

        python_df = df.loc[df["language"] == "Python"]
        python_submissions += len(python_df)

        for status, count in python_df["status"].value_counts().items():
            status_counts[status] = status_counts.get(status, 0) + int(count)

        counts = python_df["status"].value_counts()
        per_problem[path.stem] = {
            ACCEPTED: int(counts.get(ACCEPTED, 0)),
            TLE: int(counts.get(TLE, 0)),
        }

    tle_count = status_counts.get(TLE, 0)
    tle_share = tle_count / python_submissions if python_submissions else 0

    usable_problems = [
        problem_id
        for problem_id, counts in per_problem.items()
        if counts[ACCEPTED] >= 20 and counts[TLE] >= 10
    ]

    print(f"Problem metadata files: {len(problem_files):,}")
    print(f"Python submissions: {python_submissions:,}")
    print(f"Python TLE submissions: {tle_count:,}")
    print(f"Python TLE share: {tle_share:.2%}")
    print("\nPython submissions by status:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count:,}")

    print(
        "\nProblems with at least 20 Accepted and 10 TLE submissions: "
        f"{len(usable_problems):,}"
    )

    # Check how complete the problem time-limit field is.
    problem_list_path = METADATA_DIR / "problem_list.csv"
    problem_list = pd.read_csv(problem_list_path)

    if "time_limit" not in problem_list.columns:
        print("\nproblem_list.csv has no time_limit column.")
    else:
        present = problem_list["time_limit"].notna().sum()
        total = len(problem_list)
        share = present / total if total else 0
        print(
            f"\nproblem_list.csv time_limit present: "
            f"{present:,}/{total:,} ({share:.2%})"
        )


if __name__ == "__main__":
    main()