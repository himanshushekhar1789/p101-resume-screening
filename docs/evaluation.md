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


