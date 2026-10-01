# Evaluation, Benchmarking & End-to-End Validation Suite (Phase 12)

This directory contains the reproducible benchmark suite and synthetic evaluation dataset for **P_101 — LLM-Based Resume Screening System**.

It validates the complete system end-to-end across all 11 preceding architectural phases, verifying deterministic accuracy, semantic matching boundaries, scoring invariants, skill-gap classification, LLM evidence grounding, and system performance latencies.

---

## Directory Structure

```text
evaluation/
├── resumes/                      # 10 Synthetic candidate resumes (.txt)
│   ├── 01_strong_backend.txt
│   ├── 02_weak_backend.txt
│   ├── 03_strong_frontend.txt
│   ├── 04_data_scientist.txt
│   ├── 05_devops_cloud.txt
│   ├── 06_junior_software_engineer.txt
│   ├── 07_career_changer.txt
│   ├── 08_related_skills_candidate.txt
│   ├── 09_sparse_resume.txt
│   └── 10_ambiguous_formatting.txt
├── jobs/                         # 5 Synthetic job descriptions (.txt)
│   ├── 01_backend_engineer.txt
│   ├── 02_frontend_developer.txt
│   ├── 03_data_scientist.txt
│   ├── 04_devops_engineer.txt
│   └── 05_entry_level_engineer.txt
├── cases/                        # 10 Curated case definitions (.json)
│   ├── case_01_strong_backend_on_backend_job.json
│   ├── case_02_weak_backend_on_backend_job.json
│   ├── case_03_strong_frontend_on_frontend_job.json
│   ├── case_04_data_scientist_on_ds_job.json
│   ├── case_05_devops_on_devops_job.json
│   ├── case_06_junior_on_entry_job.json
│   ├── case_07_career_changer_on_backend_job.json
│   ├── case_08_related_skills_on_backend_job.json
│   ├── case_09_sparse_resume_on_backend_job.json
│   └── case_10_ambiguous_formatting_on_backend_job.json
├── reports/                      # Benchmark outputs
│   ├── latest.json               # Machine-readable benchmark telemetry
│   └── latest.md                 # Human-readable evaluation report
└── run_evaluation.py             # Benchmark test runner
```

---

## Dataset Description

### 10 Synthetic Candidate Profiles (`evaluation/resumes/`)

| File | Profile Type | Core Skills & Tenure | Key Characteristics |
| :--- | :--- | :--- | :--- |
| `01_strong_backend.txt` | Senior Backend Engineer | Python (5.0y), FastAPI (3.5y), PostgreSQL (5.0y), Docker, Redis | High experience, satisfies all must-haves and nice-to-haves |
| `02_weak_backend.txt` | Junior Backend with Deficits | Python (0.7y), SQLite | Severe tenure shortfall, missing PostgreSQL, Docker, BS degree |
| `03_strong_frontend.txt` | Senior Frontend Engineer | JavaScript (6.2y), React (5.0y), TypeScript (4.0y), Tailwind, Next.js | Strong frontend specialization, full stack nice-to-haves |
| `04_data_scientist.txt` | Data Scientist & ML Engineer | Python (4.1y), PyTorch (3.0y), SQL (4.1y), Scikit-learn, NLP, MS degree | Meets ML specialization and advanced degree requirement |
| `05_devops_cloud.txt` | Senior DevOps & Cloud Engineer | Kubernetes (4.0y), Docker (5.3y), AWS (4.5y), Terraform, CI/CD | Full infrastructure and cloud automation coverage |
| `06_junior_software_engineer.txt` | Early-Career Graduate | Python (1.0y), Git (1.0y), Linux, BS in CS (2024) | High match for entry-level positions, satisfies 0.5y requirement |
| `07_career_changer.txt` | Bootcamp Transitioner | Python (0.5y), SQL (0.5y), Finance background (3.0y) | Relevant transferrable logic, partial technical tenure |
| `08_related_skills_candidate.txt` | Adjacent Stack Candidate | Flask (3.0y), MySQL (3.0y), Docker | Tests semantic proximity vs deterministic missing gaps |
| `09_sparse_resume.txt` | Minimalist Resume | Python, FastAPI, SQL (no dates or tenure metrics) | Tests `not_evaluable` handling without unfair failure |
| `10_ambiguous_formatting.txt` | Non-standard Typography | `PYTHON`, `pOsTgReS`, `DoCkEr` | Tests normalization robustness and case-insensitivity |

### 5 Synthetic Job Descriptions (`evaluation/jobs/`)

| File | Job Title | Key Requirements | Priority Distribution |
| :--- | :--- | :--- | :--- |
| `01_backend_engineer.txt` | Senior Backend Engineer | Python (3y), FastAPI (2y), PostgreSQL, 4y general exp, BS CS | 5 Must-Haves, 2 Nice-to-Haves |
| `02_frontend_developer.txt` | Senior Frontend Developer | JavaScript (3y), React (3y), TypeScript, 3y general exp, BS | 5 Must-Haves, 2 Nice-to-Haves |
| `03_data_scientist.txt` | Data Scientist & ML Engineer | Python (3y), PyTorch (2y), SQL, 3y ML exp, Master's degree | 5 Must-Haves, 2 Nice-to-Haves |
| `04_devops_engineer.txt` | Cloud DevOps Engineer | Kubernetes (2y), Docker (3y), AWS (2y), 4y exp, BS | 5 Must-Haves, 2 Nice-to-Haves |
| `05_entry_level_engineer.txt` | Entry-Level Software Engineer | Python/JS, Git, 0.5y exp, Bachelor's degree | 4 Must-Haves, 2 Nice-to-Haves |

---

## 10 Curated Evaluation Cases (`evaluation/cases/`)

1. **Case 01 (`case_01_strong_backend_on_backend_job.json`)**: Ideal senior backend match. Verifies 100% must-have satisfaction, high fit score (>0.80), and zero missing must-haves.
2. **Case 02 (`case_02_weak_backend_on_backend_job.json`)**: Severe shortfall. Verifies `all_must_haves_satisfied == False`, low fit score (<0.30), and clear missing skill identification.
3. **Case 03 (`case_03_strong_frontend_on_frontend_job.json`)**: Senior frontend match. Verifies domain-specific matching with React, TypeScript, and modern styling.
4. **Case 04 (`case_04_data_scientist_on_ds_job.json`)**: ML & data science role. Verifies graduate degree verification and PyTorch/Python matching.
5. **Case 05 (`case_05_devops_on_devops_job.json`)**: Cloud infrastructure role. Verifies Kubernetes/Docker orchestration and AWS verification.
6. **Case 06 (`case_06_junior_on_entry_job.json`)**: Entry-level graduate on entry-level JD. Verifies proportional experience satisfaction (1.0y / 0.5y = 1.0 capped).
7. **Case 07 (`case_07_career_changer_on_backend_job.json`)**: Career transition candidate. Verifies proper experience fit attenuation and gap recommendations.
8. **Case 08 (`case_08_related_skills_on_backend_job.json`)**: Adjacent stack (Flask/MySQL vs FastAPI/PostgreSQL). Verifies semantic proximity support without overriding deterministic gap detection.
9. **Case 09 (`case_09_sparse_resume_on_backend_job.json`)**: Resume without tenure metrics. Verifies `not_evaluable` status exclusion from denominator without causing unfair auto-failure.
10. **Case 10 (`case_10_ambiguous_formatting_on_backend_job.json`)**: Mixed casing and inconsistent headers. Verifies taxonomy canonicalization across non-standard formatting.

---

## Acceptance Gates & Validation Invariants

| Category | Gate | Verification Result |
| :--- | :--- | :---: |
| **Skill Normalization** | 100% alias resolution, 100% stopword rejection | **PASSED** (100%) |
| **Protected Incompatible Pairs** | Java != JavaScript, C != C++, Python != PyTorch, React != React Native, AWS != AWS Lambda | **PASSED** (100% blocked) |
| **Invariant A & C** | Experience excluded from `semantic_fit` | **PASSED** |
| **Invariant B** | Experience excluded from `rule_fit` | **PASSED** |
| **Invariant D** | Experience tenure isolated to `experience_fit` | **PASSED** |
| **Invariant E** | Weight renormalization integrity (sum to 1.0) | **PASSED** |
| **Invariant F** | 100% Deterministic reproducibility | **PASSED** |
| **Curated Cases** | All 10 curated cases meet ground-truth | **PASSED** (10/10, 100%) |
| **LLM Anti-Hallucination** | Zero hallucinated skills or credentials | **PASSED** (100%) |
| **Zero Hiring Decisions** | Zero automated hire/reject verdicts in LLM output | **PASSED** (100%) |
| **FastAPI REST Smoke Tests** | All 7 critical endpoints return 200 OK | **PASSED** (7/7, 100%) |

---

## How to Run the Benchmark Suite

Execute the benchmark runner from the project root:

```bash
# Activate virtual environment
.\.venv\Scripts\python.exe evaluation/run_evaluation.py
```

The script will:
1. Evaluate skill normalization and false-positive protection.
2. Evaluate semantic matching and protected incompatible technology pairs.
3. Validate scoring invariants A through F.
4. Execute the 10 curated benchmark cases and check against ground truth.
5. Benchmark inference latency across 5 iterations of each pipeline stage.
6. Execute FastAPI HTTP smoke tests against all REST endpoints.
7. Generate updated `evaluation/reports/latest.json` and `evaluation/reports/latest.md`.

---

## Critical Scope Boundaries

- **Zero Candidate Ranking**: No cross-candidate sorting, stack-ranking, or leaderboard algorithms are implemented or evaluated.
- **Zero Automated Hiring Decisions**: The system outputs decision-support evidence and grounded analysis only; no automated hire/reject actions exist.
- **Synthetic Ground Truth**: All evaluation data is synthetic; it verifies system engineering correctness and architectural integrity without claiming real-world hiring efficacy.
