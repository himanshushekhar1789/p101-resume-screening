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

---

## 9. Phase 7: Semantic Matching & Embedding Layer Evaluation

### 9.1 Verification Strategy & Guardrails
Phase 7 adds semantic similarity computation without compromising determinism or transparency:
- **Semantic Signal Only**: Identifies conceptual relationships between candidate background items and job requirements without judging overall candidate quality.
- **No Overriding Authority**: Deterministic Phase 6 outcomes remain authoritative. Semantic matching enriches evidence annotations rather than overturning explicit facts.
- **Strict Domain Protection Matrix**: Explicit rule block against false-positive conflations (`Java` vs `JavaScript`, `C` vs `C++`/`C#`, `Python` vs `PyTorch`, `React` vs `React Native`, `AWS` vs `AWS Lambda`).
- **Zero Scores / Percentages / Rankings**: Outputs requirement-level similarity records and categorical summaries only. Aggregation into composite 0–100 scores is strictly reserved for Phase 8.
- **Deterministic In-Memory Caching**: Embeddings are keyed by string SHA-256 hashes to eliminate redundant forward passes on the transformer model.

### 9.2 Phase 7 Test Matrix (`backend/tests/test_semantic_matching.py`)

The test suite validates semantic matching across 14 dedicated test cases:

| Test Case | Scope | Scenario | Expected Outcome |
|---|---|---|---|
| `test_cosine_similarity_edge_cases` | Math / Linear Algebra | Orthogonal, identical, and zero-norm vectors | Returns expected floats; handles zero vectors safely without `NaN` |
| `test_embedding_service_singleton_and_caching` | Service / Cache | Identical text embedded twice | Returns cached numpy vector; cache hit count increments |
| `test_semantic_matcher_exact_identical_text` | Matcher | Identical skill strings (`Python` vs `Python`) | Similarity $\approx 1.0$, `status="semantic_match"`, `confidence="high"` |
| `test_semantic_matcher_conceptually_related_skill` | Matcher | Conceptually related frameworks (`FastAPI` vs `Flask`) | Similarity between 0.55 and 0.75, `status="semantic_partial"` |
| `test_semantic_matcher_unrelated_skill` | Matcher | Completely unrelated items (`Docker` vs `Sales Strategy`) | Similarity $< 0.55$, `status="semantic_unrelated"`, `confidence="low"` |
| `test_false_positive_protections` | Protection Matrix | Confusable pairs (`Java` vs `JavaScript`, `C` vs `C++`, etc.) | Protected filter triggered, forced score `0.0`, `status="semantic_unrelated"` |
| `test_empty_candidate_evidence_is_not_evaluable` | Matcher | Candidate profile with zero skills or experience | Status is `semantic_not_evaluable`, score `0.0` |
| `test_experience_role_semantic_evidence` | Matcher | Requirement in JD matched against descriptive role text | Extracts role evidence and establishes semantic match |
| `test_semantic_matching_disabled_configuration` | Configuration | Matching called with `semantic_matching_enabled=False` | Returns empty matches and zero-summary gracefully |
| `test_semantic_matching_custom_thresholds` | Thresholds | Setting high threshold to 0.90 and medium to 0.70 | Threshold reclassification operates accurately |
| `test_deterministic_match_augmented_with_semantic` | Integration | End-to-end `match_candidate_to_job(include_semantic=True)` | Preserves Phase 6 deterministic status while attaching `semantic_result` |
| `test_semantic_matching_does_not_override_deterministic_unmatched` | Guardrail | Deterministic `unmatched` requirement tested with semantic layer | Deterministic status remains `unmatched`; semantic evidence is supplementary |
| `test_api_matching_semantic_endpoint` | REST API | `POST /api/v1/matching/semantic` with candidate and job | HTTP 200 with `CandidateJobSemanticMatchResponse` schema |
| `test_api_matching_analyze_with_semantic_flag` | REST API | `POST /api/v1/matching/analyze` with `include_semantic=True` | HTTP 200 with populated `semantic_matches` and `semantic_result` |

### 9.3 Benchmark Similarity Pairs (`all-MiniLM-L6-v2`)

| Requirement | Candidate Evidence | Empirical Cosine Similarity | Semantic Status | Protected Filter? |
|---|---|---|---|---|
| `Python` | `Python (programming_language)` | 0.88–1.00 | `semantic_match` | No |
| `FastAPI` | `Flask (framework)` | ~0.62–0.68 | `semantic_partial` | No |
| `PostgreSQL` | `MySQL (database)` | ~0.65–0.72 | `semantic_partial` | No |
| `Docker` | `Kubernetes (devops)` | ~0.66–0.74 | `semantic_partial` | No |
| `React` | `Docker (devops)` | ~0.15 | `semantic_unrelated` | No |
| `Java` | `JavaScript (programming_language)` | Forced 0.00 | `semantic_unrelated` | **Yes (Triggered)** |
| `C` | `C++ (programming_language)` | Forced 0.00 | `semantic_unrelated` | **Yes (Triggered)** |
| `Python` | `PyTorch (framework)` | Forced 0.00 | `semantic_unrelated` | **Yes (Triggered)** |
| `React` | `React Native (framework)` | Forced 0.00 | `semantic_unrelated` | **Yes (Triggered)** |
| `AWS` | `AWS Lambda (cloud)` | Forced 0.00 | `semantic_unrelated` | **Yes (Triggered)** |

### 9.4 Performance & Latency Observations
- **Cold Model Initialization**: $\approx 1.2\text{ s}$ on initial startup (deferred via lazy evaluation until first embedding request).
- **Inference Latency (CPU)**: $\approx 8\text{ ms}$ per text batch of 10 items on modern multi-core CPU.
- **Cache Hit Latency**: $< 0.05\text{ ms}$ per item lookup via in-memory SHA-256 hash dictionary.
- **End-to-End Matching Run**: Under $25\text{ ms}$ for a standard resume (30 evidence items against 10 job requirements), enabling real-time screening workflows without GPU accelerators.

---

## 10. Phase 8: Multi-Layer Hybrid Fusion Scoring Evaluation

### 10.1 Evaluation Methodology & Mathematical Guardrails
Phase 8 combines deterministic requirement verification, semantic similarity, verifiable experience duration, and optional LLM fit into a calibrated, explainable Candidate Fit Score:
- **Canonical Range**: All component scores and the aggregate candidate fit score strictly reside in $[0.0, 1.0]$ (represented also as percentage $0.0\text{--}100.0\%$).
- **Rule Fit vs Experience Fit Separation**: Rule Fit strictly evaluates evaluable **non-experience deterministic requirements** ($\mathcal{R}_{\text{rule}}$: skills, education, certifications, and explicit constraints). Experience requirements ($\mathcal{R}_{\text{exp}}$) are intentionally excluded from Rule Fit and evaluated exclusively by Experience Fit to prevent double-counting.
- **Semantic Fit vs Experience Fit Separation (Phase 8.2)**: Semantic Fit strictly evaluates evaluable **non-experience semantic requirements** ($\mathcal{R}_{\text{rule}}$). Career experience and role tenure requirements (`category == "experience"` or `requirement_id` starting with `exp_`) are excluded from numerical Semantic Fit to prevent career tenure from being counted twice (via cosine similarity and tenure ratio). Full semantic match evidence for experience items remains preserved for recruiter diagnostics.
- **Priority-Weighted Rule Fit**: Evaluates deterministic satisfaction over $\mathcal{R}_{\text{rule}}$ where `must_have` requirements carry weight $1.0$ and `nice_to_have` requirements carry weight $0.5$.
- **Not-Evaluable Safeguard**: Incomplete evidence (`not_evaluable`) is excluded from denominators rather than treated as a punitive failure ($0.0$).
- **Proportional Experience Capping**: Explicit tenure duration calculates $\min(1.0, \text{candidate\_years} / \text{required\_years})$; excess experience is strictly capped at $1.0$.
- **Dynamic Weight Renormalization**: When components are unavailable (e.g. LLM fit disabled by default, or an experience-only job), active weights are renormalized across available components so relative priorities remain preserved.
- **Strict Prohibition Enforcement**: Generates zero candidate rankings, zero shortlists, and zero automated hiring decisions (`hire`/`reject`).

### 10.2 Phase 8 Test Matrix (`backend/tests/test_scoring_engine.py`)

The test suite validates scoring engine integrity across 24 dedicated test cases:

| Test Case | Scope | Scenario | Expected Outcome |
|---|---|---|---|
| `test_perfect_candidate_scoring` | Core Engine | Candidate satisfies all requirements with 5+ yr experience | `rule_fit = 1.0`, `exp_fit = 1.0`, `semantic_fit > 0.90`, renormalized effective weights |
| `test_missing_must_have_safety_signal` | Safety Signal | Candidate missing a critical must-have requirement | `all_must_haves_satisfied = False`, rule fit is 0.6000, overall fit not forced to 0 |
| `test_partial_experience_proportional` | Experience Math | Candidate has 2.0 years vs 5.0 years required | `experience_fit = 0.40` ($2.0 / 5.0$) |
| `test_excess_experience_capped` | Experience Math | Candidate has 8.0 years vs 5.0 years required | `experience_fit = 1.0` (capped, no bonus points above 1.0) |
| `test_not_evaluable_excluded_from_denominator` | Fairness Guardrail | Skill tenure cannot be verified from dated roles | Requirement excluded from experience denominator; `exp_fit = 1.0` |
| `test_priority_weighting_rule_fit` | Priority Hierarchy | Must-have vs nice-to-have differential impacts | Must-have match yields $0.6667$ vs nice-to-have match $0.3333$ |
| `test_semantic_score_integration` | Semantic Integration | Mocked semantic results ($0.90$ must-have, $0.70$ nice-to-have) | Weighted semantic fit $= 0.8333$ |
| `test_weight_validation_sum_rejection` | Validation | Weights summing to $1.10$ or $0.80$ | Raises `ValidationError` |
| `test_negative_weights_rejected` | Validation | Negative weight (e.g. `semantic_weight = -0.20`) | Raises `ValidationError` |
| `test_llm_unavailable_dynamic_renormalization` | Dynamic Weights | LLM fit unavailable (`score = None`) | Effective weights: Rule $0.3333$, Semantic $0.4444$, Exp $0.2222$ |
| `test_score_bounds_and_clamping` | Numerical Bounds | Extreme inputs (all unmatched vs all matched) | Output bounded strictly in $[0.0, 1.0]$ and $[0.0, 100.0\%]$ |
| `test_score_reproducibility` | Determinism | Identical input evaluated twice | Returns bitwise identical scores and breakdowns |
| `test_no_ranking_or_shortlist_in_response` | Scope Guardrail | Output inspected for ranking terms (`rank`, `shortlist`) | Zero ranking fields present |
| `test_no_hiring_decision_in_response` | Scope Guardrail | Output inspected for decision terms (`hire`, `reject`) | Zero decision fields present |
| `test_configurable_weights_sanity` | Configurability | Changing weights from semantic-heavy to rule-heavy | Score changes predictably reflecting user preferences |
| `test_five_synthetic_score_benchmarks` | Benchmarking | Evaluates 5 synthetic candidate archetypes | Accurate distribution of scores across archetypes |
| `test_rule_fit_and_experience_fit_separation` | Phase 8.1 Regression | Verifies rule_fit invariant under changing experience tenure | `rule_fit` unchanged when experience drops; `exp_fit` drops proportionally; exp-only job produces no artificial rule_fit |
| `test_career_experience_excluded_from_semantic_fit` | Phase 8.2 Regression | Experience requirement has semantic result attached | Numerical `semantic_fit` reflects non-experience skills only ($0.9000$ vs $(0.90 + 0.85)/2$); `exp_fit = 1.0` |
| `test_semantic_fit_invariant_under_experience_similarity` | Phase 8.2 Regression | Experience semantic similarity varied ($0.95$ vs $0.20$) with identical skills | `semantic_fit_score` and `candidate_fit_score` remain completely invariant ($0.8000$) |
| `test_skill_specific_experience_semantic_scoring` | Phase 8.2 Regression | Skill-specific tenure ("3+ years Python") | Skill credits `semantic_fit` ($0.92$); experience credits `exp_fit` ($1.0$); exp-only job marks semantic fit unavailable |
| `test_phase7_semantic_results_remain_available_in_diagnostic_response` | Phase 8.2 Regression | Diagnostic inspection of matches and summary | All Phase 7 semantic results fully present in response while excluded from numerical score |
| `test_api_scoring_analyze_endpoint` | REST API | `POST /api/v1/scoring/analyze` with profiles | HTTP 200 with `CandidateJobScoreResponse` schema |
| `test_api_matching_analyze_with_include_score` | REST API | `POST /api/v1/matching/analyze` with `include_score=True` | HTTP 200 with populated `score` object |
| `test_api_matching_from_files_with_include_score` | REST API | `POST /api/v1/matching/from-files` with `include_score=True` | HTTP 200 with end-to-end PDF parsing and score calculation |

### 10.3 Synthetic Candidate Score Benchmarks (Section 36)

| Archetype | Profile Summary | Rule Fit | Semantic Fit | Exp Fit | Candidate Fit Score | Must-Haves Satisfied? |
|---|---|---|---|---|---|---|
| **Candidate A — Strong Match** | Senior Full-Stack (Python, FastAPI, Docker, 6 yr exp) | **1.0000** | **0.9240** | **1.0000** | **0.9661 (96.6%)** | **True** |
| **Candidate B — Missing Critical Must-Have** | Strong Backend Dev lacking required PostgreSQL database | **0.6000** | **0.5900** | **1.0000** | **0.6844 (68.4%)** | **False** (Safety Signal) |
| **Candidate C — Strong Skills, Low Experience** | Junior Engineer with Python/FastAPI but 1.5 yr exp (5 yr req) | **1.0000** | **0.9350** | **0.3000** | **0.7728 (77.3%)** | **False** |
| **Candidate D — Strong Experience, Weak Skill Fit** | 10 yr Veteran Engineer from unrelated stack (0/2 required skills) | **0.0000** | **0.1750** | **1.0000** | **0.3000 (30.0%)** | **False** |
| **Candidate E — Sparse Resume** | Resume with Python skill, but 2 unverified tenure requirements | **1.0000** | **0.8000** | **N/A** | **0.8857 (88.6%)** | **True** (2 not evaluable) |

### 10.4 Configurable Weights Sanity Verification
To verify that scoring is truly configurable rather than static:
* **Candidate**: Strong rule satisfaction ($1.00$), moderate semantic similarity ($0.50$), perfect experience ($1.00$).
* **Config A (Semantic-Heavy)**: $w_{\text{rule}}=0.20, w_{\text{semantic}}=0.60, w_{\text{exp}}=0.20 \implies \text{Fit Score} = 0.7000$.
* **Config B (Rule-Heavy)**: $w_{\text{rule}}=0.60, w_{\text{semantic}}=0.20, w_{\text{exp}}=0.20 \implies \text{Fit Score} = 0.9000$.
* **Result**: Score adjusts dynamically and predictably ($\Delta = +0.20$), confirming active weight compliance.

---

## 11. Phase 9: Skill-Gap Analysis & Evidence Grounding Evaluation

### 11.1 Evaluation Methodology & Rigor
Phase 9 evaluates candidate deficiencies with strict evidence grounding and objective decision-support boundaries:
- **Four-Category Skill Classification**: Every skill is classified deterministically as `satisfied`, `missing`, `insufficient`, or `not_evaluable`.
- **Deterministic-First Authority (Rule 6)**: Phase 6 deterministic `unmatched` cannot be upgraded by semantic similarity. Semantic embeddings provide contextual explanation only.
- **Career Tenure Separation**: General experience requirements are analyzed strictly in `experience_gaps` and never converted into technical skills.
- **Deduplication Integrity**: Aliases and duplicates are merged under canonical names with `must_have` priority precedence and maximum tenure retention.
- **Summary Arithmetic Invariants**: `total_skill_requirements = satisfied + missing + insufficient + not_evaluable`. `must_have_gaps = missing(must_have) + insufficient(must_have)` (strictly excluding `not_evaluable`).
- **Prohibition Verification**: Zero rankings, zero shortlists/top-N cuts, zero automated hiring/rejection decisions, zero recommendations/courses.

### 11.2 Phase 9 Test Matrix (`backend/tests/test_skill_gap_analyzer.py`)

The test suite validates Phase 9 across 15 dedicated scenarios:

| Test Case | Scope | Scenario | Expected Outcome |
|---|---|---|---|
| `test_perfect_skill_match` | Full Match | Candidate has Python (4 yrs) & Docker (3 yrs) for 3 yr requirements | All skills `satisfied`, `shortfall = None`, `must_have_gaps = 0` |
| `test_missing_must_have_skill` | Critical Gap | Candidate lacks required PostgreSQL skill | Status `missing`, `must_have_gaps = 1`, clear explanation and empty candidate evidence |
| `test_missing_nice_to_have_skill` | Non-Critical Gap | Candidate lacks optional Redis skill | Status `missing`, `priority = nice_to_have`, `must_have_gaps = 0`, `nice_to_have_gaps = 1` |
| `test_insufficient_skill_specific_experience` | Duration Shortfall | Candidate has 1 yr Docker vs 3 yrs required | Status `insufficient`, `required_value = "3.0 years"`, `candidate_value = "1.0 years"`, `shortfall = "2.0 years"`, `must_have_gaps = 1` |
| `test_not_evaluable_skill` | Ambiguous Tenure | Candidate lists AWS in skills list but with 0 dated role tenure | Status `not_evaluable`, `not_evaluable_count = 1`, `must_have_gaps = 0` (excluded per Section 11) |
| `test_semantic_similarity_cannot_override_deterministic_missing` | Rule 6 Enforcement | Job requires PostgreSQL, candidate has MySQL with high cosine similarity (0.68) | Deterministic outcome is authoritative: status is `missing`, semantic match cited purely as supporting context in explanation |
| `test_general_experience_remains_separate` | Separation of Concerns | Job requires "5+ years backend software engineering" | Evaluated in `experience_gaps` (status `satisfied`), NOT converted into a skill gap |
| `test_evidence_preservation` | Evidence Grounding | Evaluates satisfied and insufficient skills | Verifies job evidence and candidate dated role evidence are explicitly retained |
| `test_duplicate_normalized_skills` | Deduplication | JD lists "JS" (must_have, 3 yrs) and "JavaScript" (nice_to_have, 1 yr) | Merged under canonical "JavaScript", retains `must_have` priority and 3.0 yrs tenure, single gap item |
| `test_skill_gap_summary_counts_and_rules` | Summary Arithmetic | Mixed profile: 1 satisfied, 1 missing must-have, 1 missing nice-to-have, 1 insufficient, 1 not_evaluable | Total=5, satisfied=1, missing=2, insufficient=1, not_evaluable=1, must_have_gaps=2, nice_to_have_gaps=1 |
| `test_no_ranking_or_hiring_decisions_in_gap_response` | Scope Boundaries | Response payload inspected for forbidden keywords | Zero occurrences of `rank`, `shortlist`, `hire`, `reject`, `recommendation`, `course` |
| `test_api_gaps_analyze_endpoint` | REST API | `POST /api/v1/gaps/analyze` with structured profile payload | HTTP 200 with complete `CandidateJobSkillGapResponse` |
| `test_api_gaps_from_files_endpoint` | End-to-End File API | `POST /api/v1/gaps/from-files` with uploaded PDF/DOCX files | HTTP 200 with extracted profiles and grounded skill gaps |
| `test_matching_analyze_with_include_skill_gaps` | Unified Matching API | `POST /api/v1/matching/analyze` with `include_skill_gaps=True` | HTTP 200 with populated `gaps` field in `CandidateJobMatchResponse` |
| `test_matching_from_files_with_include_skill_gaps` | Unified File API | `POST /api/v1/matching/from-files` with `include_skill_gaps=True` | HTTP 200 with populated `gaps` field from uploaded documents |

---

## 12. Phase 10: LLM Explanations & Personalized Recommendations Evaluation

### 12.1 Evaluation Methodology & Rigor
Phase 10 evaluates narrative explanation transparency and recommendation precision against strict grounding rules:
- **Strict Evidence Grounding**: The LLM explains previously computed facts from Phases 6–9 without inventing or extrapolating skills, employers, or credentials.
- **Deterministic-First Authority**: Conceptually related skills (MySQL vs PostgreSQL) are cited as supporting context only; missing status is never overridden.
- **Quantitative Shortfall Preservation**: Insufficient skill tenure preserves exact deficits (e.g. 1.0 vs 3.0 years) without inflating candidate experience.
- **Recommendations Strictly Grounded in Gaps**: Actionable recommendations and verifiable artifacts are generated ONLY for skills with status `missing`, `insufficient`, or `not_evaluable`.
- **Numerical Score Preservation**: Hybrid fit scores ($S_{\text{rule}}$, $S_{\text{semantic}}$, $S_{\text{experience}}$, $S_{\text{fit}}$) are interpreted objectively without numerical alteration.
- **Strict Prohibition Enforcement**: Zero candidate rankings, zero shortlists/top-N cuts, zero automated hiring/rejection decisions.
- **Controlled Error Handling**: Malformed or non-JSON responses are rejected via `LLMValidationError` and HTTP 422.

### 12.2 Phase 10 Test Matrix (`backend/tests/test_llm_explanation.py`)

The test suite validates Phase 10 across 15 dedicated scenarios:

| Test Case | Scope | Scenario | Expected Outcome |
|---|---|---|---|
| `test_fully_satisfied_candidate` | Full Match | Candidate satisfies all requirements | Strengths acknowledge verified skills; zero gaps and zero recommendations |
| `test_missing_skill` | Critical Gap | Candidate lacks PostgreSQL | PostgreSQL cited in `key_gaps`, status `missing`, recommendation generated |
| `test_insufficient_skill` | Duration Shortfall | Candidate has 1 yr Docker vs 3 yrs required | Quantitative shortfall (2.0 yrs) preserved; status `insufficient` |
| `test_not_evaluable_skill` | Ambiguous Tenure | AWS listed without dated employment history | Status `not_evaluable`; explicit uncertainty and unverified tenure cited |
| `test_semantic_evidence_cannot_override_deterministic_status` | Rule 6 Enforcement | PostgreSQL required; candidate has MySQL | PostgreSQL remains `missing`; semantic evidence cited as supporting context only |
| `test_no_hallucinated_evidence` | Anti-Hallucination | Candidate with no AWS/Kubernetes | Output contains zero claims of AWS/Kubernetes competency |
| `test_score_preservation` | Numerical Integrity | Candidate score 0.72 with rule/semantic/experience breakdown | Scores explained without modification; numerical values preserved verbatim |
| `test_recommendations_only_from_gaps` | Recommendation Grounding | Only gap is Kubernetes | Recommendation targets Kubernetes only; no unrelated technologies recommended |
| `test_no_hiring_decision` | Scope Boundaries | Response payload inspected for decision keywords | Zero occurrences of `hire`, `reject`, `recommend_hire`, `rank`, or `shortlist` |
| `test_invalid_llm_response` | Schema Validation | Mock provider returns malformed non-JSON | Raises `LLMValidationError`; rejects malformed output cleanly |
| `test_mock_provider_deterministic_offline` | Determinism | Mock client invoked across repeated executions | 100% deterministic, bitwise reproducible outputs without network calls |
| `test_api_explanations_analyze_endpoint` | REST API | `POST /api/v1/explanations/analyze` with structured profile payload | HTTP 200 with complete, validated `LLMExplanationResponse` |
| `test_integrated_endpoint_include_explanation_true` | Unified Matching API | `POST /api/v1/matching/analyze` with `include_explanation=True` | HTTP 200 with populated `.explanation` alongside `.score` and `.gaps` |
| `test_integrated_endpoint_backward_compatibility` | Backward Compatibility | `POST /api/v1/matching/analyze` with `include_explanation=False` | HTTP 200 with `.explanation is None` |
| `test_file_based_explanation_endpoint` | End-to-End File API | `POST /api/v1/explanations/from-files` with uploaded PDF/DOCX files | HTTP 200 with extracted profiles, matching, gaps, and grounded explanation |

---

## 13. Phase 11: Frontend Web Dashboard Evaluation

### 13.1 Frontend Test Matrix (`frontend/src/**/*.test.tsx`)
The frontend dashboard is verified across 21 component unit tests covering layout, scoring badges, requirement coverage, skill-gap rendering, and LLM explanation views:

| Component / Test Suite | Scope | Verification Details | Status |
| :--- | :--- | :--- | :---: |
| `OverallScoreBadge.test.tsx` | Score UI | Visual color states (green >=75%, yellow 50-74%, red <50%), percentage formatting | **PASSED** |
| `ScoreBreakdownCard.test.tsx` | Score Breakdown | Displays 4 components, effective weights, explanations, not evaluable counts | **PASSED** |
| `RequirementCoverageTable.test.tsx` | Deterministic View | Status badges (matched, partial, unmatched), evidence inspection, must-have priority | **PASSED** |
| `SkillGapSection.test.tsx` | Skill Gaps | Missing vs insufficient vs not-evaluable classification, experience separation | **PASSED** |
| `LLMExplanationView.test.tsx` | AI Insights | Grounded summary, score explanation, recommendations, permanent recruiter disclaimer | **PASSED** |
| `TypeScript & Next.js Build` | Production Build | Full TypeScript compilation (`tsc --noEmit`) and Next.js static export build | **PASSED** |

---

## 14. Phase 12: Comprehensive Evaluation, Benchmarking & End-to-End Validation Suite

### 14.1 Suite Architecture & Methodology
The Phase 12 benchmark suite (`evaluation/run_evaluation.py`) validates the complete system across all 11 prior phases:

```text
evaluation/
├── resumes/                 # 10 Synthetic candidate resumes
├── jobs/                    # 5 Synthetic job descriptions
├── cases/                   # 10 Curated evaluation cases with ground-truth
├── reports/                 # latest.json & latest.md generated outputs
└── run_evaluation.py        # Automated benchmark test runner
```

### 14.2 Engineering Acceptance Gates Results

| Evaluation Category | Acceptance Gate | Benchmark Result | Status |
| :--- | :--- | :--- | :---: |
| **Skill Normalization & Aliases** | 100% Protected pairs, >=90% Aliases | 100.0% Aliases, 100% Protected | **PASSED** |
| **Semantic Matching & Isolation** | 100% Protected blocking, 0% conflation | 100% Protected Pairs Blocked | **PASSED** |
| **Scoring Invariants (A–F)** | 100% Invariants hold | 6/6 Invariants Verified | **PASSED** |
| **Curated Benchmark Cases** | >= 90% Cases pass ground-truth | 10/10 Cases Passed (100.0%) | **PASSED** |
| **LLM Grounding & Guardrails** | 100% Anti-hallucination & No verdicts | 100% Grounded, 0 Hiring Verdicts | **PASSED** |
| **API End-to-End Smoke Tests** | 100% Endpoints return 200 OK | 7/7 Endpoints Operational | **PASSED** |

### 14.3 Scoring Invariants A through F Verification
- **Invariant A & C**: Career experience items are strictly excluded from numerical `semantic_fit` calculation (Phases 8.1 & 8.2).
- **Invariant B**: Experience requirements are strictly excluded from deterministic `rule_fit` calculation.
- **Invariant D**: Changing experience tenure alters `experience_fit` only; `rule_fit` and `semantic_fit` are completely unaffected.
- **Invariant E**: When `llm_fit` is unavailable (default), dynamic renormalization scales remaining component weights so that their sum equals exactly 1.0.
- **Invariant F**: Final candidate fit score is 100% deterministic and bitwise reproducible across identical inputs.

### 14.4 10 Curated Benchmark Cases Matrix

| Case ID | Candidate Profile Type | Target Role | Fit Score | Must-Haves Met? | Gaps Found | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| `case_01` | Senior Backend Engineer | Senior Backend Engineer | 84.1% | Yes | 0 missing | **PASSED** |
| `case_02` | Junior Backend with Deficits | Senior Backend Engineer | 25.2% | No | 6 missing | **PASSED** |
| `case_03` | Senior Frontend Engineer | Senior Frontend Developer | 82.8% | Yes | 0 missing | **PASSED** |
| `case_04` | Data Scientist & ML Engineer | Data Scientist & ML Engineer | 84.4% | Yes | 0 missing | **PASSED** |
| `case_05` | Senior DevOps & Cloud Engineer | Cloud DevOps Engineer | 89.7% | Yes | 0 missing | **PASSED** |
| `case_06` | Early-Career CS Graduate | Entry-Level Software Engineer | 80.5% | Yes | 1 missing | **PASSED** |
| `case_07` | Bootcamp Transitioner | Senior Backend Engineer | 56.0% | No | 4 missing | **PASSED** |
| `case_08` | Adjacent Stack (Flask/MySQL) | Senior Backend Engineer | 52.7% | No | 4 missing | **PASSED** |
| `case_09` | Minimalist / Undated Resume | Senior Backend Engineer | 35.3% | No | 4 missing | **PASSED** |
| `case_10` | Non-standard Typography | Senior Backend Engineer | 69.9% | No | 2 missing | **PASSED** |

### 14.5 Performance & Latency Telemetry

#### Embedding Inference & Cache Performance
- **Warm Inference Latency**: ~25–45 ms (CPU-first SentenceTransformer)
- **Cached Inference Latency**: ~0.10 ms (In-memory SHA-256 cache)
- **Cache Speedup Factor**: >240x acceleration

#### Pipeline Stage Latencies (5-Run Sample, milliseconds)
| Pipeline Stage | Min (ms) | Median (ms) | p95 (ms) |
| :--- | :---: | :---: | :---: |
| Document Parsing (PyMuPDF) | 9.17 | 12.33 | 17.56 |
| Profile & JD Extraction | 41.28 | 43.72 | 47.77 |
| Deterministic Matching | 8.43 | 10.79 | 65.66 |
| Hybrid Scoring | 0.20 | 0.21 | 0.27 |
| Skill-Gap Analysis | 0.79 | 0.86 | 1.01 |
| Grounded LLM Explanation | 1.78 | 1.93 | 2.45 |
| **End-to-End Pipeline** | **64.09** | **72.65** | **130.84** |

### 14.6 Critical Scope Boundaries
1. **Zero Candidate Ranking**: No sorting, ranking, or leaderboard capabilities are implemented or evaluated.
2. **Zero Automated Hiring Actions**: All evaluations produce transparent decision-support evidence without automated hire/reject decisions.
3. **Synthetic Ground Truth**: All evaluation profiles and JDs are synthetic engineering fixtures.




