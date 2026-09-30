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

## 3. Project Directory Structure

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
│   │   │       └── health.py  # Health check & DB connectivity endpoint
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── session.py     # SQLAlchemy engine, session maker, and init_db
│   │   │   └── models.py      # Relational models (Job, Candidate, Resume, etc.)
│   │   │
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── llm_client.py  # Provider abstraction (Gemini, OpenAI, Mock)
│   │   │   ├── hybrid_engine.py
│   │   │   ├── validators.py
│   │   │   └── prompts/       # Centralized, versioned prompt templates
│   │   │
│   │   └── services/          # Core business logic services
│   │       ├── __init__.py
│   │       ├── resume_parser.py
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
│       └── test_health.py     # System health and schema creation tests
│
├── frontend/                  # Next.js / React dashboard (Phase 11)
├── data/
│   └── sample/                # Synthetic test resumes and annotations
└── scripts/                   # Evaluation and utility scripts
```

---

## 4. Getting Started

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

## 5. Development Roadmap & Incremental Phases

- [x] **Phase 1: Project Setup + Backend + Database**
- [ ] **Phase 2: Resume PDF/DOCX Parsing**
- [ ] **Phase 3: Structured Resume Information Extraction**
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
