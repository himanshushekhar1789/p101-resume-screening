# P_101 — LLM-Based Resume Screening System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00.svg?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> An academic-grade, production-quality AI-assisted resume screening and candidate decision-support system featuring multi-layer hybrid scoring, grounded evidence citations, skill-gap analysis, and bias-reduction masked screening.

---

## Documentation & Demonstration Quick Links

* 📄 **[Final Technical Project Report](docs/final-project-report.md)**: Comprehensive 29-section academic report (Problem Statement, Architecture, Scoring Formulations, Benchmark Gates, Ethical Guardrails).
* 🏛️ **[System Architecture Guide](docs/architecture.md)**: Deep dive into pipeline decoupling, false-positive protection matrix, and mathematical scoring invariants.
* 📊 **[Evaluation & Benchmark Suite](docs/evaluation.md)**: Synthetic dataset (10 resumes, 5 JDs, 10 curated cases), scoring invariants (A–F), and pipeline latency telemetry.
* 🎬 **[Live Demo Guide](docs/demo.md)**: 5–7 minute click-by-click live presentation script with talking points and UI inspection cues.
* ✅ **[Demo Checklist & Viva Q&A](docs/demo-checklist.md)**: Pre-flight checklist and authoritative answers to common evaluation and viva defense questions.
* 📑 **[Master Documentation Index](docs/README.md)**: Complete directory of all project technical documentation and evaluation reports.

---

## 1. System Vision & Objective

Traditional Applicant Tracking Systems (ATS) rely either on brittle keyword matching (missing qualified candidates who use synonyms) or opaque black-box LLM scoring (hallucinating qualifications and exhibiting unexplainable bias). 

**P_101** introduces a **transparent, hybrid decision-support architecture**:
- **Decision-Support Tool**: It does **not** make unquestionable hiring decisions. The human reviewer remains responsible for the final hiring decision.
- **Transparent Multi-Layer Hybrid Scoring**:
  - **Rule Fit (30%)**: Verifiable hard criteria (mandatory skills, minimum education, required experience).
  - **Semantic Skill Fit (40%)**: Embeddings and skill normalization (`Sentence Transformers`, cosine similarity).
  - **Experience Fit (20%)**: Depth of project and tenure alignment against JD scope.
  - **LLM-Supported Fit (10%)**: Structured evidence synthesis and qualification reasoning.
- **Evidence-Grounded Explanations**: Matches cite actual lines from the resume text—no fabricated qualifications.
- **Skill-Gap Analysis & Actionable Learning Roadmaps**: Pinpoints matched, partially matched, and missing skills with customized project/learning recommendations.
- **Fairness & Privacy First**: Includes a **Masked Screening Mode** that redacts candidate names, gender signals, institutions, and photos to prevent unconscious bias.

---

## 2. System Architecture

```
Frontend (Next.js / React + Tailwind CSS)
   │
   ▼ HTTP REST
FastAPI Backend (/api/v1)
   │
   ├── Configuration (.env / Pydantic Settings)
   ├── Database Layer (SQLAlchemy ORM: SQLite for MVP, PostgreSQL for Production)
   │
   └── Application Pipeline Services:
       ├── 1. Document Extraction (PyMuPDF for PDF, python-docx for DOCX)
       ├── 2. Information Extraction (spaCy + Rule Matcher + Regex)
       ├── 3. PII Masking Engine (Redacts personal identifiers in Masked Mode)
       ├── 4. Job Description Analyzer (Mandatory vs. Preferred taxonomy)
       ├── 5. Rule Filter Engine (Deterministic hard filters)
       ├── 6. Semantic Matching Engine (Dense vector embeddings & Cosine similarity)
       ├── 7. Multi-Layer Hybrid Fusion (Configurable weights & sub-scores)
       ├── 8. Skill-Gap & Evidence Analyzer (Citations & gap classification)
       ├── 9. LLM Recommendation Engine (Provider abstraction: Gemini, OpenAI, Mock)
       └── 10. Reporting & CSV Export (Pandas)
```

---

## 3. Resume Document Processing (Phase 2)

The system ingests candidate documents and transforms them into clean, structured text representations without premature AI manipulation.

### Supported Formats & Extraction Engines
- **PDF (`.pdf`)**: Extracted via **PyMuPDF** (`pymupdf`).
  - Reads all document pages in sequence.
  - Sorts text blocks (`sort=True`) to maintain natural reading order across multi-column layouts.
  - Detects scanned / image-only PDFs that lack a text layer and raises a clear `422 Unprocessable Content` error (OCR is out of scope for this phase).
- **DOCX (`.docx`)**: Extracted via **python-docx**.
  - Interleaves body paragraphs and table elements in natural document order.
  - Deduplicates merged table cells to prevent duplicate noise.
  - Rejects empty or corrupt DOCX files with informative `400 Bad Request` errors.
- **Unsupported Formats**: Automatically rejected (`.jpg`, `.png`, `.txt`, `.xlsx`, `.zip`, executables) with `400 Bad Request`.

### Document Parsing API Example

#### Request (`POST /api/v1/resumes/parse`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/resumes/parse" \
     -F "file=@sample_resume.pdf"
```

#### Response (`200 OK`)
```json
{
  "filename": "sample_resume.pdf",
  "file_type": "pdf",
  "page_count": 1,
  "character_count": 160,
  "word_count": 20,
  "text": "Alex Rivera\nSenior Full Stack Developer\nSkills: Python, FastAPI, React, PostgreSQL, Docker\nExperience: 5 years at TechCorp designing cloud-native microservices."
}
```

---

## 4. Structured Resume Extraction (Phase 3)

The raw text extracted from documents is analyzed through a layered architecture to build a validated `CandidateProfile`:

1. **Deterministic Rule Extraction**:
   - **Contact & Identifiers**: Extracts clean email addresses, telephone numbers, and profile URLs (LinkedIn, GitHub) via regex.
   - **Section Segmentation**: Locates and segments resume sections (Summary, Technical Skills, Experience, Education, Projects, Certifications, Achievements) using header heuristics.
2. **LLM Reasoning & Provider Abstraction**:
   - Provider abstraction supporting **Google Gemini** (`gemini-1.5-flash`), **OpenAI** (`gpt-4o-mini`), and an offline **Mock Client**.
   - Centralized, versioned prompt template (`backend/app/ai/prompts/resume_extraction.txt`).
   - Strict zero-hallucination instructions: extracts only explicit facts, preserves nulls for missing values, and categorizes skills.
3. **Pydantic Validation & Ground-Truth Reconciliation**:
   - Cleans JSON strings, strips markdown formatting, and validates against `CandidateProfile`.
   - Merges deterministic regex findings to safeguard against omission.

### Supported Profile Fields
- **Personal Info**: `name`, `email` (RFC format-validated), `phone` (standardized string), `location`, `linkedin_url`, `github_url`.
- **Summary**: Professional summary / career objective.
- **Skills**: Skill list with category classification (`programming_language`, `framework`, `database`, `tool`, `cloud`, `devops`, `ai_ml`, `other`).
- **Education**: Degree, institution, field of study, start/end years, grade.
- **Experience**: Job title, company, location, start/end dates, current role flag, description, skills mentioned.
- **Projects**: Project title, description, technologies used, URL, dates.
- **Certifications**: Credential name, issuing organization, dates, credential ID.
- **Achievements**: Awards, competitions, publications.

### Extraction API Example (Phase 3 & 3.1 Hardened)

#### Request (`POST /api/v1/resumes/extract`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/resumes/extract" \
     -F "file=@data/sample/resumes/synthetic_software_engineer.pdf"
```

#### Response (`200 OK`)
```json
{
  "filename": "synthetic_software_engineer.pdf",
  "file_type": "pdf",
  "profile": {
    "personal_info": {
      "name": "David Vance",
      "email": "david.vance@example-dev.org",
      "phone": "+1 (555) 234-5678",
      "location": null,
      "linkedin_url": "https://linkedin.com/in/david-vance-dev",
      "github_url": "https://github.com/davidvance"
    },
    "summary": "Backend Software Engineer with 5+ years building scalable microservices using Python, FastAPI, and PostgreSQL.",
    "skills": [
      { "name": "Python", "category": "programming_language" },
      { "name": "SQL", "category": "database" },
      { "name": "FastAPI", "category": "framework" },
      { "name": "Django", "category": "framework" },
      { "name": "PostgreSQL", "category": "database" },
      { "name": "Redis", "category": "database" },
      { "name": "Git", "category": "tool" },
      { "name": "AWS", "category": "cloud" },
      { "name": "Docker", "category": "devops" },
      { "name": "Kubernetes", "category": "devops" },
      { "name": "REST APIs", "category": "other" },
      { "name": "Microservices", "category": "other" }
    ],
    "education": [
      {
        "degree": "B.Tech",
        "institution": "State Tech University",
        "field": "Computer Science",
        "start_year": 2015,
        "end_year": 2019,
        "grade": null
      }
    ],
    "experience": [
      {
        "title": "Senior Software Engineer",
        "company": "CloudCorp",
        "location": null,
        "start_date": "2022",
        "end_date": null,
        "is_current": true,
        "description": "Designed and maintained high-throughput REST APIs using FastAPI and PostgreSQL. Containerized microservice deployments with Docker and Kubernetes.",
        "skills": ["Fastapi", "Postgresql", "Docker", "Kubernetes", "Rest Apis"]
      },
      {
        "title": "Software Developer",
        "company": "AppLabs",
        "location": null,
        "start_date": "2019",
        "end_date": "2022",
        "is_current": false,
        "description": "Built backend business logic in Python and optimized SQL relational queries.",
        "skills": ["Python", "Sql"]
      }
    ],
    "projects": [
      {
        "name": "E-Commerce Microservices",
        "description": "Scalable distributed order processing engine built with FastAPI and Docker.",
        "technologies": ["Fastapi", "Docker"],
        "url": null,
        "start_date": null,
        "end_date": null
      }
    ],
    "certifications": [
      {
        "name": "AWS Certified Solutions Architect",
        "issuing_organization": "Amazon Web Services",
        "issue_date": "2023",
        "credential_id": null,
        "url": null
      }
    ],
    "achievements": []
  },
  "extraction_metadata": {
    "character_count": 1098,
    "word_count": 138,
    "page_count": 1,
    "llm_provider": "mock"
  }
}
```

---

## 5. Job Description Analysis & Requirement Extraction (Phase 4)

Unstructured Job Descriptions (raw text JSON or PDF/DOCX uploads) are parsed and converted into a structured, validated `JobProfile`:

1. **Dual Input Methods**:
   - **Direct JSON (`POST /api/v1/jobs/analyze`)**: Ingests raw text payloads directly from applicant systems or recruiters.
   - **Document Upload (`POST /api/v1/jobs/analyze/upload`)**: Reuses Phase 2 document parsing for PDF and DOCX job postings.
2. **Deterministic & Rule-Based Heuristics**:
   - **Section Segmentation**: Detects Summary, Responsibilities, Minimum/Required Qualifications, Preferred Qualifications, Education, and Experience.
   - **Priority Disambiguation**: Categorizes qualifications into `must_have` vs. `nice_to_have` by recognizing mandatory clauses ("must have", "required", "minimum of") versus optional indicators ("plus", "preferred", "bonus").
   - **Numeric Extraction**: Standardizes minimum years of experience and isolates general experience from skill-specific tenure.
   - **Degree & Certification Matching**: Disambiguates degree acronyms from common verbs (e.g., distinguishing "B.E." from "be") and extracts credential requirements.
   - **Responsibilities Isolation**: Keeps primary day-to-day duties cleanly isolated from candidate qualification requirements.
3. **LLM Extraction & Ground-Truth Reconciliation**:
   - Versioned prompt (`backend/app/ai/prompts/job_extraction.txt`) grounded on zero-hallucination principles.
   - Post-reconciliation overrides false must-haves when cited evidence denotes optionality ("is a plus"), harmonizes categories, and auto-populates flattened `must_have` / `nice_to_have` summary lists.

### Supported Job Profile Fields
- **Metadata**: `title`, `department`, `location`, `employment_type`, `summary`.
- **Responsibilities**: Clean list of primary job duties (`List[str]`).
- **Skills Requirements**: Name, category, priority (`must_have` / `nice_to_have`), minimum years, and original source context.
- **Experience Requirements**: Minimum years, required domain/scope, and priority.
- **Education Requirements**: Minimum degree level, accepted fields of study, and mandatory flag.
- **Certification Requirements**: Name, issuing organization, and priority.
- **Summary Collections**: Flattened string lists of `must_have` and `nice_to_have` qualifications for fast scoring and rule filtering.

### Job Description Analysis API Examples

#### 1. Analyze Raw Text JD (`POST /api/v1/jobs/analyze`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/jobs/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Senior Backend Engineer",
       "text": "Responsibilities:\n- Design scalable APIs.\n\nRequirements:\n- 5+ years of experience with Python and FastAPI.\n- Bachelor'\''s degree in Computer Science.\n- Experience with AWS and Docker is a plus."
     }'
```

#### 2. Analyze Uploaded Document JD (`POST /api/v1/jobs/analyze/upload`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/jobs/analyze/upload" \
     -F "file=@data/sample/job_descriptions/backend_engineer_jd.pdf"
```

#### Sample Response (`200 OK`)
```json
{
  "title": "Senior Backend Engineer",
  "profile": {
    "title": "Senior Backend Engineer",
    "department": null,
    "location": null,
    "employment_type": null,
    "summary": "Backend engineering role designing high-throughput services.",
    "responsibilities": [
      "Architect and build scalable backend microservices.",
      "Design relational schemas and optimize complex SQL queries."
    ],
    "skills": [
      {
        "name": "Python",
        "category": "programming_language",
        "priority": "must_have",
        "minimum_years": 5.0,
        "context": "5+ years of experience with Python and FastAPI"
      },
      {
        "name": "FastAPI",
        "category": "framework",
        "priority": "must_have",
        "minimum_years": 5.0,
        "context": "5+ years of experience with Python and FastAPI"
      },
      {
        "name": "AWS",
        "category": "cloud",
        "priority": "nice_to_have",
        "minimum_years": null,
        "context": "Experience with AWS and Docker is a plus"
      }
    ],
    "experience": [
      {
        "role_or_domain": "Backend Software Engineering",
        "minimum_years": 5.0,
        "priority": "must_have",
        "context": "5+ years backend software development experience"
      }
    ],
    "education": {
      "degree_level": "Bachelor's",
      "fields_of_study": ["Computer Science", "Software Engineering"],
      "is_required": true,
      "context": "Bachelor's degree in Computer Science or related field required"
    },
    "certifications": [],
    "other_requirements": [],
    "must_have": [
      "5.0+ years of experience in Backend Software Engineering",
      "Python (programming_language)",
      "FastAPI (framework)",
      "Education: Bachelor's in Computer Science, Software Engineering"
    ],
    "nice_to_have": [
      "AWS (cloud)"
    ]
  },
  "metadata": {
    "character_count": 845,
    "word_count": 112,
    "page_count": 1,
    "llm_provider": "mock"
  }
}
```

---

## 6. Skill Normalization & Taxonomy Mapping (Phase 5)

Phase 5 establishes a common, machine-comparable canonical representation for skills across resumes and job descriptions:

1. **Deterministic Skill Standardization**:
   - Case & whitespace normalization (`PYTHON`, `  python  ` $\rightarrow$ `Python`).
   - Conservative alias resolution (`JS` $\rightarrow$ `JavaScript`, `K8s` $\rightarrow$ `Kubernetes`, `GCP` $\rightarrow$ `Google Cloud`, `NLP` $\rightarrow$ `Natural Language Processing`).
   - Version stripping (`Python 3.11` $\rightarrow$ `Python`, `React 18` $\rightarrow$ `React`).
   - Punctuation sensitivity (`C++` $\neq$ `C`, `C#` $\neq$ `C`, `.NET` $\neq$ `Node.js`).
2. **Authoritative Taxonomy Categories**:
   - Strictly enforces 10 canonical categories: `programming_language`, `framework`, `library`, `database`, `tool`, `cloud`, `devops`, `ai_ml`, `soft_skill`, `other`.
3. **Deduplication with Provenance**:
   - Preserves all original strings in `original_names` (e.g. `['Python', 'python', 'Python 3']`).
   - For job descriptions, merges duplicate requirements with `must_have` precedence and maximum required years of experience.
4. **Zero-Hallucination Unknown Skill Protection**:
   - Unregistered skills retain their clean original text with `normalization_method="unknown"` and `confidence=0.5`.
5. **False-Positive Word Guard**:
   - Prevents ordinary resume/JD words (`experience`, `work`, `team`, `cloud`, `data`) occurring alone from becoming technical skills.

### Skill Normalization API Examples

#### 1. Standalone Skill Normalization (`POST /api/v1/skills/normalize`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/skills/normalize" \
     -H "Content-Type: application/json" \
     -d '{
       "skills": ["py", "python", "Python 3.11", "js", "Postgres", "k8s", "Docker"],
       "source": "manual"
     }'
```

#### Sample Response (`200 OK`)
```json
{
  "count": 5,
  "normalized_skills": [
    {
      "canonical_name": "Python",
      "original_name": "py",
      "original_names": ["py", "python", "Python 3.11"],
      "category": "programming_language",
      "normalization_method": "alias",
      "confidence": 1.0,
      "source": "manual"
    },
    {
      "canonical_name": "JavaScript",
      "original_name": "js",
      "original_names": ["js"],
      "category": "programming_language",
      "normalization_method": "alias",
      "confidence": 1.0,
      "source": "manual"
    },
    {
      "canonical_name": "PostgreSQL",
      "original_name": "Postgres",
      "original_names": ["Postgres"],
      "category": "database",
      "normalization_method": "alias",
      "confidence": 1.0,
      "source": "manual"
    },
    {
      "canonical_name": "Kubernetes",
      "original_name": "k8s",
      "original_names": ["k8s"],
      "category": "devops",
      "normalization_method": "alias",
      "confidence": 1.0,
      "source": "manual"
    },
    {
      "canonical_name": "Docker",
      "original_name": "Docker",
      "original_names": ["Docker"],
      "category": "devops",
      "normalization_method": "exact",
      "confidence": 1.0,
      "source": "manual"
    }
  ]
}
```

#### 2. Inspect Canonical Skill Taxonomy (`GET /api/v1/skills/taxonomy`)
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/skills/taxonomy"
```

---

## 7. Candidate ↔ Job Requirement Matching Engine (Phase 6)

Phase 6 connects the normalized candidate profile and job requirements through a **100% deterministic, transparent matching engine**:

- **Strictly Grounded Evaluation**: Evaluates whether a candidate satisfies job requirements across **skills**, **experience**, **education**, **certifications**, and **explicit constraints**.
- **Zero Scores or Hallucinations**: In strict compliance with architectural decoupling, Phase 6 computes **0 overall scores**, **0 match percentages**, **0 rankings**, and makes **0 LLM calls**. (Scoring fusion is reserved for Phase 8).
- **Match Status Categories**: `matched`, `partial`, `unmatched`, `not_evaluable`.
- **Match Method Transparency**: Direct citation of mechanism (`canonical_exact`, `alias_normalized`, `version_compatible`, `experience_verified`, `experience_insufficient`, `education_match`, `education_partial`, `certification_match`, `text_evidence`, `unmatched`, `not_evaluable`).
- **Overclaiming Protection**: Skill-specific tenure requirements require explicit verifiable role duration (marked `not_evaluable` rather than assuming total tenure).
- **Overlap Prevention**: Career experience calculates the union of disjoint intervals to prevent double-counting concurrent roles.
- **Priority Preservation**: `must_have` vs `nice_to_have` constraints are preserved with source text citations.

### Matching API Examples

#### 1. Analyze Profiles Directly (`POST /api/v1/matching/analyze`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/matching/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "candidate": { ... },
       "job": { ... }
     }'
```

#### 2. Match Directly from Files (`POST /api/v1/matching/from-files`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/matching/from-files" \
     -F "resume_file=@data/sample/resumes/synthetic_software_engineer.pdf" \
     -F "jd_file=@data/sample/job_descriptions/backend_developer_jd.txt"
```

---

## 8. Embedding-Based Semantic Matching (Phase 7)

Phase 7 introduces a dense semantic representation layer utilizing `sentence-transformers` (`all-MiniLM-L6-v2`) and cosine similarity:

- **Semantic Decision-Support**: Computes continuous semantic similarity (0.0 to 1.0) between candidate evidence items (skills, role summaries, projects) and job requirements without judging overall candidate suitability.
- **Strictly Subordinate to Determinism**: Phase 6 deterministic logic remains authoritative. Semantic similarity enriches requirement evidence rather than overturning explicit facts.
- **Threshold-Driven Classification**:
  - $\ge 0.75$: `semantic_match` (confidence `high`)
  - $0.55 \text{ to } 0.75$: `semantic_partial` (confidence `medium`)
  - $< 0.55$: `semantic_unrelated` (confidence `low`)
  - Empty/missing evidence: `semantic_not_evaluable`
- **Domain False-Positive Protection Matrix**: Hard filters strictly prevent semantic conflation of distinct technologies (`Java` vs `JavaScript`, `C` vs `C++`/`C#`, `Python` vs `PyTorch`, `React` vs `React Native`, `AWS` vs `AWS Lambda`), forcing similarity to `0.0`.
- **In-Memory SHA-256 Caching**: Cached embeddings avoid redundant forward passes, yielding sub-millisecond retrieval on repeated terms.
- **Strict Zero Scores / Zero Rankings**: Outputs requirement-level similarity records only. Scoring fusion is strictly reserved for Phase 8.

### Semantic Matching API Examples

#### 1. Evaluate Semantic Matches Directly (`POST /api/v1/matching/semantic`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/matching/semantic" \
     -H "Content-Type: application/json" \
     -d '{
       "candidate": { ... },
       "job": { ... }
     }'
```

#### 2. Deterministic Matching Enriched with Semantic Evidence (`POST /api/v1/matching/analyze`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/matching/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "candidate": { ... },
       "job": { ... },
       "include_semantic": true
     }'
```

---

## 9. Multi-Layer Hybrid Fusion Scoring Engine (Phase 8)

Phase 8 introduces an explainable, configurable **Multi-Layer Hybrid Fusion Scoring Engine** that combines deterministic requirement satisfaction, semantic similarity, and experience proportionality:

- **Four Component Scores (Normalized $[0.0, 1.0]$)**:
  1. **`rule_fit`**: Evaluates evaluable **non-experience deterministic requirements** ($\mathcal{R}_{\text{rule}}$: skills, education, certifications, and explicit constraints) from Phase 6. Experience requirements ($\mathcal{R}_{\text{exp}}$) are intentionally excluded because career tenure is represented separately and proportionally by `experience_fit`. Priority-weighted (`must_have` = 1.0, `nice_to_have` = 0.5) over $\mathcal{R}_{\text{rule}}$:
     - `matched` $\rightarrow$ 1.0
     - `partial` $\rightarrow$ 0.5
     - `unmatched` $\rightarrow$ 0.0
     - `not_evaluable` $\rightarrow$ Excluded from both numerator and denominator.
  2. **`semantic_fit`**: Priority-weighted average of continuous raw cosine similarity scores ($[0.0, 1.0]$) across semantically evaluable **non-experience requirements** from Phase 7 (`must_have` = 1.0, `nice_to_have` = 0.5). Career experience and role tenure requirements (`category == "experience"` or `exp_*`) are strictly excluded to prevent double-counting with `experience_fit`, while remaining fully preserved in diagnostic evidence.
  3. **`experience_fit`**: Proportional career tenure ratio over $\mathcal{R}_{\text{exp}}$ ($\min(\text{candidate\_years} / \text{required\_years}, 1.0)$), capped strictly at 1.0 to prevent unfairly rewarding overqualified candidates; excluded when no experience requirements exist.
  4. **`llm_fit`**: Qualitative evaluation placeholder (defaults to `None` / `available = False` for deterministic, zero-cost execution).
- **Default Fusion Weights**:
  - `rule_fit_weight`: **0.30**
  - `semantic_fit_weight`: **0.40**
  - `experience_fit_weight`: **0.20**
  - `llm_fit_weight`: **0.10**
- **Dynamic Weight Renormalization**:
  When a component is unavailable or non-evaluable (e.g., qualitative LLM fit disabled or no experience requirement), its weight dynamically resets to 0.0, and remaining active weights are automatically renormalized to sum to 1.0:
  $$w'_i = \frac{w_i}{\sum_{j \in \text{active}} w_j}, \quad \text{Final Fit Score} = \sum_{i \in \text{active}} w'_i \times s_i$$
- **Independent Safety Signal (`all_must_haves_satisfied`)**:
  Tracked as an uncompromised boolean safety gate. A candidate with high nice-to-have fit cannot mask missing mandatory qualifications.
- **Strict Guardrails**:
  - **Zero Candidate Ranking**: Evaluates single candidate-job pairs without global ordering or candidate comparison.
  - **Zero Shortlists or Top-N Cuts**: No arbitrary cutoffs or candidate filtering.
  - **Zero Hiring Decisions**: No automated "hire" or "reject" judgments; acts purely as an objective decision-support signal.
  - **100% Deterministic & Reproducible**: Identical inputs always produce identical floating-point scores.

### Scoring API Examples

#### 1. Analyze Fit Score Directly (`POST /api/v1/scoring/analyze`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/scoring/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "candidate": { ... },
       "job": { ... },
       "custom_weights": {
         "rule_fit_weight": 0.40,
         "semantic_fit_weight": 0.40,
         "experience_fit_weight": 0.20,
         "llm_fit_weight": 0.0
       }
     }'
```

#### 2. Unified Requirement Matching with Fit Score (`POST /api/v1/matching/analyze`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/matching/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "candidate": { ... },
       "job": { ... },
       "include_semantic": true,
       "include_score": true
     }'
```

#### 3. Match and Score Directly from Files (`POST /api/v1/matching/from-files`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/matching/from-files?include_semantic=true&include_score=true" \
     -F "resume_file=@data/sample/resumes/synthetic_software_engineer.pdf" \
     -F "jd_file=@data/sample/job_descriptions/backend_developer_jd.pdf"
```

---

## 10. Skill-Gap Analysis & Evidence Grounding (Phase 9)

Phase 9 introduces an evidence-grounded skill-gap analysis engine that identifies candidate deficiencies against job requirements while upholding strict objectivity and verification standards:

- **Four Discrete Skill Gap Statuses**:
  1. `satisfied`: Candidate satisfies the skill with verified duration meeting or exceeding requirements.
  2. `missing`: Candidate profile contains no matching skill evidence whatsoever.
  3. `insufficient`: Candidate demonstrates the skill, but verified duration falls short of required tenure.
  4. `not_evaluable`: Skill mentioned or demonstrated, but tenure cannot be verified from dated work history.
- **Deterministic-First Authority (Rule 6)**: Phase 6 deterministic matching is authoritative. Semantic similarity **cannot** override a deterministic `unmatched` status to `satisfied` or `partial`. Instead, semantic similarity is cited purely as supporting context in the explanation.
- **Quantitative Shortfall Calculation**: For `insufficient` skills: $\text{shortfall} = \max(0.0, \text{required\_years} - \text{candidate\_years})$.
- **Career Tenure Separation**: General experience requirements are analyzed strictly in `experience_gaps` and never converted into technical skill gaps.
- **Canonical Skill Deduplication**: Groups alias requirements (e.g. `JS` and `JavaScript`) under canonical taxonomy names, preserving `must_have` priority precedence and maximum tenure requirements.
- **Strict Decision-Support Guardrails**: Zero candidate ranking, zero shortlists, zero hiring/rejection decisions, zero courses/learning recommendations.

### Skill-Gap API Examples

#### 1. Analyze Gaps from Profiles (`POST /api/v1/gaps/analyze`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/gaps/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "candidate": { ... },
       "job": { ... }
     }'
```

#### 2. Analyze Gaps from Uploaded Files (`POST /api/v1/gaps/from-files`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/gaps/from-files" \
     -F "resume_file=@data/sample/resumes/synthetic_software_engineer.pdf" \
     -F "jd_file=@data/sample/job_descriptions/backend_developer_jd.pdf"
```

##### 3. Unified Matching with Score and Gaps (`POST /api/v1/matching/analyze`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/matching/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "candidate": { ... },
       "job": { ... },
       "include_semantic": true,
       "include_score": true,
       "include_skill_gaps": true,
       "include_explanation": true
     }'
```

---

## 11. LLM Explanations & Personalized Recommendations (Phase 10)

Phase 10 provides an evidence-grounded explanation and personalized recommendation layer that translates structured evaluation metrics into human-readable narrative audits:

- **Critical Boundary Principle**: The LLM is an explanation and recommendation layer only. It is **NOT** an authority over deterministic matching, semantic matching, scoring, or gap determination, and never alters underlying facts or numerical scores.
- **Mandatory Evidence Grounding**: Explanations cite only verified resume and JD evidence; zero fabricated experience, skills, employers, or credentials.
- **Explicit Uncertainty**: Incomplete evidence or unverified tenure is clearly acknowledged as not evaluable.
- **Deterministic-First Respect**: Related skills (e.g. MySQL for PostgreSQL) are explained as supporting context only without overriding missing status.
- **Targeted Recommendations**: Generated exclusively for skills identified as gaps in Phase 9 (`missing`, `insufficient`, `not_evaluable`), providing concrete project workflows and verifiable proof artifacts.
- **Zero Decision-Making**: Strictly non-evaluative; contains zero candidate rankings, shortlists, or automated hiring/rejection decisions.

### Explanation API Examples

#### 1. Generate Explanation from Profiles (`POST /api/v1/explanations/analyze`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/explanations/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "candidate": { ... },
       "job": { ... }
     }'
```

#### 2. Generate Explanation from Uploaded Files (`POST /api/v1/explanations/from-files`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/explanations/from-files" \
     -F "resume_file=@data/sample/resumes/synthetic_software_engineer.pdf" \
     -F "job_file=@data/sample/job_descriptions/backend_engineer_jd.pdf"
```

---

## 12. Project Directory Structure

```
p101-resume-screening/
│
├── README.md                  # Project overview, setup, and architecture
├── .env.example               # Template for environment variables
├── .env                       # Local environment configuration (git-ignored)
├── .gitignore                 # Standard Python, Next.js, and DB ignore rules
├── requirements.txt           # Python dependency declarations
├── Dockerfile                 # Container image specification for backend
├── docker-compose.yml         # Multi-service setup (FastAPI + PostgreSQL)
│
├── docs/                      # Architectural & API specifications
│   ├── architecture.md        # Comprehensive architecture & matching specifications
│   ├── api.md                 # REST API endpoints specification
│   └── evaluation.md          # Evaluation methodology & synthetic dataset plan
│
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI entry point, lifespan, CORS, and routing
│   │   ├── config.py          # Centralized Pydantic BaseSettings management
│   │   ├── schemas.py         # Pydantic validation request/response models
│   │   │
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── health.py          # Health check & DB connectivity endpoint
│   │   │       ├── resumes.py         # Parse & Extract endpoints (/parse, /extract)
│   │   │       ├── jobs.py            # Job Description analysis endpoints (/analyze, /upload)
│   │   │       ├── skills.py          # Skill normalization & taxonomy endpoints (/normalize, /taxonomy)
│   │   │       ├── matching.py        # Matching endpoints (/analyze, /from-files, /semantic)
│   │   │       ├── scoring.py         # Hybrid fit scoring endpoint (/analyze)
│   │   │       ├── gaps.py            # Skill gap analysis endpoints (/analyze, /from-files)
│   │   │       └── explanations.py    # LLM explanations & recommendations (/analyze, /from-files)
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── session.py             # SQLAlchemy engine, session maker, and init_db
│   │   │   └── models.py              # Relational models (Job, Candidate, Resume, etc.)
│   │   │
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── llm_client.py          # Provider abstraction (Gemini, OpenAI, Mock)
│   │   │   ├── validators.py          # JSON sanitization and Pydantic validation
│   │   │   └── prompts/
│   │   │       ├── resume_extraction.txt # Versioned resume extraction prompt
│   │   │       ├── job_extraction.txt    # Versioned job description extraction prompt
│   │   │       └── llm_explanation.txt   # Versioned explanation and recommendations prompt
│   │   │
│   │   └── services/                  # Core business logic services
│   │       ├── __init__.py
│   │       ├── document_parser.py     # PDF/DOCX parsing, validation & sanitization
│   │       ├── rule_extractor.py      # Resume regex & heading segmentation rules
│   │       ├── resume_extractor.py    # Hybrid rule + LLM profile extraction
│   │       ├── jd_rule_extractor.py   # Job description rule & section extraction
│   │       ├── jd_analyzer.py         # Job description analysis orchestration
│   │       ├── skill_taxonomy.py      # Centralized canonical skill registry
│   │       ├── skill_normalizer.py    # Skill normalization & deduplication service
│   │       ├── matching_engine.py     # Deterministic candidate-job requirement matching
│   │       ├── embedding_service.py   # Dense vector embeddings and in-memory cache
│   │       ├── semantic_matcher.py    # Semantic matching and false-positive protection matrix
│   │       ├── scoring_engine.py      # Multi-layer hybrid fusion scoring engine
│   │       ├── skill_gap_analyzer.py  # Evidence-grounded skill gap analyzer
│   │       ├── llm_explanation_service.py # Evidence-grounded LLM explanations & recommendations
│   │       ├── rule_filter.py
│   │       ├── semantic_scorer.py
│   │       ├── fusion.py
│   │       ├── skill_gap.py
│   │       ├── recommender.py
│   │       ├── explainer.py
│   │       └── pii_masker.py
│   │
│   └── tests/
│       ├── __init__.py
│       ├── test_health.py             # System health and schema creation tests
│       ├── test_document_parser.py    # PDF, DOCX, validation & parse endpoint tests
│       ├── test_resume_extractor.py   # Resume schema, rule, LLM validation & extraction tests
│       ├── test_jd_analyzer.py        # Job description analysis and API tests
│       ├── test_skill_normalizer.py   # Skill normalization and taxonomy tests
│       ├── test_matching_engine.py    # Deterministic matching and API tests
│       ├── test_semantic_matching.py  # Embedding, threshold, caching, and semantic match tests
│       ├── test_scoring_engine.py     # Hybrid fusion scoring, priority, capping & API tests
│       ├── test_skill_gap_analyzer.py # Evidence-grounded skill gap analysis & API tests
│       └── test_llm_explanation.py    # Grounded LLM explanations & recommendations tests
│
├── frontend/                  # Next.js / React dashboard (Phase 11)
├── data/
│   └── sample/
│       ├── resumes/           # Diverse synthetic test resumes (.pdf, .docx)
│       └── job_descriptions/  # Diverse synthetic job postings (.txt, .pdf, .docx)
└── scripts/                   # Evaluation and utility scripts
```

---

## 13. Getting Started

### Prerequisites
---

## 12. Frontend Web Dashboard (Phase 11)

The frontend provides an intuitive, accessible web dashboard built with **Next.js 16 (App Router)**, **TypeScript**, and **Tailwind CSS v4**.

### Key Pages & Capabilities
- **Dashboard (`/`)**: Displays real-time backend operational status (`/health`), recent session screening history, and architecture summaries.
- **Job Setup (`/jobs/new`)**: Configure target roles by uploading JD documents (`.pdf`, `.docx`, `.txt`) or pasting raw text; inspects extracted mandatory/preferred skills, experience tenure, and degree requirements.
- **Job Management (`/jobs`)**: Review active screening roles and criteria.
- **Analysis Workspace (`/analysis`)**: Central evaluation screen. Supports selecting an active job role or uploading a JD document alongside a candidate resume (`.pdf` or `.docx`).
- **Score Breakdown & Safety Signals**: Renders overall candidate fit percentage, component breakdown (Rule Fit, Semantic Fit, Experience Fit, LLM Fit), and safety signals (`all_must_haves_satisfied`).
- **Requirement-by-Requirement Audit**: Interactive, accessible table detailing priority, status, match method, semantic cosine similarity, and expandable verbatim evidence citations.
- **Evidence-Grounded Skill Gaps**: Distinguishes satisfied, missing, insufficient (with exact tenure shortfall), and not-evaluable skills. Keeps career experience tenure strictly separate.
- **Grounded AI Explanations & Recommendations**: Renders executive summaries, verified strengths, key gaps, and targeted project recommendations with a permanent, prominent Recruiter Review Policy disclaimer.

---

## 13. Getting Started & Local Development

### Prerequisites
- Python 3.11 or higher
- Node.js 18+ (tested on Node v24) and npm
- Git

### Step 1: Set Up Backend
```bash
# Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Run FastAPI backend
uvicorn backend.app.main:app --reload --port 8000
```
- Interactive API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/v1/health`

### Step 2: Set Up and Run Frontend
```bash
cd frontend

# Install frontend dependencies
npm install

# Configure environment variables
cp .env.example .env.local

# Run Next.js development server
npm run dev
```
- Frontend Web Dashboard: `http://localhost:3000`

### Step 3: Run Tests & Benchmarks
```bash
# Run backend test suite (168 tests)
pytest backend/tests/ -q

# Run frontend test suite (21 tests)
cd frontend && npm test

# Run Phase 12 comprehensive benchmark suite
python evaluation/run_evaluation.py
```

---

## 13. Evaluation, Benchmarking & End-to-End Validation (Phase 12)

The system includes a dedicated, reproducible benchmarking suite in `evaluation/`:
- **Synthetic Evaluation Dataset**: 10 synthetic candidate profiles across realistic engineering archetypes and 5 industry job descriptions.
- **10 Curated Evaluation Cases**: End-to-end ground-truth verification checking parsing, extraction, deterministic matching, skill-gap detection, and LLM explanation grounding.
- **Scoring Invariants (A through F)**: Verifies that experience is excluded from `rule_fit` and `semantic_fit`, experience tenure is isolated to `experience_fit`, dynamic weight renormalization preserves sum to 1.0, and scores are 100% deterministic and reproducible.
- **Protected Technology Matrix**: Guarantees that distinct technologies (`Java != JavaScript`, `C != C++`, `C != C#`, `Python != PyTorch`, `React != React Native`, `AWS != AWS Lambda`) are strictly blocked from semantic false-positive conflation.
- **Telemetry & Latencies**: Generates machine-readable `evaluation/reports/latest.json` and human-readable `evaluation/reports/latest.md` with end-to-end pipeline latencies (median ~73 ms, p95 ~131 ms).

---

## 14. Development Roadmap & Incremental Phases

- [x] **Phase 1: Project Setup + Backend + Database**
- [x] **Phase 2: Resume PDF/DOCX Parsing**
- [x] **Phase 3: Structured Resume Information Extraction**
- [x] **Phase 4: Job Description Analysis & Requirement Extraction**
- [x] **Phase 5: Skill Normalization & Taxonomy Mapping**
- [x] **Phase 6: Candidate ↔ Job Requirement Matching Engine**
- [x] **Phase 7: Embedding-Based Semantic Matching**
- [x] **Phase 8: Multi-Layer Hybrid Fusion Scoring**
- [x] **Phase 9: Skill-Gap Analysis & Evidence Grounding**
- [x] **Phase 10: LLM Explanations & Personalized Recommendations**
- [x] **Phase 11: Frontend Web Dashboard**
- [x] **Phase 12: Evaluation, Benchmarking & End-to-End Validation**
- [x] **Phase 13: Demo Readiness & End-to-End Demo Validation**
- [x] **Phase 14: Final Project Documentation & Report Preparation**



