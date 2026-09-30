# P_101 — LLM-Based Resume Screening System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00.svg?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> An academic-grade, production-quality AI-assisted resume screening and candidate decision-support system featuring multi-layer hybrid scoring, grounded evidence citations, skill-gap analysis, and bias-reduction masked screening.

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

## 5. Project Directory Structure

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
│   ├── architecture.md        # Comprehensive architecture & fusion mathematics
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
│   │   │       └── resumes.py         # Parse & Extract endpoints (/parse, /extract)
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
│   │   │       └── resume_extraction.txt # Versioned extraction prompt
│   │   │
│   │   └── services/                  # Core business logic services
│   │       ├── __init__.py
│   │       ├── document_parser.py     # PDF/DOCX parsing, validation & sanitization
│   │       ├── rule_extractor.py      # Regex & heading segmentation rules
│   │       ├── resume_extractor.py    # Hybrid rule + LLM profile extraction
│   │       ├── jd_analyzer.py
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
│       └── test_resume_extractor.py   # Schema, rule, LLM validation & extraction tests
│
├── frontend/                  # Next.js / React dashboard (Phase 11)
├── data/
│   └── sample/
│       └── resumes/           # Diverse synthetic test resumes (.pdf, .docx)
└── scripts/                   # Evaluation and utility scripts
```

---

## 6. Getting Started

### Prerequisites
- Python 3.11 or higher
- Git

### Step 1: Clone and Enter the Directory
```bash
cd p101-resume-screening
```

### Step 2: Set Up Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Key configuration values in `.env`:
```ini
APP_ENV=development
DEBUG=True
PORT=8000
DATABASE_URL=sqlite:///./resume_screening.db
LLM_PROVIDER=mock   # Options: mock (offline testing), gemini, openai
LLM_API_KEY=        # Required only when using cloud LLM providers
```

### Step 5: Run the Backend Application
```bash
uvicorn backend.app.main:app --reload --port 8000
```
- Interactive API Documentation (Swagger UI): `http://127.0.0.1:8000/docs`
- Alternative API Documentation (ReDoc): `http://127.0.0.1:8000/redoc`
- Health Check: `http://127.0.0.1:8000/api/v1/health`

### Step 6: Run Tests
```bash
pytest backend/tests/ -v
```

---

## 7. Development Roadmap & Incremental Phases

- [x] **Phase 1: Project Setup + Backend + Database**
- [x] **Phase 2: Resume PDF/DOCX Parsing**
- [x] **Phase 3: Structured Resume Information Extraction**
- [ ] **Phase 4: Job Description Analysis & Requirement Extraction**
- [ ] **Phase 5: Skill Normalization & Taxonomy Mapping**
- [ ] **Phase 6: Deterministic Rule Engine**
- [ ] **Phase 7: Embedding-Based Semantic Matching**
- [ ] **Phase 8: Multi-Layer Hybrid Fusion Scoring**
- [ ] **Phase 9: Skill-Gap Analysis & Evidence Grounding**
- [ ] **Phase 10: LLM Explanations & Personalized Recommendations**
- [ ] **Phase 11: Frontend Web Dashboard**
- [ ] **Phase 12: End-to-End System Integration**
- [ ] **Phase 13: Synthetic Evaluation & Benchmark Testing**
- [ ] **Phase 14: Documentation & Docker Deployment**
