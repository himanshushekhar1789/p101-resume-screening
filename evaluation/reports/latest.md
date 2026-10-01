# P_101 — Phase 12 Evaluation & Benchmark Report

**Generated At**: 2026-10-01 05:24:52 UTC  
**Python**: 3.13.5 | **Platform**: win32  
**Dataset**: 10 Synthetic Resumes, 5 Synthetic Job Descriptions, 10 Curated Evaluation Cases  

---

## Executive Summary & Engineering Gates

| Evaluation Category | Acceptance Gate | Benchmark Result | Status |
| :--- | :--- | :--- | :---: |
| **Skill Normalization & Aliases** | 100% Protected pairs, >=90% Aliases | 100.0% Aliases, 100% Protected | **PASSED** |
| **Semantic Matching & Isolation** | 100% Protected blocking, 0% conflation | 100% Protected Pairs Blocked | **PASSED** |
| **Scoring Invariants (A–F)** | 100% Invariants hold | 6/6 Invariants Verified | **PASSED** |
| **Curated Benchmark Cases** | >= 90% Cases pass ground-truth | 10/10 Cases Passed (100.0%) | **PASSED** |
| **LLM Grounding & Guardrails** | 100% Anti-hallucination & No verdicts | 100% Grounded, 0 Hiring Verdicts | **PASSED** |
| **API End-to-End Smoke Tests** | 100% Endpoints return 200 OK | 7/7 Endpoints Operational | **PASSED** |

---

## 1. Skill Normalization & False-Positive Protection

- **Tested Aliases**: 13 canonical alias pairs (e.g. `JS` -> `JavaScript`, `Postgres` -> `PostgreSQL`, `k8s` -> `Kubernetes`).
- **Alias Accuracy**: 100.0%.
- **Protected Distinct Technologies**: 100% preserved without conflation:
  - `C` != `C++`
  - `C` != `C#`
  - `Java` != `JavaScript`
  - `Python` != `PyTorch`
  - `React` != `React Native`
  - `AWS` != `AWS Lambda`
- **Stopword False-Positive Rejection**: 100% rejection rate for generic resume words (`experience`, `team`, `development`, `code`, `skills`).

---

## 2. Semantic Matching & Pair Distinctions (Phase 7)

- **Related Technology Pairs**:
  - `FastAPI <-> Flask`: 0.23
  - `PostgreSQL <-> MySQL`: 0.5469
  - `Docker <-> Kubernetes`: 0.3151
- **Unrelated Technology Pairs**:
  - `React <-> Accounting`: 0.0526
  - `Python <-> Accounting`: 0.2864
  - `Docker <-> Graphic Design`: 0.1283
- **Protected Pair Blocking**: All 5 protected pairs (`Java != JavaScript`, `C != C++`, `Python != PyTorch`, `React != React Native`, `AWS != AWS Lambda`) are strictly blocked by the false-positive protection matrix.

---

## 3. Hybrid Scoring Invariants A–F (Phase 8/8.1/8.2)

- **Invariant A & C**: Career-experience semantic similarity does NOT contribute to `semantic_fit` (PASSED).
- **Invariant B**: Experience requirements do NOT contribute to `rule_fit` (PASSED).
- **Invariant D**: Changing experience tenure changes `experience_fit` only; `rule_fit` and `semantic_fit` remain unchanged (PASSED).
- **Invariant E**: Unavailable `llm_fit` triggers proper dynamic weight renormalization, and active weights sum to exactly 1.0 (PASSED).
- **Invariant F**: Final candidate fit score is 100% reproducible for identical inputs (PASSED).

---

## 4. Curated Synthetic Cases Results Matrix

| Case ID | Candidate Profile Type | Target Role | Fit Score | Must-Haves Met? | Gaps Found | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| `case_01_strong_backend_on_backend_job` | Curated synthetic | Target JD | 84.1% | Yes | 0 missing | **PASSED** |
| `case_02_weak_backend_on_backend_job` | Curated synthetic | Target JD | 25.2% | No | 6 missing | **PASSED** |
| `case_03_strong_frontend_on_frontend_job` | Curated synthetic | Target JD | 82.8% | Yes | 0 missing | **PASSED** |
| `case_04_data_scientist_on_ds_job` | Curated synthetic | Target JD | 84.4% | Yes | 0 missing | **PASSED** |
| `case_05_devops_on_devops_job` | Curated synthetic | Target JD | 89.7% | Yes | 0 missing | **PASSED** |
| `case_06_junior_on_entry_job` | Curated synthetic | Target JD | 80.5% | Yes | 1 missing | **PASSED** |
| `case_07_career_changer_on_backend_job` | Curated synthetic | Target JD | 56.0% | No | 4 missing | **PASSED** |
| `case_08_related_skills_on_backend_job` | Curated synthetic | Target JD | 52.7% | No | 4 missing | **PASSED** |
| `case_09_sparse_resume_on_backend_job` | Curated synthetic | Target JD | 35.3% | No | 4 missing | **PASSED** |
| `case_10_ambiguous_formatting_on_backend_job` | Curated synthetic | Target JD | 69.9% | No | 2 missing | **PASSED** |

---

## 5. Performance & Latency Telemetry

### Embedding Inference Performance
- **Warm Inference**: 25.70 ms
- **Cached Inference**: 0.104 ms
- **Cache Acceleration Factor**: 247.4x speedup

### Pipeline Stage Latencies (5-Run Sample, milliseconds)
| Stage | Min (ms) | Median (ms) | p95 (ms) |
| :--- | :---: | :---: | :---: |
| Document Parsing | 9.17 | 12.33 | 17.56 |
| Profile & JD Extraction | 41.28 | 43.72 | 47.77 |
| Deterministic Matching | 8.43 | 10.79 | 65.66 |
| Hybrid Scoring | 0.2 | 0.21 | 0.27 |
| Skill-Gap Analysis | 0.79 | 0.86 | 1.01 |
| Grounded LLM Explanation | 1.78 | 1.93 | 2.45 |
| **End-to-End Pipeline** | **64.09** | **72.65** | **130.84** |

---

## 6. Interpretation & Scope Boundaries

1. **Synthetic Curated Nature**: These metrics represent performance across the curated synthetic benchmark dataset of 10 candidate profiles and 5 job specifications. They are project-level engineering gates and do not constitute an empirical claim of real-world hiring efficacy.
2. **Zero Candidate Ranking**: No cross-candidate sorting, stack-ranking, or leaderboard algorithms were evaluated or implemented.
3. **Zero Automated Hiring Actions**: All evaluations produced purely decision-support evidence without automated hire/reject decisions.
