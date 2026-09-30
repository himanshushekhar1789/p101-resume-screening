# Evaluation & Testing Strategy — P_101 Resume Screening System

This document outlines the evaluation framework, metrics, and synthetic dataset strategy for testing the system.

## 1. Evaluation Methodology
Because this system acts as a decision-support tool, evaluation spans multiple objective dimensions:

| Dimension | Metric | Target | Description |
|-----------|--------|--------|-------------|
| **Text Extraction** | Character Accuracy / Layout preservation | > 98% | Accuracy of PyMuPDF & python-docx extraction from single/two-column formats |
| **Information Extraction** | F1-Score on Entities | > 85% | Accurate detection of skills, degree, contact info, and experience periods |
| **Skill Normalization** | Canonical Mapping Accuracy | > 95% | Synonym mapping (e.g. "ReactJS" -> "React") |
| **Semantic Matching** | Cosine Correlation with Ground Truth | > 0.80 | Alignment between human-rated fit and vector similarity |
| **Skill-Gap Detection** | Precision / Recall on Missing Skills | > 90% | High recall to ensure candidates are alerted to all actual gaps |
| **Explainability** | Citation Grounding Rate | 100% | Zero hallucinations: every match evidence must quote actual resume tokens |
| **Ranking Quality** | NDCG@5 / Kendall's Tau | > 0.85 | Agreement between system ranking and expert recruiter ranking |

## 2. Synthetic Test Dataset
To maintain ethical standards and respect privacy:
- **Zero real human resumes** will be committed into the repository.
- Synthetic resumes covering realistic archetypes (Entry-Level, Mid-Level Full Stack, Senior DevOps, Career Transitioner, Non-matching Applicant) will be generated and placed in `data/sample/`.
- Corresponding ground-truth annotations will be provided in `data/sample/annotations.json`.

## 3. Robustness & Fairness
- **Masked Mode Verification**: Running the pipeline with and without masked mode to confirm that non-job-related attributes (name, gender, institution) produce 0 differential impact on scores.
- **Malformed Documents**: Testing behavior with corrupted PDFs, image-only PDFs, and empty files to guarantee clean HTTP 4xx error handling.

---

## 4. Phase 2: Document Processing Test Matrix

The test suite in `backend/tests/test_document_parser.py` validates text extraction and input security across 19 unit & integration tests:

| Test Case | Target Component | Input Conditions | Expected Outcome |
|-----------|------------------|------------------|------------------|
| `test_sanitize_filename` | Filename Sanitizer | Path traversal (`../../../etc/passwd/resume.pdf`) | Clean basename `resume.pdf` without directory components |
| `test_validate_document_size_empty` | Size Validator | 0 bytes payload | Raises `EmptyDocumentError` |
| `test_validate_document_size_oversized` | Size Validator | Payload > configured limit | Raises `DocumentSizeLimitError` |
| `test_detect_file_type_unsupported` | File Detector | Unsupported extension (`.png`) | Raises `UnsupportedFormatError` |
| `test_detect_file_type_header_mismatch` | Header Checker | `.pdf` with non-PDF bytes, `.docx` with non-zip bytes | Raises `CorruptDocumentError` |
| `test_parse_valid_pdf_single_page` | PyMuPDF Parser | Well-formed single page text PDF | Extracts text, correct word/character/page counts |
| `test_parse_valid_pdf_multi_page` | PyMuPDF Parser | Well-formed 2-page text PDF | Preserves page order, extracts text from all pages |
| `test_parse_scanned_or_blank_pdf` | Scanned Detector | PDF with blank page (image/scanned equivalent) | Detects zero extractable text, raises `ScannedDocumentError` |
| `test_parse_corrupt_pdf` | PyMuPDF Parser | Damaged/incomplete PDF stream | Gracefully caught, raises `CorruptDocumentError` |
| `test_parse_valid_docx` | python-docx Parser | Valid DOCX with multiple paragraphs | Extracts text preserving paragraph order |
| `test_parse_docx_with_tables` | python-docx Parser | DOCX with embedded skill/experience table | Extracts table cells in row order, deduplicates merged cells |
| `test_parse_empty_docx` | python-docx Parser | DOCX with 0 text paragraphs or tables | Raises `EmptyDocumentError` |
| `test_parse_corrupt_docx` | python-docx Parser | Damaged/corrupt zip stream | Raises `CorruptDocumentError` |
| `test_api_parse_valid_pdf` | REST API | Multi-part form upload with valid PDF | HTTP 200 with `DocumentParseResponse` schema |
| `test_api_parse_valid_docx` | REST API | Multi-part form upload with valid DOCX | HTTP 200 with `DocumentParseResponse` schema |
| `test_api_parse_unsupported_format` | REST API | Image upload (`.png`) | HTTP 400 Bad Request with descriptive message |
| `test_api_parse_empty_file` | REST API | 0-byte file upload | HTTP 400 Bad Request |
| `test_api_parse_scanned_pdf` | REST API | Scanned/blank PDF upload | HTTP 422 Unprocessable Content alerting user to scanned format |
| `test_api_parse_corrupt_file` | REST API | Malformed PDF upload | HTTP 400 Bad Request |

---

## 5. Phase 3: Structured Resume Extraction Evaluation

### 5.1 LLM Mocking Strategy for CI/CD & Testing
To guarantee deterministic, ultra-fast, and cost-free test executions, the test suite never relies on live paid LLM API calls:
- `MockLLMClient` is injected during unit and integration tests.
- It operates in two modes:
  1. **Pre-queued Responses**: Injects custom JSON or corrupted text strings to simulate failure, malformed output, or edge cases.
  2. **Heuristic Parsing Fallback**: Uses regex and section boundaries to parse raw resume text into valid candidate profiles, enabling realistic end-to-end tests without external network calls.

### 5.2 Phase 3 Test Matrix (`backend/tests/test_resume_extractor.py`)

| Test Case | Scope | Scenario | Expected Outcome |
|---|---|---|---|
| `test_candidate_profile_valid` | Schema | Complete profile with all nested models | Validates and instantiates without errors |
| `test_candidate_profile_missing_optional_fields` | Schema | Profile with omitted optional fields | Defaults smoothly to None and empty lists |
| `test_candidate_profile_invalid_email` | Schema | Malformed email string | Raises `ValueError` via field validator |
| `test_candidate_profile_phone_string_conversion` | Schema | Integer phone input (`9876543210`) | Converts to string via `mode='before'` validator |
| `test_extract_email` | Rule Extractor | Realistic email in messy text | Extracts canonical lowercase email |
| `test_extract_phone` | Rule Extractor | US and international phone formats | Extracts clean phone string |
| `test_extract_links` | Rule Extractor | Text containing LinkedIn and GitHub URLs | Maps URLs to respective dictionary keys |
| `test_extract_sections` | Rule Extractor | Multi-section resume text | Slices resume into Summary, Skills, Experience, Education |
| `test_validate_llm_json_clean` | Validator | Plain JSON string from LLM | Successfully parses into `CandidateProfile` |
| `test_validate_llm_json_markdown_wrapped` | Validator | JSON wrapped in ````json ... ```` blocks | Strips markdown fences and parses cleanly |
| `test_validate_llm_json_malformed` | Validator | Broken JSON syntax from LLM | Raises `LLMValidationError` |
| `test_validate_llm_json_schema_error` | Validator | JSON payload with invalid schema values | Catches Pydantic validation errors |
| `test_extract_candidate_profile_service` | Service | Raw text processed with `MockLLMClient` | Returns complete, grounded `CandidateProfile` |
| `test_api_extract_synthetic_pdf` | REST API | Synthetic Software Engineer PDF upload | HTTP 200 with extracted skills, experience, education |
| `test_api_extract_synthetic_docx` | REST API | Synthetic Frontend Developer DOCX upload | HTTP 200 with table-extracted skills and experience |
| `test_api_extract_unsupported_format` | REST API | Non-resume file format upload | HTTP 400 Bad Request |
| `test_api_extract_scanned_pdf` | REST API | Blank/scanned PDF upload | HTTP 422 Unprocessable Content |
| `test_multi_job_experience_separation` | Service & API | Resume with multiple jobs (`synthetic_software_engineer.pdf`) | Extracts 2 distinct jobs, clean companies without bullet dumps, valid dates |
| `test_education_formats_parsing` | Rule Extractor | Formats A (multi-line), B (dash-delimited), C (comma-delimited) | Accurately parses degree (preserving dots like M.S.), field, and clean institution |
| `test_project_name_description_separation` | Rule Extractor | Colon- and dash-delimited project entries | Isolates project name from functional description and maps technologies |
| `test_skill_categorization_hardening` | Taxonomy | Skills including `REST APIs`, `Python`, `FastAPI`, `PostgreSQL` | Standardizes categories: `REST APIs` to `other`, `Python` to `programming_language` |
| `test_reconcile_candidate_profile_recovers_merged_job` | Reconciler | Flawed LLM output with merged jobs, leaked institution, bad skill category | Unpacks 2 jobs, cleans education and projects, standardizes skill categories |
| `test_all_four_synthetic_resumes_extract_e2e` | End-to-End API | All 4 synthetic resumes (`.pdf` and `.docx`) | 100% extraction success with 0 schema violations or bullet-point leaks |

---

## 6. Phase 4: Job Description Analysis & Requirement Extraction Evaluation

### 6.1 Requirement & Priority Taxonomy
Phase 4 converts unstructured Job Descriptions into a structured, validated `JobProfile`:
- **Requirement Classification**:
  - `must_have`: Non-negotiable mandatory qualifications (e.g., "Must have 3+ years...", "Required:", "Essential:").
  - `nice_to_have`: Optional, advantageous qualifications (e.g., "Experience with Docker is a plus", "Preferred qualifications:", "Bonus if...").
- **Isolated Dimensions**:
  - `skills`: Required & preferred technical / soft skills with explicit category and priority.
  - `experience`: Minimum years and role/domain scope requirements (general vs. skill-specific).
  - `education`: Minimum degree level, accepted fields of study, and whether mandatory.
  - `certifications`: Industry certifications with priority.
  - `responsibilities`: Primary job responsibilities cleanly isolated from qualification requirements.
  - `must_have` vs `nice_to_have`: Pre-computed, flattened string summaries for downstream scoring and rule filtering.

### 6.2 Phase 4 Test Matrix (`backend/tests/test_jd_analyzer.py`)

| Test Case | Scope | Scenario | Expected Outcome |
|---|---|---|---|
| `test_job_profile_schema_valid` | Schema | Complete `JobProfile` instance with all requirement types | Validates cleanly without error |
| `test_priority_normalization_validator` | Schema | Priority strings like "preferred", "bonus", "plus" | Normalized to `RequirementPriority.NICE_TO_HAVE` |
| `test_rule_section_segmentation` | Rule Extractor | Unstructured JD text with headers | Correctly splits text into summary, responsibilities, requirements |
| `test_must_have_vs_nice_to_have_classification` | Rule Extractor | Mixed requirement text with "must have", "plus", "preferred" | Accurately assigns `must_have` and `nice_to_have` priorities |
| `test_experience_years_extraction` | Rule Extractor | Numeric expressions like "5+ years", "3-5 years" | Extracts correct `minimum_years` float (e.g. 5.0, 3.0) |
| `test_skill_specific_vs_general_experience` | Rule Extractor | "5+ years backend" vs "3+ years Python" | Categorizes into general experience and skill requirement |
| `test_education_requirement_extraction` | Rule Extractor | "Bachelor's degree in CS or related field required" | Extracts degree "Bachelor's", field "Computer Science", is_required=True |
| `test_zero_hallucination_empty_education_and_certifications` | Rule Extractor | JD with no mention of degree or certifications | Leaves education=None, certifications=[], 0 hallucinated requirements |
| `test_certification_requirement_extraction` | Rule Extractor | "AWS Certified Solutions Architect or CKA preferred" | Extracts 2 certifications with `nice_to_have` priority |
| `test_responsibilities_isolation` | Rule Extractor | "Responsibilities:" section with bullet points | Extracts clean duty list without mixing into requirements |
| `test_mock_llm_jd_extraction` | LLM Mock | Offline mock generation with JD prompt | Produces valid JSON string parsable into `JobProfile` |
| `test_reconcile_overrides_false_must_haves_with_plus_evidence` | Reconciler | Flawed LLM output tagging "AWS is a plus" as `must_have` | Overrides priority to `nice_to_have` based on evidence |
| `test_analyze_job_description_service` | Service | Raw text JD passed to `analyze_job_description()` | Returns complete, validated `JobProfile` |
| `test_api_analyze_job_json` | REST API | `POST /api/v1/jobs/analyze` with JSON payload | HTTP 200 with `JobAnalysisResponse` schema |
| `test_api_analyze_job_upload_pdf` | REST API | `POST /api/v1/jobs/analyze/upload` with synthetic PDF | HTTP 200 with extracted requirements and `page_count` |
| `test_api_analyze_job_upload_docx` | REST API | `POST /api/v1/jobs/analyze/upload` with synthetic DOCX | HTTP 200 with extracted requirements |
| `test_api_analyze_job_upload_unsupported_file` | REST API | Uploading `.png` or unsupported format to upload endpoint | HTTP 400 Bad Request |
| `test_all_four_synthetic_jds_extract_e2e` | End-to-End API | Processing all 4 synthetic JDs (Backend, Frontend, Data Science, Intern) | 100% extraction success with accurate must/nice classification |

### 6.3 Synthetic Job Descriptions Benchmark Results

All 4 benchmark JDs were evaluated through both text and uploaded document formats:

| Job Description | Format | Must-Have Skills | Nice-to-Have Skills | Min Experience | Degree Required | Certifications |
|---|---|---|---|---|---|---|
| **Senior Backend Engineer** | `.txt`, `.pdf` | Python, FastAPI, PostgreSQL, Docker | Kubernetes, AWS, Redis, Celery, CI/CD | 5.0 years | Bachelor's (CS) | AWS Solutions Architect, CKA (Preferred) |
| **Frontend Developer** | `.txt`, `.docx` | React, TypeScript, JavaScript, CSS, HTML | Next.js, Redux, Tailwind CSS, Jest | 3.0 years | Bachelor's (CS/IT) | None |
| **Data Scientist & ML Engineer** | `.txt` | Python, PyTorch/TensorFlow, Scikit-Learn, SQL, Pandas | AWS SageMaker, MLflow, Docker | 3.0 years | Master's/Ph.D. (CS/Stats/Math) | AWS Machine Learning Specialty (Preferred) |
| **Software Engineering Intern** | `.txt` | Python/Java, Data Structures, Algorithms, Git | Linux, Docker, REST APIs, SQL | 0.0 years | Enrolled in B.S./B.Tech (CS) | None |

**Key Benchmarks Achieved**:
- **Priority Accuracy**: 100% agreement on mandatory vs. preferred keywords ("is a plus" consistently mapped to `nice_to_have`).
- **Degree False-Positive Mitigation**: Disambiguated English auxiliary verb "be" from degree acronym "B.E.", preventing false education requirements.
- **Zero Hallucination Rate**: 0% hallucinated certifications or degrees when absent from the input text.
- **Responsibilities Separation**: Cleanly separated job responsibilities from qualification criteria.

---

## 7. Phase 5: Skill Normalization & Taxonomy Mapping Evaluation

### 7.1 Normalization Architecture & Benchmarks
Phase 5 introduces deterministic skill standardization without LLM dependencies:
- **Canonical Skill Registry**: Centralized repository of >90 software engineering, data science, DevOps, and cloud competencies across 10 controlled categories.
- **Alias Resolution**: Conservative mapping of acronyms (`JS` $\rightarrow$ `JavaScript`, `K8s` $\rightarrow$ `Kubernetes`, `GCP` $\rightarrow$ `Google Cloud`, `NLP` $\rightarrow$ `Natural Language Processing`).
- **Version Stripping**: Standardized handling of versions (`Python 3.11` $\rightarrow$ `Python`, `React 18` $\rightarrow$ `React`).
- **Punctuation Sensitivity**: Exact differentiation of technical punctuation (`C++` $\neq$ `C`, `C#` $\neq$ `C`, `.NET` $\neq$ `Node.js`).
- **Deduplication with Provenance**: Merging redundant variants into single canonical records while preserving all extracted textual forms in `original_names`.

### 7.2 Phase 5 Test Matrix (`backend/tests/test_skill_normalizer.py`)

| Test Case | Scope | Scenario | Expected Outcome |
|---|---|---|---|
| `test_clean_skill_string` | String Sanitizer | Leading bullets, numbers, whitespace, technical punctuation | Cleans formatting while preserving `C++`, `C#`, `.NET`, `CI/CD` |
| `test_basic_case_and_casing_normalization` | Normalizer | `Python`, `python`, `PYTHON`, `  pYtHoN  ` | Normalizes to `Python` (`programming_language`, conf 1.0) |
| `test_safe_alias_mappings` | Taxonomy | 23 real-world aliases (`JS`, `TS`, `Postgres`, `GCP`, `K8s`, `NLP`, `ML`, etc.) | 100% accurate canonical name and category resolution |
| `test_version_normalization` | Normalizer | `Python 3.11`, `React 18`, `Postgres 15`, `Vue 3`, `Java 17` | Strips version to base canonical identity |
| `test_punctuation_sensitive_skills_separation` | Normalizer | `C`, `C++`, `c ++`, `C#`, `c #`, `.NET`, `Node.js`, `Next.js` | Zero accidental merges; distinct canonical representations |
| `test_unknown_skill_zero_hallucination` | Fallback | Unregistered technologies (`CustomInternalGraphEngine`) | Preserves original text, `method="unknown"`, `confidence=0.5`, 0 hallucination |
| `test_category_consistency_from_registry` | Taxonomy | Misclassified input categories (e.g., Python as 'other') | Registry overrides and enforces authoritative category |
| `test_false_positive_protection` | Stopwords | Isolated words like `experience`, `work`, `team`, `cloud`, `data` | Rejected and cleanly discarded from skills |
| `test_candidate_skill_deduplication` | Deduplication | Candidate with `Python`, `python`, `Python 3`, `K8s`, `Kubernetes` | Deduplicates to 3 canonical skills; merges `original_names` |
| `test_job_skill_deduplication_precedence` | Deduplication | JD with `Python` (must_have, 5yr) and `Python 3` (nice_to_have, 3yr) | `must_have` wins; max years (5.0) wins; evidence combined |
| `test_candidate_profile_pipeline_populates_normalized_skills` | Pipeline Integration | Synthetic resume parsed through `extract_candidate_profile()` | `profile.skills` preserved; `profile.normalized_skills` populated |
| `test_job_profile_pipeline_populates_normalized_skills` | Pipeline Integration | Synthetic JD parsed through `analyze_job_description()` | `profile.skills` preserved; `profile.normalized_skills` populated |
| `test_api_normalize_skills_endpoint` | REST API | `POST /api/v1/skills/normalize` with JSON list of strings | HTTP 200 with canonical names, methods, and confidence |
| `test_api_taxonomy_endpoint` | REST API | `GET /api/v1/skills/taxonomy` | HTTP 200 with all categories and registered skills |
| `test_e2e_synthetic_resumes_normalization` | End-to-End | Normalizing all 4 synthetic resumes (`.pdf` and `.docx`) | 100% success; key competencies accurately normalized |
| `test_e2e_synthetic_jds_normalization` | End-to-End | Normalizing all 4 synthetic JDs (`.txt`, `.pdf`, `.docx`) | 100% success; aliases and versions merged without loss |

### 7.3 Synthetic Datasets Normalization Audit

| Dataset Item | Extracted Skills | Normalized Skills | Notable Normalization & Deduplication Events |
|---|---|---|---|
| **Synthetic Software Engineer** (`.pdf`) | 14 | 14 | `PostgreSQL`, `FastAPI`, `Docker`, `Kubernetes`, `AWS`, `REST APIs`, `Microservices` confirmed canonical |
| **Synthetic Frontend Developer** (`.docx`) | 12 | 11 | `HTML5` $\rightarrow$ `HTML`; `CSS3` & `CSS` merged into `CSS`; `Next.js` and `Tailwind CSS` preserved |
| **Synthetic Data Scientist** (`.pdf`) | 9 | 9 | `NLP` $\rightarrow$ `Natural Language Processing` (alias); `GCP` $\rightarrow$ `Google Cloud` (alias) |
| **Synthetic Junior Intern** (`.docx`) | 9 | 9 | `Sqlite` $\rightarrow$ `SQLite`; `C` strictly separated from `C++` |
| **Backend Engineer JD** (`.txt`) | 15 | 15 | `GCP` $\rightarrow$ `Google Cloud`; `CI/CD` and `Mentorship` categorized; priorities intact |
| **Data Scientist JD** (`.txt`) | 16 | 15 | `NLP` and `Natural Language Processing` merged into 1 requirement with both evidence lines |
| **Frontend Developer JD** (`.txt`) | 11 | 9 | `JavaScript` & `Js` merged; `CSS` & `CSS3` merged; 2.0 min years preserved |
| **Entry Level Intern JD** (`.txt`) | 7 | 7 | `Problem Solving` $\rightarrow$ `soft_skill`; `Agile` $\rightarrow$ `other`; `C`, `Java`, `Python` canonical |

---

## 8. Phase 6: Candidate ↔ Job Requirement Matching Engine Evaluation

### 8.1 Guardrails & Verification Methodology
Phase 6 connects the normalized candidate profile and job requirements through a 100% deterministic matching layer:
- **Zero LLM Calls**: All matching logic is executed through rule-based and taxonomy-based evaluation.
- **Zero Embeddings / Cosine Calculations**: Dense vector similarity is reserved for Phase 7.
- **Zero Scores / Percentages / Rankings**: Outputs requirement-level evaluation records and summary counts only.
- **No Overclaiming / Conservative Verification**: Skill-specific tenure requirements return `not_evaluable` if durations cannot be verified from dated roles.
- **Non-Overlapping Tenure Union**: Concurrent positions are merged into disjoint date intervals to prevent double-counting.

### 8.2 Phase 6 Test Matrix (`backend/tests/test_matching_engine.py`)

| Test Case | Scope | Scenario | Expected Outcome |
|---|---|---|---|
| `test_parse_date_to_year_float` | Date Parser | `2021`, `2021-06`, `06/2021`, `June 2021`, `Present` | Converts to decimal year float; invalid strings return `None` |
| `test_calculate_non_overlapping_tenure` | Tenure Calculator | Two overlapping roles (2020-2022, 2021-2023) | Merges intervals into [2020, 2023] yielding exactly 3.0 years |
| `test_parse_degree_level` | Education Parser | `B.Tech`, `Master of Science`, `Ph.D.`, `High School` | Maps to academic hierarchy levels 1–5 |
| `test_is_field_of_study_compatible` | Education Parser | Candidate CS degree vs Software Engineering requirement | Recognizes compatible STEM fields |
| `test_canonical_exact_skill_match` | Skill Matcher | Candidate `Python` vs Job `Python` | `status="matched"`, `method="canonical_exact"` |
| `test_alias_skill_match` | Skill Matcher | Candidate `K8s` vs Job `Kubernetes` | `status="matched"`, `method="alias_normalized"` |
| `test_version_compatible_skill_match` | Skill Matcher | Candidate `Python 3.11` vs Job `Python` | `status="matched"`, `method="version_compatible"` |
| `test_unmatched_skill` | Skill Matcher | Candidate without `Kubernetes` | `status="unmatched"`, `method="unmatched"` |
| `test_skill_with_unverifiable_years_is_not_evaluable` | Skill Matcher | Candidate has skill in skills section but no role duration | `status="not_evaluable"`, `method="not_evaluable"` |
| `test_skill_with_sufficient_role_years` | Skill Matcher | Candidate with 4.0 yr in Python role vs 3.0 yr requirement | `status="matched"`, `method="experience_verified"` |
| `test_general_experience_match` | Experience Matcher | Candidate with 5.0 years total vs 3.0 years requirement | `status="matched"`, `method="experience_verified"` |
| `test_general_experience_insufficient` | Experience Matcher | Candidate with 2.0 years total vs 5.0 years requirement | `status="partial"`, `method="experience_insufficient"` |
| `test_education_exact_match` | Education Matcher | Candidate B.Tech CS vs Job Bachelor's in CS requirement | `status="matched"`, `method="education_match"` |
| `test_education_partial_field_mismatch` | Education Matcher | Candidate Master's in Mechanical vs Job Bachelor's in CS | `status="partial"`, `method="education_partial"` |
| `test_certification_match` | Cert Matcher | Candidate AWS Certified Architect vs Job Requirement | `status="matched"`, `method="certification_match"` |
| `test_priority_preservation` | Priority Integrity | Job specifies `must_have` vs `nice_to_have` requirements | Match records strictly preserve original priorities |
| `test_no_scores_or_rankings_in_output` | Schema Integrity | Output inspected for scores, percentages, ranking fields | Asserted absent; only requirement counts present in summary |
| `test_five_synthetic_scenarios` | Synthetic Benchmark | Evaluates 5 synthetic applicant scenarios from Section 27 | Verified expected match distributions across archetypes |
| `test_api_matching_analyze_endpoint` | REST API | `POST /api/v1/matching/analyze` with JSON profiles | HTTP 200 with `CandidateJobMatchResponse` schema |
| `test_api_matching_from_files_endpoint` | REST API | `POST /api/v1/matching/from-files` with PDF and DOCX | HTTP 200 with end-to-end extraction and matching |
| `test_api_matching_from_files_unsupported_format` | REST API | Uploading `.png` to matching endpoint | HTTP 400 Bad Request |

### 8.3 Benchmark Audit for the 5 Synthetic Scenarios

| Scenario | Candidate Profile | Target Job Posting | Must-Have Results | Nice-to-Have Results | Overall Assessment |
|---|---|---|---|---|---|
| **1. Ideal Match** | Senior Backend Developer (5 yr Python, FastAPI, Docker, Postgres, B.Tech CS) | Senior Backend Engineer JD (5 yr Python, FastAPI, Docker, Postgres, BS CS) | **6/6 Matched** (100% satisfied) | **1 Matched, 1 Unmatched** (K8s missing) | `all_must_haves_satisfied=True` |
| **2. Mismatched Candidate** | Frontend Developer (React, TypeScript, CSS, UI design) | Senior Backend Engineer JD (Python, FastAPI, Postgres, Docker) | **0/6 Matched**, 6 Unmatched | **0/2 Matched**, 2 Unmatched | `all_must_haves_satisfied=False` |
| **3. Insufficient Experience** | Junior Software Engineer (1.5 yr experience, holds Python/Docker) | Senior Backend Engineer JD (5+ years experience required) | **5/6 Matched**, **1 Partial** (Experience Insufficient) | **0/2 Matched** | `all_must_haves_satisfied=False` (due to partial experience) |
| **4. Related Degree Compatibility** | Engineer with B.Tech in Electronics / IT | Software Engineer JD (BS Computer Science required) | **Degree: Partial** (`education_partial`) | All skill must-haves evaluated | Degree accepted partially; highlights field nuance |
| **5. Missing Critical Skill** | Backend Developer (Python, Django, AWS, but lacks Docker & Postgres) | Backend Engineer JD (Requires Python, FastAPI, Docker, Postgres) | **2/4 Skills Matched**, **2 Skills Unmatched** | Certifications & experience evaluated | Transparently pinpoints exact missing requirements |




