# Architectural & Design Decisions

This document records the core architectural and methodological decisions for the CP/DSA Code Review Tool. These choices are fixed upfront to prevent scope creep, data leakage, and security risks.

---

## 1. Scope & Target Language
- **Decision:** Target **Python only** for v1.
- **Rationale:** Python provides a clean, standardized Abstract Syntax Tree (`ast` module) in the standard library. C++ support is deferred to future work because it requires complex macro pre-processing (`#define`, `template`) and external tooling (e.g. `tree-sitter`).

---

## 2. Parsing Engine
- **Decision:** Use the standard library **`ast`** module.
- **Rationale:** No third-party binary dependencies required for Python AST analysis. Tree-sitter will only be introduced if multi-language support (C++) is implemented.

---

## 3. Modeling Task & Objective
- **Decision:** Binary classification: **Accepted (AC) vs. Time Limit Exceeded (TLE)**.
- **Rationale:** Other verdicts (such as *Wrong Answer*, *Runtime Error*, *Memory Limit Exceeded*) are excluded from the main classification task. Our goal is to identify algorithmic inefficiency and performance bottlenecks, not functional correctness bugs.

---

## 4. Dataset Splitting Strategy
- **Decision:** Split dataset strictly by **`problem_id`** (70% train / 15% validation / 15% test).
- **Rationale:** Never split by submission. Splitting by submission would place solutions for the same problem in both train and test sets, causing massive data leakage and giving artificially high test accuracy.

---

## 5. Ground Truth & Complexity Labels
- **Decision:** Hand-labeled complexity annotations will only be used as a **benchmark test set**, never for training.
- **Rationale:** Hand labels (e.g. $O(n)$, $O(n^2)$) ensure an honest, unbiased ground-truth evaluation for the static estimator without introducing label noise into the training pipeline.

---

## 6. Feature Engineering & Data Leakage
- **Decision:** **Never** include `cpu_time` or execution runtime metrics as features.
- **Decision on Problem Constraints:** Drop `time_limit` / constraint metadata since it is missing or sparse in the dataset.
- **Rationale:** `cpu_time` is an outcome of running the code and completely leaks the target label.

---

## 7. Security & Execution
- **Decision:** **Never execute, `eval()`, or `exec()` user code.**
- **Rationale:** The entire analysis must remain purely static (AST-based and model-inferred) to prevent arbitrary code execution vulnerabilities when analyzing untrusted submissions.
