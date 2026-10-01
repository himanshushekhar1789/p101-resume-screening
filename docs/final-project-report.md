# P_101 — LLM-Based Resume Screening System
### An Evidence-Grounded Recruiter Decision-Support Platform with Hybrid Scoring and Transparent Skill-Gap Auditing

---

## 1. Document Control & Metadata

* **Project Identifier**: P_101
* **System Title**: LLM-Based Resume Screening System
* **Academic/Engineering Classification**: AI-Assisted Decision-Support System / NLP Pipeline
* **Software Version**: 1.0.0
* **Date**: October 2026
* **Repository Baseline**: Phases 1–13 Complete (Commits `b59c76c` / `c93d4c5`)
* **Target Audience**: College Project Evaluators, Faculty Reviewers, Technical Examiners, Software Engineers

---

## 2. Abstract

Manual resume screening in technical recruitment is notoriously labor-intensive, inconsistent, and prone to subjective cognitive fatigue. Conventional automated systems typically rely on rigid keyword matching, which penalizes qualified candidates who use valid synonyms or modern terminology. Conversely, modern attempts to delegate screening entirely to generative Large Language Models (LLMs) suffer from severe architectural drawbacks, including unexplainable scoring, hallucinated qualifications, sensitivity to prompt injection, and lack of deterministic auditability.

This project, **P_101**, presents an evidence-grounded, multi-layered resume screening decision-support platform designed to assist human recruiters without automating hiring or rejection decisions. The system integrates a decoupled, deterministic requirement matching engine with a dense semantic similarity engine (`sentence-transformers/all-MiniLM-L6-v2`) and a constrained generative LLM explanation layer. Resumes and job descriptions are parsed into strongly validated, structured schemas using PyMuPDF, python-docx, and Pydantic. Technical skills are normalized against an extensible canonical taxonomy featuring alias resolution and false-positive protection between lookalike technologies. Candidate qualifications are evaluated through a multi-factor hybrid scoring model comprising Rule Fit (30%), Semantic Fit (40%), Experience Fit (20%), and LLM-Supported Fit (10%). Skill gaps are categorized into satisfied, missing, insufficient, and un-evaluable dimensions with verbatim evidence citations.

The system was evaluated against a synthetic benchmark suite of 10 candidate resumes and 5 job specifications across 10 curated evaluation cases. The implementation demonstrated 100% alias resolution accuracy, 100% false-positive isolation across protected technology pairs, 6/6 verified scoring invariants, 100% factual grounding of LLM explanations, and zero automated hiring/rejection verdicts across 189 total regression tests (168 backend, 21 frontend). P_101 provides recruiters with an interpretable, transparent, and auditable candidate qualification workspace.

---

## 3. Introduction

Resume screening represents the initial and often most critical filtering stage in the hiring lifecycle. In high-volume technical hiring, corporate job postings frequently attract hundreds or thousands of applicants. Human talent acquisition specialists face significant challenges in thoroughly evaluating every application against intricate technical specifications. Consequently, organizations have long sought automated tools to streamline candidate triage.

However, existing automated solutions exhibit fundamental flaws:
1. **Keyword-Based Applicant Tracking Systems (ATS)**: These tools perform superficial string matching. If a job description mandates "PostgreSQL" and a candidate lists "Postgres" or "RDBMS (Postgres 14)", basic keyword screeners may flag the requirement as unsatisfied. Conversely, candidates who mechanically "keyword-stuff" their resumes pass filters regardless of actual technical depth.
2. **Monolithic Generative LLM Screeners**: Recent efforts to prompt generative LLMs with prompts such as "Rate this resume from 1 to 10" introduce opacity, non-determinism, and hallucinations. A candidate might be awarded a high score based on persuasive prose or stylistic flair, despite lacking core mandatory requirements. Furthermore, generative models can be manipulated via prompt injection hidden within white text or resume metadata.

P_101 addresses these challenges by introducing an **architecturally constrained hybrid pipeline**. Rather than treating the LLM as an opaque judge, P_101 enforces strict separation of concerns:
* **The Deterministic Rule Engine** is the sole mathematical authority over hard requirements (must-have skills, minimum tenure, education credentials).
* **The Semantic Matching Engine** captures conceptual proximity and adjacent technical domains without overriding hard rules.
* **The LLM Layer** acts strictly as an evidence-grounded summarizer and recommendation assistant, constrained to explain facts established upstream by deterministic analysis.
* **The Human Recruiter** remains the sole decision-maker.

---

## 4. Problem Statement

Modern technical recruiters encounter four pervasive bottlenecks during first-pass resume screening:

1. **Volume and Latency**: Large applicant pools overwhelm recruiting teams, resulting in screening backlogs, prolonged hiring cycles, and superficial evaluations.
2. **Vocabulary and Phrasing Discrepancies**: Technical candidates express identical proficiencies using diverse phrasing, acronyms, version tags, and informal abbreviations (e.g., `JS` vs. `JavaScript`, `K8s` vs. `Kubernetes`, `FastAPI` vs. `Python REST APIs`). Simple string matching fails to bridge this semantic gap.
3. **Auditability and Evidence Traceability**: Commercial screening tools often assign opaque percentages or qualitative rankings without verifiable evidence. Recruiters cannot easily discern *why* a candidate scored 72% or which specific sentences in the resume justify the rating.
4. **Hallucination and Compliance Vulnerabilities in Direct AI Scoring**: Direct generative AI scoring risks severe regulatory and ethical pitfalls, including manufactured candidate credentials, uncalibrated scoring variances between identical runs, and potential compliance violations under emerging automated employment decision regulations (e.g., EU AI Act, NYC Local Law 144).

**Project Objective Statement**:  
To design, implement, and validate an auditable, transparent, and reproducible decision-support system that converts raw resumes and job descriptions into structured profiles, evaluates candidate qualifications through orthogonal deterministic, semantic, and tenure-based scoring models, isolates skill gaps with verbatim textual evidence, and provides recruiters with grounded natural language explanations while preserving human decision authority.

---

## 5. System Objectives

The implementation was guided by ten concrete engineering objectives:

1. **Structured Resume Parsing**: Ingest unstructured PDF and DOCX resume documents, validate structural integrity, preserve natural reading order, and extract structured candidate profiles (contact details, technical skills, chronological experience, education, and certifications).
2. **Structured Job Description Analysis**: Parse plain-text and document-based job descriptions to extract classified requirements, categorizing them into mandatory (must-have) and preferred (nice-to-have) tiers.
3. **Skill Normalization & False-Positive Isolation**: Develop a canonical skill taxonomy with bidirectional alias resolution while enforcing strict boundaries between distinct but orthographically similar technologies (e.g., `Java` vs. `JavaScript`, `C` vs. `C++`, `Python` vs. `PyTorch`).
4. **Deterministic Requirement Matching**: Implement an authoritative, rule-based matching engine that evaluates candidate evidence against requirements and classifies results into `matched`, `partial`, `unmatched`, and `not_evaluable` states.
5. **Contextual Semantic Matching**: Integrate a local dense embedding model (`sentence-transformers/all-MiniLM-L6-v2`) to assess conceptual similarity between candidate evidence and job criteria without allowing semantic scores to override missing mandatory requirements.
6. **Multi-Factor Hybrid Scoring**: Formulate an orthogonal, weighted fusion scoring model combining Rule Fit (30%), Semantic Fit (40%), Experience Fit (20%), and LLM-Supported Fit (10%) with dynamic renormalization for missing components and strict separation of experience tenure.
7. **Evidence-Grounded Skill-Gap Analysis**: Identify precise technical skill deficits, categorize them into `missing`, `insufficient`, and `not_evaluable` buckets, and substantiate every gap with verbatim candidate evidence or verified absence.
8. **Constrained LLM Explanations & Recommendations**: Build an explanation adapter that generates plain-language executive summaries and targeted development recommendations grounded exclusively in upstream deterministic facts, with strict guardrails preventing automated hiring verdicts or ungrounded claims.
9. **Interactive Recruiter Web Interface**: Construct a clean, accessible Next.js/React frontend providing intuitive score visualization, requirement coverage audits, expandable evidence citations, and human-in-the-loop disclaimers.
10. **Ethical Guardrails & Decision-Support Preservation**: Ensure the system functions strictly as an assistive tool by prohibiting automated candidate ranking, elimination leaderboards, and auto-rejection mechanisms.

---

## 6. Conventional Approaches & Their Limitations

Before developing P_101, conventional screening paradigms were examined:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CONVENTIONAL SCREENING PARADIGMS                      │
├──────────────────────────┬───────────────────────────┬──────────────────────┤
│ Paradigm                 │ Mechanism                 │ Core Limitation      │
├──────────────────────────┼───────────────────────────┼──────────────────────┤
│ 1. Manual Human Review   │ Recruiter reads full text │ Severe fatigue,      │
│                          │ of every incoming resume  │ subjective bias,     │
│                          │                           │ low throughput       │
├──────────────────────────┼───────────────────────────┼──────────────────────┤
│ 2. Keyword-Based ATS     │ Substring / Regex search  │ Brittle to synonyms, │
│                          │ against target skill list │ vulnerable to keyword│
│                          │                           │ stuffing, no context │
├──────────────────────────┼───────────────────────────┼──────────────────────┤
│ 3. Pure LLM Prompting    │ Direct prompt to LLM:     │ Non-deterministic,   │
│                          │ "Evaluate resume against  │ hallucinated facts,  │
│                          │ JD and score 1-100"       │ black-box reasoning, │
│                          │                           │ prompt injection     │
└──────────────────────────┴───────────────────────────┴──────────────────────┘
```

### Analysis of Limitations

1. **Keyword Matching Failure Modes**: Keyword engines operate without ontological awareness. For example, a candidate possessing 5 years of `PostgreSQL` experience will be penalized if the ATS only searches for `Postgres` or `SQL Database`. Furthermore, keyword matchers cannot differentiate between a candidate who *designed* a system using Docker and a candidate who simply wrote "worked in an environment where Docker was present."
2. **Pure LLM Failure Modes**: End-to-end LLM screening delegates the entire evaluation to a statistical language model. LLMs frequently hallucinate degrees or skill proficiencies that are absent from the resume. More critically, LLM scores are non-reproducible across temperature runs, sensitive to resume font or formatting artifacts, and incapable of providing mathematical audit trails necessary for legal compliance.
3. **The P_101 Differentiator**: P_101 isolates the LLM from the mathematical scoring formula entirely. The score is computed using deterministic set theory and deterministic tenure ratios; the LLM merely translates those computed findings into natural language prose.

---

## 7. Proposed System Architecture & Workflow

P_101 implements a decoupled, pipe-and-filter architecture where data flows sequentially through discrete, independently verifiable stages:

```text
               JOB DESCRIPTION                        CANDIDATE RESUME
              (PDF / DOCX / TXT)                     (PDF / DOCX Document)
                      │                                        │
                      ▼                                        ▼
             ┌─────────────────┐                      ┌─────────────────┐
             │   JD Analysis   │                      │ Document Parser │
             │   & Extraction  │                      │ (PyMuPDF / DOCX)│
             └────────┬────────┘                      └────────┬────────┘
                      │                                        │
                      ▼                                        ▼
             ┌─────────────────┐                      ┌─────────────────┐
             │ Requirement     │                      │ Candidate       │
             │ Classification  │                      │ Profile Parser  │
             │ (Must vs. Nice) │                      └────────┬────────┘
             └────────┬────────┘                               │
                      │                                        ▼
                      │                               ┌─────────────────┐
                      │                               │ Skill Taxonomy  │
                      │                               │ & Normalization │
                      │                               └────────┬────────┘
                      │                                        │
                      ├───────────────────┬────────────────────┤
                      │                   │                    │
                      ▼                   ▼                    ▼
             ┌─────────────────┐ ┌─────────────────┐ ┌──────────────────┐
             │  Deterministic  │ │    Semantic     │ │    Experience    │
             │ Matching Engine │ │ Matching Engine │ │ Tenure Evaluator │
             └────────┬────────┘ └────────┬────────┘ └────────┬─────────┘
                      │                   │                   │
                      └───────────────────┼───────────────────┘
                                          ▼
                               ┌─────────────────────┐
                               │ Multi-Layer Hybrid  │
                               │   Fusion Scoring    │
                               └──────────┬──────────┘
                                          │
                                          ▼
                               ┌─────────────────────┐
                               │ Skill-Gap Analysis  │
                               │ & Evidence Citation │
                               └──────────┬──────────┘
                                          │
                                          ▼
                               ┌─────────────────────┐
                               │ Grounded LLM        │
                               │ Explanation Layer   │
                               └──────────┬──────────┘
                                          │
                                          ▼
                               ┌─────────────────────┐
                               │ Recruiter Decision- │
                               │ Support Web UI      │
                               └─────────────────────┘
```

### Architectural Guardrails & Operating Invariants
* **Zero Automated Hiring/Rejection**: The system does not output "Hire" or "Reject" determinations. It outputs objective fit metrics, requirement satisfaction tables, and evidence snippets.
* **Zero Candidate Ranking**: Candidates are evaluated individually against the job specification. No cross-candidate sorting, stack-ranking, or leaderboard algorithms are implemented.
* **Deterministic Matching Authority**: Hard must-have criteria cannot be marked as satisfied through semantic proximity alone.
* **Score Immutability**: The LLM generation layer has zero authority over computed scores. All scores are immutable outputs of the mathematical scoring service.

---

## 8. System Layer Architecture

The system is structured across five distinct architectural layers:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. PRESENTATION LAYER (Next.js 16 / React 19 / Tailwind CSS v4)             │
│    Routes: / (Overview), /jobs, /jobs/new, /analysis, /candidates           │
│    Components: ScoreBreakdownCard, RequirementCoverageTable, SkillGapCard   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. API LAYER (FastAPI / Pydantic v2 / REST)                                 │
│    Routers: /jobs, /resumes, /skills, /matching, /scoring, /gaps            │
│    Middlewares: CORS, Request Validation, HTTP Error Handling               │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. PROCESSING LAYER (Core Application Business Logic)                       │
│    Services: DocumentParser, RuleExtractor, ResumeExtractor, JDAnalyzer    │
│    Engines: MatchingEngine, HybridScorer, SkillGapAnalyzer                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. AI & NLP LAYER (Local Embeddings & Constrained Generative LLM)           │
│    Embeddings: SentenceTransformer (all-MiniLM-L6-v2) on CPU                │
│    LLM Client: LLMClient abstraction (MockLLMClient / Gemini / OpenAI)      │
│    Prompts: System-prompt guardrails, strict anti-hallucination templates   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 5. DATA & PERSISTENCE LAYER (SQLAlchemy ORM / SQLite)                       │
│    Entities: Job, Candidate, Resume, Profile, Requirement, Score, SkillGap  │
│    Validation Schemas: Pydantic schemas for all payloads and domain models  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Technology Stack

Every component in P_101 is implemented using proven, production-grade open-source libraries:

| Architectural Tier | Technology / Library | Version | Purpose in P_101 |
| :--- | :--- | :--- | :--- |
| **Backend Framework** | Python / FastAPI | 3.11+ / 0.115+ | High-performance asynchronous REST API framework |
| **Data Validation** | Pydantic | 2.10+ | Strict type validation, serialization, and JSON schema generation |
| **Frontend Framework** | Next.js / React | 16.3.8 / 19.0+ | Server-side rendered and client-hydrated recruiter interface |
| **Frontend Language** | TypeScript | 5.0+ | Type-safe UI components, interfaces, and API clients |
| **UI Styling** | Tailwind CSS / Lucide-React | 4.0+ / 1.16+ | Clean, accessible recruiter dashboard styling and icon set |
| **Document Parsing (PDF)** | PyMuPDF (`fitz`) | 1.25+ | High-speed PDF text block extraction with natural reading-order sorting |
| **Document Parsing (DOCX)**| python-docx | 1.1+ | Structural parsing of Word documents, body paragraphs, and tables |
| **NLP & Dense Embeddings** | `sentence-transformers` | 3.4+ | Local execution of dense vector representations |
| **Embedding Model** | `all-MiniLM-L6-v2` | PyTorch / CPU | 384-dimensional dense semantic embedding (runs 100% locally) |
| **Similarity Metric** | Cosine Similarity (`scikit-learn`) | 1.6+ | Vector dot-product similarity computation |
| **Database ORM** | SQLAlchemy | 2.0+ | Object-relational mapping and schema management |
| **Persistence Database** | SQLite | 3.40+ | Local, self-contained relational database (`resume_screening.db`) |
| **Backend Testing** | pytest / pytest-asyncio | 8.3+ | Unit, integration, invariant, and API smoke testing |
| **Frontend Testing** | Vitest / Testing Library | 5.0+ | Component testing, hook testing, and accessibility assertions |
| **Version Control** | Git | 2.40+ | Version control, conventional commit history, and release tags |

---

## 10. Resume Document Processing Pipeline

Resume ingestion in Phase 2 strictly decouples physical file extraction from downstream analytical reasoning:

### 1. Ingestion Validation
* **Extension & Format Checking**: Validates that incoming files end in `.pdf` or `.docx`.
* **Magic Byte Inspection**: Verifies binary headers (`%PDF` for PDF, `PK\x03\x04` for DOCX) to prevent malicious file extension spoofing.
* **Payload Size Limits**: Enforces a strict upload limit (default 10 MB) to prevent denial-of-service via memory exhaustion.

### 2. PDF Extraction Engine (`PyMuPDF`)
* Extracted via `pymupdf.open(stream=file_bytes, filetype="pdf")`.
* Uses `page.get_text("blocks", sort=True)` to sort text blocks by vertical and horizontal position, preserving logical multi-column reading flow.
* **Scanned Document Detection**: Evaluates character-to-page ratios. If an uploaded PDF has pages but yields zero extractable text (indicating a flattened scan or image without an OCR layer), the parser immediately raises a `422 Unprocessable Content` error (`ScannedDocumentError`).

### 3. DOCX Extraction Engine (`python-docx`)
* Extracted via `docx.Document(io.BytesIO(file_bytes))`.
* Iterates sequentially through document elements, interleaving body paragraphs and table contents in their natural visual order.
* **Merged-Cell Deduplication**: Tracks previously visited XML cell addresses to prevent duplicated text strings caused by horizontally or vertically merged table cells.

---

## 11. Structured Candidate Profile Extraction

Raw text from parsed documents is transformed into a strongly typed `CandidateProfile` schema through a layered extraction pipeline:

```text
Raw Resume Text
      │
      ├──→ 1. Deterministic Extraction (rule_extractor.py)
      │       • Regex extraction of email, phone, and URLs (LinkedIn, GitHub)
      │       • Structural section heading segmentation (Summary, Skills, Experience, Education)
      │       • Date range isolation (YYYY-MM to YYYY-MM or Present)
      │
      ├──→ 2. LLM Extraction Layer (llm_client.py)
      │       • Synthesizes unstructured employment history into structured items
      │       • Extracts company, role, dates, achievements, and technology tags
      │       • Normalizes education (degree level, institution, graduation year)
      │
      └──→ 3. Schema Hardening & Reconciliation (resume_extractor.py)
              • Validates output against CandidateProfile Pydantic schema
              • Resolves multi-role employment boundaries
              • Reconciles deterministic contact details with LLM outputs
```

### Extracted Candidate Entities
* **Contact Information**: Full name, primary email, sanitized phone number, location, and professional URLs.
* **Technical Skills**: Grouped by canonical category (`languages`, `frameworks`, `databases`, `cloud`, `tools`).
* **Work Experience**: Chronological list of positions containing title, organization, start/end dates, computed tenure in months, and responsibilities.
* **Education Credentials**: Institution name, degree type (`bachelors`, `masters`, `doctorate`, `diploma`), field of study, and graduation year.
* **Certifications & Projects**: Verifiable professional credentials and open-source or academic project descriptions.

---

## 12. Job Description Analysis & Requirement Extraction

The job description analysis service (`jd_analyzer.py`) transforms unstructured job postings into a validated `JobProfile`:

1. **Requirement Classification**:
   * **Must-Have (Mandatory)**: Hard criteria without which a candidate cannot perform the role (e.g., "Must possess at least 5 years of Python backend experience").
   * **Nice-to-Have (Preferred)**: Supplementary qualifications that enhance suitability but do not disqualify if missing (e.g., "Experience with Kubernetes or AWS is a plus").
2. **Category Segmentation**:
   * **Technical Skills**: Required programming languages, libraries, platforms, and storage engines.
   * **Tenure Thresholds**: Quantitative minimum experience requirements (e.g., 5.0 years in backend development).
   * **Education Credentials**: Minimum academic degree level (e.g., Bachelor of Science in Computer Science or related).
   * **Responsibilities**: Qualitative operational duties used for semantic alignment evaluation.

---

## 13. Skill Normalization & Taxonomy Architecture

Technical skills suffer from widespread orthographic and terminological variance. P_101 implements a bidirectional canonical taxonomy with explicit false-positive protection:

### Canonical Taxonomy & Alias Resolution
The skill normalizer maps diverse surface forms to single canonical representations:

```text
Input Term                Canonical Output
──────────────────────────────────────────
"JS", "javascript", "ecmascript"    → JavaScript
"postgres", "postgresql", "psql"    → PostgreSQL
"k8s", "kube", "kubernetes"         → Kubernetes
"react.js", "reactjs"               → React
"py", "python3"                     → Python
"docker container", "dockerized"    → Docker
```

### Protected Technology Isolation Matrix
A critical hazard in resume screening is the conflation of lookalike technologies. P_101 enforces an explicit **Protected Pair Matrix** that strictly prohibits alias mapping or semantic substitution between dangerous pairs:

```text
Protected Pair           Distinction Enforced
─────────────────────────────────────────────────────────────────────────────
Java ≠ JavaScript        Enterprise JVM language vs. Web ECMAScript runtime
C ≠ C++                  Procedural systems language vs. Object-oriented language
C ≠ C#                   Low-level systems language vs. .NET managed language
Python ≠ PyTorch         General-purpose programming language vs. Deep learning framework
React ≠ React Native     Web UI DOM framework vs. Mobile cross-platform framework
AWS ≠ AWS Lambda         Cloud infrastructure platform vs. Serverless compute service
```

*Verification*: In Phase 12 benchmarks, 100% of protected technology pairs were isolated with zero false-positive conflations.

---

## 14. Deterministic Requirement Matching Engine

The deterministic matching engine (`backend/app/services/matching_engine.py`) serves as the authoritative mathematical filter.

### Evaluation Classifications
Every requirement in the `JobProfile` is evaluated against candidate evidence and classified into one of four states:
1. `matched`: Requirement is conclusively satisfied by canonical skill alias match, verified degree equivalence, or sufficient tenure.
2. `partial`: Requirement is partially satisfied (e.g., related education degree or adjacent sub-skill).
3. `unmatched`: No evidence supporting the requirement was found in the candidate profile.
4. `not_evaluable`: Subjective or non-quantifiable requirements (e.g., "Excellent interpersonal communication", "Fast learner") that cannot be honestly verified from a static resume.

### Evaluation Workflow
* **Skills**: Verified by matching candidate normalized skills against requirement canonical names and alias graphs.
* **Education**: Evaluated by mapping candidate degree titles to a standardized academic hierarchy (`Doctorate > Master's > Bachelor's > Associate/Diploma`).
* **Tenure Separation**: Crucially, general experience requirements are **excluded** from the technical skill rule match to prevent double-counting.

---

## 15. Dense Semantic Matching Engine

The semantic matching engine (`backend/app/services/semantic_matcher.py`) evaluates conceptual and contextual relevance between candidate evidence and job requirements:

* **Model**: `sentence-transformers/all-MiniLM-L6-v2` executed locally via PyTorch on CPU.
* **Vector Representation**: Computes 384-dimensional dense sentence embeddings for job requirement descriptions and candidate experience bullets.
* **Similarity Metric**: Cosine similarity bounded in the range $[0.0, 1.0]$:
  $$\text{Cosine Similarity}(\vec{u}, \vec{v}) = \frac{\vec{u} \cdot \vec{v}}{\|\vec{u}\|_2 \|\vec{v}\|_2}$$
* **Threshold Gating**:
  - Direct Match threshold: $\ge 0.70$
  - Contextual Relevance threshold: $\ge 0.45$
  - Irrelevant: $< 0.45$
* **Non-Overriding Design**: High semantic similarity indicates topical adjacency (e.g., `Flask` and `FastAPI` sharing web API concepts), but **never overrides** a deterministic `unmatched` status for a mandatory must-have skill.

---

## 16. Multi-Factor Hybrid Scoring Model

P_101 fuses deterministic, semantic, and quantitative tenure metrics into a unified, transparent fit score:

### Configured Component Weights
```text
┌─────────────────────────────────────────────────────────────┐
│                    HYBRID SCORING MODEL                     │
├──────────────────────┬─────────┬────────────────────────────┤
│ Component            │ Weight  │ Measurement Focus          │
├──────────────────────┼─────────┼────────────────────────────┤
│ Rule Fit             │   30%   │ Deterministic technical    │
│                      │         │ skill & credential match   │
├──────────────────────┼─────────┼────────────────────────────┤
│ Semantic Fit         │   40%   │ Contextual alignment of    │
│                      │         │ candidate project evidence │
├──────────────────────┼─────────┼────────────────────────────┤
│ Experience Fit       │   20%   │ Quantitative tenure ratio  │
├──────────────────────┼─────────┼────────────────────────────┤
│ LLM-Supported Fit    │   10%   │ Grounded qualification     │
│                      │         │ depth assessment           │
└──────────────────────┴─────────┴────────────────────────────┘
```
*(Note: These weights represent project engineering configurations established during prototyping, not scientifically optimal industry constants).*

### Mathematical Formulations

1. **Rule Fit ($S_{\text{rule}}$)**:
   $$S_{\text{rule}} = \frac{\sum_{i \in R_{\text{eval}}} w_i \cdot \text{score}(i)}{\sum_{i \in R_{\text{eval}}} w_i}$$
   Where $R_{\text{eval}}$ excludes general experience requirements to maintain orthogonality.

2. **Semantic Fit ($S_{\text{semantic}}$)**:
   $$S_{\text{semantic}} = \frac{1}{|R_{\text{skills}}|} \sum_{j \in R_{\text{skills}}} \max_{k \in C_{\text{evidence}}} \text{sim}(\vec{r}_j, \vec{c}_k)$$
   Experience requirements are strictly excluded from the semantic fit calculation (Invariant A & C).

3. **Experience Fit ($S_{\text{exp}}$)**:
   $$S_{\text{exp}} = \min\left(\frac{\text{Candidate Years of Experience}}{\text{Required Years of Experience}}, 1.0\right)$$

4. **Dynamic Renormalization**:
   If an optional scoring component (such as `llm_fit`) is disabled or unavailable, the system dynamically renormalizes active component weights:
   $$W_{\text{active}} = \sum_{m \in M_{\text{available}}} W_m, \quad W'_m = \frac{W_m}{W_{\text{active}}}, \quad S_{\text{total}} = \sum_{m \in M_{\text{available}}} W'_m \cdot S_m$$
   This ensures $\sum W'_m = 1.0$ at all times (Invariant E).

5. **Must-Have Gating Indicator**:
   The final composite score is accompanied by an independent boolean flag:
   $$\text{Must-Haves Met} = \bigwedge_{r \in R_{\text{must-have}}} (\text{status}(r) == \text{matched})$$

---

## 17. Evidence-Grounded Skill-Gap Analysis

The skill-gap analyzer (`skill_gap_analyzer.py`) audits candidate shortcomings against the job profile:

* **Gap Categorization**:
  - `missing`: Required skill was completely undetected in candidate resume text.
  - `insufficient`: Skill is present, but candidate lacks required depth, version tier, or associated tenure.
  - `not_evaluable`: Requirement is subjective and must be addressed during live human interviews.
* **Separation of Gaps**: General career experience deficits (e.g., candidate possessing 2 years vs. 5 years required) are classified as tenure gaps, not conflated with technical skill absences.
* **Verbatim Evidence Citations**: Every identified match or partial match includes the exact sentence snippet from the candidate's resume, enabling recruiters to audit claims instantly.

---

## 18. LLM Explanation Layer & Safety Guardrails

The LLM explanation layer (`backend/app/services/explanation_service.py`) provides natural language briefings without compromising scoring integrity:

### Architectural Guardrails
1. **Fact Grounding**: The LLM prompt receives the upstream deterministic results, satisfied requirements, and identified gaps as immutable context. It is instructed to summarize only what is present.
2. **Zero Automated Verdicts**: The LLM is strictly prohibited from generating hiring recommendations, rejection notices, or predictive employability claims.
3. **No Speculation**: The model cannot extrapolate unmentioned credentials (e.g., assuming a candidate knows Django because they listed Python).
4. **Offline Provider Abstraction**:
   - `MockLLMClient`: Offline, deterministic heuristic fallback that operates without internet access or API tokens.
   - `GeminiLiveClient` / `OpenAIClient`: Optional production adapters conforming to the identical schema interface.

---

## 19. Frontend Recruiter Dashboard & Interface Architecture

The presentation layer is implemented as a modern, accessible Next.js 16 application:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                            RECRUITER DASHBOARD                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ Top Navigation: [ Overview ]   [ Job Setup ]   [ Candidate Screening ]      │
├─────────────────────────────────────────────────────────────────────────────┤
│ ACTIVE JOB: Senior Backend Engineer (Python, FastAPI, Postgres, Docker)     │
├──────────────────────────────────────┬──────────────────────────────────────┤
│ CANDIDATE: Alex Morgan               │ HYBRID FIT SCORE: 84.1% [Must-Haves] │
├──────────────────────────────────────┴──────────────────────────────────────┤
│ SCORE BREAKDOWN:                                                            │
│ • Rule Fit: 100%     • Semantic Fit: 64.3%                                  │
│ • Exp Fit:  100%     • Education Fit: 100%                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ REQUIREMENT COVERAGE TABLE:                                                 │
│ Req Name     Type       Status     Evidence Citation                        │
│ Python       Must-Have  Matched    "6+ years building microservices..."     │
│ FastAPI      Must-Have  Matched    "Engineered low-latency APIs in FastAPI" │
│ PostgreSQL   Must-Have  Matched    "Managed 10TB Postgres cluster"          │
│ Docker       Must-Have  Matched    "Containerized deployment workflows"     │
├──────────────────────────────────────┬──────────────────────────────────────┤
│ SKILL GAPS:                          │ LLM EXECUTIVE BRIEFING:              │
│ • None (All core skills satisfied)   │ Grounded synthesis of candidate's    │
│ • Nice-to-have: Kubernetes (Missing) │ microservices background.            │
├──────────────────────────────────────┴──────────────────────────────────────┤
│ ⚠️ HUMAN REVIEW REQUIRED: This tool is an assistive screening aid.          │
│ Final hiring and rejection decisions remain solely with human recruiters.   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Verified Application Routes
* `/` — Recruiter landing page, platform metrics, and architectural overview.
* `/jobs` — Repository of configured job specifications.
* `/jobs/new` — Document upload and text-parsing interface for new job postings.
* `/analysis` — Core candidate screening workspace with real-time scoring, coverage table, and gap audits.
* `/candidates` — Historical candidate evaluation archives.
* `/candidates/[id]` — Detailed audit view for a specific historical candidate evaluation.

---

## 20. Application Programming Interface (API Layer)

The FastAPI backend exposes a clean, strongly typed RESTful API versioned under `/api/v1`:

| Method | Endpoint Path | Request Payload | Response Model | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | None | `HealthResponse` | Liveness check, version, and environment status |
| `POST`| `/api/v1/resumes/parse` | `multipart/form-data` (file) | `DocumentParseResponse` | Validates and extracts raw text from PDF/DOCX |
| `POST`| `/api/v1/resumes/extract`| `multipart/form-data` (file) | `ResumeExtractionResponse`| Parses raw resume into structured `CandidateProfile` |
| `POST`| `/api/v1/jobs/analyze` | JSON (`job_description`, title)| `JobAnalysisResponse` | Extracts structured requirements from raw JD text |
| `POST`| `/api/v1/jobs/analyze/upload`| `multipart/form-data` (file) | `JobAnalysisResponse` | Extracts structured requirements from uploaded JD document |
| `POST`| `/api/v1/skills/normalize` | JSON (`skills: list[str]`)| `SkillNormalizationResponse`| Normalizes raw skill strings to canonical taxonomy |
| `GET` | `/api/v1/skills/taxonomy` | None | `SkillTaxonomyResponse` | Returns canonical skill categories and alias maps |
| `POST`| `/api/v1/matching/analyze`| JSON (`candidate`, `job`)| `CandidateJobMatchResponse` | Executes deterministic and semantic requirement matching |
| `POST`| `/api/v1/matching/semantic`| JSON (`candidate`, `job`)| `SemanticMatchResponse` | Evaluates semantic similarity without scoring |
| `POST`| `/api/v1/matching/from-files`| `multipart/form-data` (2 files)| `CandidateJobMatchWithScore`| End-to-end file upload to full hybrid score pipeline |
| `POST`| `/api/v1/scoring/evaluate`| JSON (`match_result`, `job`)| `ScoreResponse` | Computes hybrid fusion score and component breakdown |
| `POST`| `/api/v1/gaps/analyze` | JSON (`candidate`, `job`)| `SkillGapResponse` | Evaluates missing, insufficient, and un-evaluable gaps |
| `POST`| `/api/v1/explanations/analyze`| JSON (`candidate`, `job`)| `ExplanationResponse` | Generates grounded natural language summary and advice |

---

## 21. Database Architecture & Data Model

The persistence layer is implemented via SQLAlchemy ORM backed by SQLite (`resume_screening.db`):

```text
┌─────────────────┐       1:N       ┌─────────────────────┐
│      jobs       │────────────────<│    requirements     │
└────────┬────────┘                 └─────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐       1:1       ┌─────────────────────┐
│   candidates    │─────────────────│       resumes       │
└────────┬────────┘                 └─────────────────────┘
         │
         ├─── 1:1 ───> ┌─────────────────────┐
         │             │      profiles       │
         │             └─────────────────────┘
         ├─── 1:1 ───> ┌─────────────────────┐
         │             │       scores        │
         │             └─────────────────────┘
         ├─── 1:N ───> ┌─────────────────────┐
         │             │     skill_gaps      │
         │             └─────────────────────┘
         └─── 1:N ───> ┌─────────────────────┐
                       │   recommendations   │
                       └─────────────────────┘
```

### Table Schema Summary
1. `jobs`: Stores job postings, raw JD text, extracted requirement schemas (JSON), and configured component weights.
2. `requirements`: Individual requirements extracted from jobs with category (`skill`, `experience`, `education`) and priority (`mandatory`, `preferred`).
3. `candidates`: Represents an evaluated candidate application linked to a target job with PII masking flags.
4. `resumes`: Preserves uploaded document metadata, file type (`pdf`/`docx`), and extracted raw text for auditability.
5. `profiles`: Strongly validated candidate profile containing contact details, categorized skills, chronological employment, and education credentials.
6. `scores`: Records computed fit metrics (`rule_score`, `semantic_score`, `experience_score`, `total_score`) and JSON weight breakdown.
7. `skill_gaps`: Individual identified skill discrepancies with status (`matched`, `partial`, `missing`) and verbatim evidence quotes.
8. `recommendations`: Grounded skill-development guidance linked to specific candidate skill deficits.

---

## 22. Evaluation & Benchmarking Methodology

To rigorously validate system performance without exposing real candidate data, an evaluation framework was executed in Phase 12:

### Evaluation Dataset Composition
* **10 Synthetic Candidate Resumes**: Realistic resumes spanning diverse technical profiles:
  - Strong Backend Engineer (`01_strong_backend.pdf`)
  - Weak Backend Junior (`02_weak_backend.pdf`)
  - Strong Frontend Developer (`03_strong_frontend.pdf`)
  - Machine Learning Scientist (`04_data_scientist.pdf`)
  - DevOps Cloud Engineer (`05_devops_cloud.pdf`)
  - Junior Generalist (`06_junior_software_engineer.pdf`)
  - Career Transitioner (`07_career_changer.pdf`)
  - Adjacent Skills Candidate (`08_related_skills_candidate.pdf`)
  - Sparse Formatting Resume (`09_sparse_resume.pdf`)
  - Multi-Column Ambiguous Resume (`10_ambiguous_formatting.pdf`)
* **5 Synthetic Job Descriptions**: Comprehensive specifications for Backend, Frontend, Data Science, DevOps, and Entry-Level Software Engineering.
* **10 Curated Ground-Truth Cases**: Pre-calculated benchmark scenarios with explicit expected score ranges, must-have requirements, and known skill gaps.

### Evaluation Criteria
1. **Taxonomy Integrity**: Verification of canonical alias resolution and rejection of non-technical stopwords.
2. **False-Positive Isolation**: Verification that lookalike technologies are strictly blocked from matching.
3. **Scoring Invariants**: Verification of mathematical properties (A through F) governing score orthogonality, tenure independence, dynamic weight renormalization, and 100% calculation reproducibility.
4. **Anti-Hallucination Audit**: Verification that 100% of LLM claims map directly to resume evidence and 0% generate hiring/rejection verdicts.
5. **System Telemetry**: Measurement of component execution latencies across cold and warm inference cycles.

*Methodological Clarification*: The evaluation dataset is entirely synthetic. These benchmarks validate software engineering correctness, mathematical invariance, and architectural integrity; they do not establish empirical claims of real-world hiring efficacy.

---

## 23. Engineering Validation Results

The Phase 12 validation suite verified all acceptance gates:

### Summary of Engineering Acceptance Gates
| Evaluation Category | Acceptance Threshold | Measured Result | Status |
| :--- | :--- | :--- | :---: |
| **Skill Alias Resolution** | $\ge 90.0\%$ accuracy | **100.0%** (13/13 verified) | **PASSED** |
| **Protected Technology Blocking** | 100% isolation | **100.0%** (6/6 protected pairs) | **PASSED** |
| **Scoring Invariants (A–F)** | 100% mathematical compliance | **6/6 Invariants Verified** | **PASSED** |
| **Curated Benchmark Cases** | $\ge 90.0\%$ ground-truth compliance | **10/10 Cases Passed (100%)** | **PASSED** |
| **LLM Evidence Grounding** | 100% grounded citations | **100.0%** grounded | **PASSED** |
| **Hallucinated Credentials** | Exactly 0 instances | **0 detected** | **PASSED** |
| **Automated Hiring Verdicts** | Exactly 0 instances | **0 detected** | **PASSED** |
| **API Smoke Tests** | 100% operational | **7/7 Operational** | **PASSED** |
| **Backend Unit/Integration Tests**| 100% passing | **168/168 Passed** | **PASSED** |
| **Frontend Component Tests** | 100% passing | **21/21 Passed** | **PASSED** |
| **Frontend Production Build** | Zero TypeScript/build errors | **Successful Optimized Build** | **PASSED** |

### Curated Benchmark Results Matrix
| Case ID | Candidate Profile | Target Job Role | Fit Score | Must-Haves Met? | Gaps Found | Benchmark Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| `case_01` | Strong Senior Backend | Senior Backend Engineer | 84.1% | **Yes** | 0 missing | **PASSED** |
| `case_02` | Weak Junior Backend | Senior Backend Engineer | 25.2% | **No** | 6 missing | **PASSED** |
| `case_03` | Strong Frontend | Frontend Developer | 82.8% | **Yes** | 0 missing | **PASSED** |
| `case_04` | Data Scientist | Senior Data Scientist | 84.4% | **Yes** | 0 missing | **PASSED** |
| `case_05` | DevOps / Cloud Engineer | Senior DevOps Engineer | 89.7% | **Yes** | 0 missing | **PASSED** |
| `case_06` | Junior Software Engineer| Entry-Level Engineer | 80.5% | **Yes** | 1 missing | **PASSED** |
| `case_07` | Career Transitioner | Senior Backend Engineer | 56.0% | **No** | 4 missing | **PASSED** |
| `case_08` | Related Skills (Flask/MySQL)| Senior Backend Engineer | 52.7% | **No** | 4 missing | **PASSED** |
| `case_09` | Sparse Resume Structure | Senior Backend Engineer | 35.3% | **No** | 4 missing | **PASSED** |
| `case_10` | Ambiguous Multi-Column | Senior Backend Engineer | 69.9% | **No** | 2 missing | **PASSED** |

### Latency Telemetry (Sample of 5 Warm Execution Runs on CPU)
| Pipeline Stage | Minimum Latency | Median Latency | 95th Percentile (p95) |
| :--- | :---: | :---: | :---: |
| Document Parsing (PyMuPDF) | 9.17 ms | 12.33 ms | 17.56 ms |
| Profile & Requirement Extraction | 41.28 ms | 43.72 ms | 47.77 ms |
| Deterministic Rule Matching | 8.43 ms | 10.79 ms | 65.66 ms |
| Hybrid Scoring Computation | 0.20 ms | 0.21 ms | 0.27 ms |
| Skill-Gap Analysis | 0.79 ms | 0.86 ms | 1.01 ms |
| Grounded LLM Explanation | 1.78 ms | 1.93 ms | 2.45 ms |
| **Complete End-to-End Pipeline** | **64.09 ms** | **72.65 ms** | **130.84 ms** |

---

## 24. Live Demonstration Scenarios

In Phase 13, three representative candidate scenarios were packaged and validated for live viva presentation:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DEMO SCENARIO MATRIX                               │
├────────────────────┬────────────────────┬───────────────────────────────────┤
│ Scenario           │ Target Job         │ Demonstrated Behavior             │
├────────────────────┼────────────────────┼───────────────────────────────────┤
│ Scenario A         │ Senior Backend     │ Candidate satisfies all 5 must-   │
│ Alex Morgan        │ Engineer (Python,  │ have skills and 5.0 yr tenure.    │
│ (Strong Match)     │ FastAPI, Postgres, │ Score: 84.1%. All citations tied  │
│                    │ Docker, Redis)     │ to verbatim resume evidence.      │
├────────────────────┼────────────────────┼───────────────────────────────────┤
│ Scenario B         │ Senior Backend     │ Candidate possesses basic Python  │
│ Brian Miller       │ Engineer           │ but lacks 4 mandatory skills and  │
│ (Weak Match)       │                    │ has 0.6 yrs tenure. Score: 25.2%. │
│                    │                    │ Gating flags "Must-Haves Missing".│
├────────────────────┼────────────────────┼───────────────────────────────────┤
│ Scenario C         │ Senior Backend     │ Candidate has 3.0 yrs Flask/MySQL.│
│ Hector Vance       │ Engineer           │ Semantic Fit is high (55.1%), but │
│ (Semantic Contrast)│                    │ Deterministic Engine holds line:  │
│                    │                    │ FastAPI/Postgres are UNMET.       │
└────────────────────┴────────────────────┴───────────────────────────────────┘
```

*Key Technical Showcase in Scenario C*: Demonstrates why pure LLM screening fails and why P_101's hybrid design succeeds. The SentenceTransformer detects that Flask and MySQL are semantically adjacent to FastAPI and PostgreSQL, elevating the contextual score. However, the deterministic engine enforces hard criteria: must-haves are marked as missing, preventing an unqualified candidate from falsely passing initial screening.

---

## 25. Security, Privacy & Responsible AI Considerations

P_101 incorporates responsible engineering principles into every pipeline layer:

1. **Mitigation of Unconscious Bias**:
   * The scoring engine operates exclusively upon technical skills, verified degree types, and quantitative tenure.
   * Candidate demographic attributes (name, gender, age, ethnicity, nationality, physical address, photographs) are strictly excluded from the scoring models.
   * *Precise Academic Disclaimer*: *The system is designed to reduce reliance on demographic or institutional signals during its evaluation pipeline, but this does not constitute proof of absence of bias.*
2. **Deterministic Anti-Hallucination Boundaries**:
   * Scores are calculated mathematically by the deterministic engine. The LLM has zero ability to inflate, deflate, or alter scores.
   * Explanations are constrained by system prompts that prohibit external factual assumptions.
3. **Data Privacy & Operational Security**:
   * Zero third-party cloud data transmission: In default configuration, embedding models and LLM adapters run locally on the host machine.
   * Path sanitization: File upload handlers sanitize incoming filenames to prevent path traversal vulnerabilities.
   * Secret management: Environment variables (`.env`, `.env.local`) isolate configuration from version-controlled source code.
4. **Mandatory Human-in-the-Loop Oversight**:
   * The user interface renders a prominent disclaimer reminding recruiters that the system is an assistive decision-support platform, not an automated hiring authority.

---

## 26. Verified System Limitations

In accordance with academic standards, the following known technical boundaries are acknowledged:

1. **CPU Embedding Cold-Start Latency**: Initial loading of PyTorch and `all-MiniLM-L6-v2` weights on a CPU requires approximately 1.5–2.5 seconds during initial server startup. Once warm, inference completes in under 30 milliseconds.
2. **Absence of Optical Character Recognition (OCR)**: The document parser relies on digital text streams extracted via PyMuPDF. Flattened, scanned image resumes lacking embedded text layers are rejected with a `422 Unprocessable Content` error rather than routed through heavy OCR models.
3. **Taxonomy Coverage Boundaries**: While the canonical skill taxonomy covers major programming languages, cloud providers, web frameworks, and databases, niche or emergent proprietary frameworks outside the taxonomy rely on dense semantic matching rather than canonical alias resolution.
4. **Complex Non-Standard Degree Formats**: International degree equivalents or multi-disciplinary academic minors outside standard bachelor's/master's/doctorate hierarchies require manual recruiter verification.
5. **Single-Candidate Workspace**: The current interface evaluates candidates individually against a target job role. Cross-candidate comparative ranking and batch queue screening were intentionally omitted to maintain focus on auditable single-candidate decision support.

---

## 27. Future Scope & Research Directions

The following enhancements represent natural extensions of the P_101 architecture:

1. **Local OCR Pipeline**: Integration of an efficient local OCR engine (such as Tesseract or PaddleOCR) to extract text from scanned, image-only resume documents.
2. **Dynamic Taxonomy Expansion**: Semi-automated ingestion of public ontology datasets (e.g., ESCO, O*NET) to continuously expand canonical skill alias dictionaries.
3. **Recruiter-Configurable Policy Sliders**: Enabling recruiters to adjust scoring weights (e.g., placing 60% emphasis on Rule Fit for strict compliance roles) via authenticated administrative settings.
4. **Consented Real-World Validation**: Conducting IRB-approved studies with consenting organizations to measure recruiter time savings and usability across diverse real-world hiring pipelines.
5. **Batch Ingestion & Deduplication**: Developing an asynchronous background worker queue (e.g., Celery/Redis) to process large resume batches with duplicate candidate detection.

---

## 28. Conclusion

P_101 successfully demonstrates that AI-assisted resume screening does not require opaque, non-deterministic end-to-end LLM decision-making. By architecturally decoupling **deterministic rule verification**, **dense semantic vector similarity**, and **constrained natural language generation**, the system achieves high interpretability while protecting against common AI failure modes such as hallucination, keyword conflation, and prompt injection.

Through 13 completed phases of rigorous design, implementation, and benchmarking, the project has established:
* Complete orthogonality between technical skill matching, semantic similarity, and experience tenure calculations.
* Verifiable, evidence-grounded skill-gap identification tied to verbatim resume citations.
* A robust, responsive web interface that enhances recruiter productivity while keeping the human recruiter firmly in control of hiring decisions.

P_101 fulfills all project objectives and provides an auditable, transparent engineering blueprint for responsible AI decision support in technical recruitment.

---

## 29. References & Technical Bibliography

1. **FastAPI Documentation & Design Guidelines**: Tiangolo, S. (2024). *FastAPI: Modern, fast (high-performance), web framework for building APIs with Python*. https://fastapi.tiangolo.com
2. **Pydantic Data Validation**: Colvin, S. et al. (2024). *Pydantic: Data validation using Python type hints*. https://docs.pydantic.dev
3. **Sentence-Transformers & Dense Embeddings**: Reimers, N., & Gurevych, I. (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks*. Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing (EMNLP). https://arxiv.org/abs/1908.10084
4. **Pretrained Embedding Weights (`all-MiniLM-L6-v2`)**: Wang, W., Wei, F., Dong, L., Bao, H., Yang, N., & Zhou, M. (2020). *MiniLM: Deep Self-Attention Distillation for Task-Agnostic Compression of Pre-Trained Transformers*. NeurIPS 2020.
5. **PyMuPDF Documentation**: McKie, P., & Liu, R. (2024). *PyMuPDF: High-performance Python bindings for MuPDF*. https://pymupdf.readthedocs.io
6. **Python-docx Library**: Canny, S. (2024). *python-docx: Create and modify Word .docx files in Python*. https://python-docx.readthedocs.io
7. **Next.js & React Framework**: Vercel Inc. (2024). *Next.js Documentation & App Router Architecture*. https://nextjs.org/docs
8. **SQLAlchemy 2.0 Unified Tutorial**: Bayer, M. (2024). *SQLAlchemy Database Toolkit for Python*. https://docs.sqlalchemy.org
9. **European Commission (2024)**: *Proposal for a Regulation laying down harmonised rules on Artificial Intelligence (Artificial Intelligence Act)*. CELEX:52021PC0206.
10. **New York City Department of Consumer and Worker Protection (2023)**: *Automated Employment Decision Tools (AEDT) Rules (Local Law 144)*. NYC Rules.
