# System Architecture — P_101 LLM-Based Resume Screening System

## 1. Overview
The **P_101 LLM-Based Resume Screening System** is designed as an AI-assisted decision-support platform that evaluates candidate resumes against Job Descriptions (JDs) with transparency, verifiable evidence, skill-gap analysis, and fairness. It does not replace human recruiters; rather, it empowers them with interpretable scoring and structured insights.

```
                      ┌──────────────────────────────────────┐
                      │        Frontend Dashboard            │
                      │     (Next.js / React + Tailwind)     │
                      └──────────────────┬───────────────────┘
                                         │ HTTP REST
                                         ▼
                      ┌──────────────────────────────────────┐
                      │          FastAPI Backend             │
                      │   (Validation, Routes, Middlewares)  │
                      └──────────────────┬───────────────────┘
                                         │
        ┌────────────────────────────────┴────────────────────────────────┐
        │                                                                 │
        ▼                                                                 ▼
┌───────────────────────────────┐                       ┌─────────────────────────────────┐
│     Ingestion & Extraction    │                       │       Hybrid Decision Engine    │
├───────────────────────────────┤                       ├─────────────────────────────────┤
│ • PyMuPDF / python-docx       │                       │ 1. Rule Engine (Hard Filters)   │
│ • Section Parsing             │                       │ 2. Semantic Matcher (Embeddings)│
│ • PII Masking Engine          │                       │ 3. Experience Matcher           │
│ • Skill Normalizer            │                       │ 4. LLM Explainer & Validator    │
└───────────────────────────────┘                       │ 5. Multi-Layer Fusion Scoring   │
                                                        └────────────────┬────────────────┘
                                                                         │
                                                                         ▼
                                                        ┌─────────────────────────────────┐
                                                        │ Post-Processing & Insights      │
                                                        ├─────────────────────────────────┤
                                                        │ • Skill Gap Identification      │
                                                        │ • Evidence Grounding            │
                                                        │ • Actionable Recommendations    │
                                                        │ • Candidate Ranking & Export    │
                                                        └─────────────────────────────────┘
```

## 2. Document Ingestion & Processing Pipeline (Phase 2)

Before any AI or matching engine runs, resumes pass through a strictly decoupled document extraction pipeline:

```text
Upload (.pdf or .docx)
   ↓
Validation
   • Extension check (.pdf, .docx only)
   • Magic byte verification (%PDF, PK\x03\x04)
   • Size boundary validation (<= configurable MAX_UPLOAD_SIZE_MB, non-zero)
   • Filename path-traversal sanitization
   ↓
Document Parser Service (backend/app/services/document_parser.py)
   ├── PDF Branch: PyMuPDF (pymupdf)
   │   • Iterates pages
   │   • Extracts text with reading order sort (sort=True)
   │   • Catches blank/scanned documents (raises 422 ScannedDocumentError)
   └── DOCX Branch: python-docx
       • Preserves natural body flow order across paragraphs and tables
       • Merged-cell deduplication in tables
       • Catches empty documents (raises 400 EmptyDocumentError)
   ↓
Clean Extracted Text & Metadata (character count, word count, page count)
   ↓
Downstream Information Extraction & Screening Pipelines
```

## 3. Structured Resume Extraction Pipeline (Phase 3 & 3.1)

The raw text extracted from documents is converted into a validated `CandidateProfile` through a 5-stage layered extraction and quality-hardening pipeline:

```text
Document Parser
      ↓
Raw Resume Text
      ↓
Deterministic / Rule Extraction (backend/app/services/rule_extractor.py)
      ├── Regex Email & Phone extraction
      ├── LinkedIn & GitHub profile links
      ├── Headings & Section segmentation (Summary, Skills, Experience, Education, etc.)
      ├── Multi-job boundary detection (parse_experience_blocks)
      ├── Multi-format education extraction (parse_education_blocks)
      └── Project name vs. description isolation (parse_project_blocks)
      ↓
LLM Extraction Layer (backend/app/ai/llm_client.py + prompts/resume_extraction.txt)
      ├── Strict negative constraints preventing entity merging
      ├── Categorizes skills via canonical SKILL_TAXONOMY
      └── Extracts complex entities (nested experience, education, projects, achievements)
      ↓
JSON Sanitization & Pydantic Validation (backend/app/ai/validators.py & schemas.py)
      ├── Strips markdown codeblocks & locates outermost JSON boundaries
      ├── Enforces strict validation against CandidateProfile schema
      ├── Validates skill categories against VALID_SKILL_CATEGORIES
      └── Sanitizes company fields against bullet-point leakage
      ↓
Quality-Hardening & Ground-Truth Reconciliation (backend/app/services/resume_extractor.py)
      ├── Merges deterministic contact info (email/phone/links)
      ├── Unpacks merged jobs if LLM collapses multiple roles into a single experience item
      ├── Cleans institution names by removing leaked degree names, fields, and year ranges
      ├── Splits merged project names and descriptions
      └── Normalizes skill categories according to canonical taxonomy
      ↓
Validated Candidate Profile (CandidateProfile)
```

### 3.1 Quality Hardening Specifics (Phase 3.1)

1. **Multi-Job Experience Separation**:
   - Resumes with multiple positions (e.g. Senior Software Engineer at CloudCorp and Software Developer at AppLabs) are segmented by detecting date boundary patterns (`19\d\d|20\d\d\s*[-–]\s*(?:19\d\d|20\d\d|present)`) and role headers.
   - Company fields are strictly sanitized: bullet points (`-`, `*`, `•`), long duty descriptions (>80 chars), and swapped titles are rejected or cleaned.
   - Date ranges are validated to guarantee `start_date <= end_date`. If reversed, dates are automatically swapped.

2. **Education Format Resilience**:
   - Accommodates Format A (multi-line), Format B (dash-delimited `Degree in Field - Institution (Years)`), and Format C (comma-delimited `Degree, Field, Institution, Years`).
   - Degree tokens preserve abbreviation periods (e.g., `M.S.`, `B.S.`, `Ph.D.`, `B.Tech`).
   - Fields of study are partitioned cleanly from institutions without text leakage.
   - Lingering dates and parentheses are stripped from the `institution` string.

3. **Project Name vs. Description Separation**:
   - Project titles are decoupled from their functional descriptions when resumes present them as `Project Name: Description` or `Project Name - Description`.
   - Technologies are parsed from explicit tech stack lines or extracted canonical keywords from project descriptions.

4. **Skill Taxonomy & Hardening**:
   - Skill items are normalized against `SKILL_TAXONOMY`, enforcing exact categorization among 10 allowed categories: `programming_language`, `framework`, `library`, `database`, `tool`, `cloud`, `devops`, `ai_ml`, `soft_skill`, and `other`.
   - Technical concepts and architectures such as `REST APIs` and `Microservices` are strictly mapped to `other` rather than misclassified as frameworks or tools.

## 4. Hybrid AI Engine Layers

The decision pipeline intentionally rejects purely black-box LLM screening or purely naive keyword matching. It employs a 4-layer architecture:

### Layer 1: Rule Engine (Objective Criteria)
- Evaluates non-negotiable hard requirements: mandatory skills, minimum degree level, minimum years of experience, work authorizations.
- Produces `rule_score` (0–100) and qualification flags.

### Layer 2: NLP & Semantic Embedding Layer
- Skill taxonomy normalization (e.g., "JS" -> "JavaScript", "K8s" -> "Kubernetes").
- Dense semantic vector embeddings (Sentence Transformers / `all-MiniLM-L6-v2`) + cosine similarity for contextual match beyond raw strings.
- Produces `semantic_score` (0–100).

### Layer 3: Experience & Project Alignment Layer
- Evaluates duration, seniority depth, and relevant project experience against JD scope.
- Produces `experience_score` (0–100).

### Layer 4: LLM Explanation & Verification Layer
- Provider abstraction (`backend/app/ai/llm_client.py`) supporting Gemini, OpenAI, or local/mock runners.
- Structured JSON outputs verified against strict Pydantic schemas.
- Extracts citation evidence directly from resume text.
- Generates context-specific learning roadmaps for detected skill gaps.
- Produces `llm_score` (0–100).

### Layer 5: Fusion Scoring
- Total Candidate Score = $W_{rule} \cdot S_{rule} + W_{semantic} \cdot S_{semantic} + W_{exp} \cdot S_{exp} + W_{llm} \cdot S_{llm}$
- Default configurable weights: 30% Rule Fit, 40% Semantic Skill Fit, 20% Experience Fit, 10% LLM Fit.
- Every score is stored and presented with its sub-score breakdown.

## 3. Database Schema Overview
The database uses SQLAlchemy and supports both SQLite (rapid local testing) and PostgreSQL (production).
Core entities:
- `Job`: JD text, title, parsed requirements, scoring weights.
- `Candidate`: Reference to job, display ID, masking status.
- `Resume`: Raw text, original filename, parsed content metadata.
- `Profile`: Normalized skills, experience, education, projects.
- `Requirement`: Extracted mandatory and preferred skills/qualifications.
- `Score`: Detailed score breakdown (`rule_score`, `semantic_score`, `experience_score`, `llm_score`, `total_score`).
- `SkillGap`: Matched, partial, and missing skills with evidence and importance.
- `Recommendation`: Targeted skill improvement and project ideas.

## 4. Privacy & Masked Mode
- Recruiter can toggle `masked_mode`.
- When enabled, names, gender indicators, photographs, institutions, and contact details are redacted before scoring to mitigate cognitive bias.
