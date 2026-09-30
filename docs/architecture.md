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

## 2. Hybrid AI Engine Layers

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
