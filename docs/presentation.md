# P_101 — Final Project Presentation: Slide Deck & Speaker Notes
### An Evidence-Grounded Recruiter Decision-Support Platform with Hybrid Scoring and Transparent Skill-Gap Auditing

* **Project Identifier**: P_101
* **Format**: 15-Slide Presentation + Speaker Notes + Live Demo Handoff
* **Target Delivery Duration**: 8–12 minutes (slides) + 5–6.5 minutes (live demo)
* **Target Audience**: College Faculty, Project Evaluators, Technical Reviewers, Viva Examiners
* **Baseline Commit**: `9fb0826` (Phases 1–14 Complete & Fully Verified)

---

## Slide Directory & Presentation Map

```text
SLIDE FLOW:
Slide 01: Title & Project Identity               (0:00 - 0:30)
Slide 02: Problem Statement & Industry Context   (0:30 - 1:15)
Slide 03: Project Objectives & Scope             (1:15 - 1:55)
Slide 04: Existing vs. Proposed Screening Model  (1:55 - 2:40)
Slide 05: Five-Tier System Architecture          (2:40 - 3:25)
Slide 06: Production Technology Stack            (3:25 - 3:55)
Slide 07: Unstructured Resume & JD Ingestion     (3:55 - 4:35)
Slide 08: Deterministic vs. Semantic Matching    (4:35 - 5:20)
Slide 09: Multi-Factor Hybrid Scoring Model      (5:20 - 6:05)
Slide 10: Skill-Gap Auditing & LLM Guardrails    (6:05 - 6:50)
Slide 11: Recruiter Web Interface & UX           (6:50 - 7:35)
Slide 12: Engineering Validation & Benchmark     (7:35 - 8:15)
Slide 13: Live Demonstration Workflow            (8:15 - 8:55)
Slide 14: System Limitations & Future Scope      (8:55 - 9:35)
Slide 15: Conclusion & Technical Q&A             (9:35 - 10:00)
```

---

## Slide 1 — Title & Project Identity

### Slide Details
* **Slide Number**: 1 / 15
* **Slide Title**: P_101 — LLM-Based Resume Screening System
* **Slide Subtitle**: An Evidence-Grounded Recruiter Decision-Support Platform
* **Slide Purpose**: Establish project identity, core philosophy, and set the professional tone for faculty evaluators.

### Visual Layout & Content
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                                   P_101                                     │
│                     LLM-BASED RESUME SCREENING SYSTEM                       │
│                                                                             │
│             An Evidence-Grounded Recruiter Decision-Support Platform        │
│          with Deterministic Matching, Dense Embeddings, and Hybrid Scoring  │
│                                                                             │
│     ───────────────────────────────────────────────────────────────────     │
│                                                                             │
│      Student Name:       [Presenter Name / Candidate ID]                    │
│      Degree / Branch:    Bachelor of Technology — Computer Science & Engg.  │
│      Institution:        Department of Computer Science & Engineering       │
│      Academic Year:      2025 – 2026                                        │
│      Project Guide:      [Faculty Guide Name / Department]                  │
│                                                                             │
│      Core Philosophy:    Decision Support, Not Automated Hiring Authority   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Technical Points
* P_101 is an assistive audit tool designed to empower human recruiters, not an automated replacement for human judgment.
* Solves the dual extremes of modern screening: brittle keyword matchers vs. opaque, hallucination-prone black-box LLMs.
* 100% self-contained, reproducible, and executable locally on consumer-grade hardware.

### Speaker Notes (Estimated Duration: ~30 seconds)
> *"Good morning, respected members of the evaluation committee and faculty guides. Today, I am presenting project **P_101: An LLM-Based Resume Screening System**. In today’s recruitment landscape, hiring teams face massive resume volumes. Most organizations resort either to traditional keyword Applicant Tracking Systems, which are brittle and miss qualified candidates, or to end-to-end generative AI prompts, which are opaque, non-deterministic, and prone to hallucinating qualifications. P_101 resolves this dilemma through an evidence-grounded, multi-layered decision-support platform that keeps the human recruiter firmly in control. Let us begin by examining the exact problem statement."*

### Demo Transition Cue
* Transition to Slide 2 to dissect the recruitment screening bottleneck.

---

## Slide 2 — Problem Statement & Industry Context

### Slide Details
* **Slide Number**: 2 / 15
* **Slide Title**: Problem Statement & The Recruitment Bottleneck
* **Slide Purpose**: Define the real-world operational challenges of technical resume screening and outline why current automated tools fail.

### Visual Layout & Content
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                    THE RESUME SCREENING BOTTLENECK                          │
├──────────────────────────────┬──────────────────────────────┬───────────────┤
│ High Application Volume      │ Phrasing & Term Discrepancy  │ Black-Box AI  │
├──────────────────────────────┼──────────────────────────────┼───────────────┤
│ • Recruiters review 100s of  │ • "JS" vs "JavaScript"       │ • Unexplainable│
│   resumes per role.          │ • "Postgres" vs "PostgreSQL" │   percentages │
│ • Severe cognitive fatigue   │ • "K8s" vs "Kubernetes"      │ • Hallucinated│
│   and subjective screening.  │ • Keyword tools miss true    │   qualifications│
│ • Long hiring cycle latency. │   competency synonyms.       │ • Zero audit  │
│                              │ • Vulnerable to keyword spam.│   trail.      │
├──────────────────────────────┴──────────────────────────────┴───────────────┤
│                             CENTRAL REQUIREMENT                             │
│  "Design a transparent first-pass screening system that provides verifiable  │
│   evidence citations while preserving final authority with the human."      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Technical Points
* **Cognitive Fatigue**: Human screeners spend under 10 seconds per resume, leading to inconsistent manual evaluation.
* **Lexical Divergence**: Candidates describe identical proficiencies using diverse acronyms, versions, and synonyms.
* **The Keyword ATS Flaw**: String matching penalizes legitimate synonyms while rewarding manipulative keyword-stuffing.
* **The Generative LLM Flaw**: Direct LLM grading (e.g., "Score this candidate 1 to 10") is non-reproducible, vulnerable to prompt injection, and legally non-compliant under emerging AI employment regulations.

### Speaker Notes (Estimated Duration: ~40 seconds)
> *"The problem begins with scale. Technical recruiters frequently process hundreds of applications for a single opening. When humans review resumes under time pressure, evaluations become inconsistent and fatigued. To cope, companies deploy keyword-based ATS tools. But keyword search is brittle: if a candidate writes 'Postgres' or 'K8s', a naive keyword tool searching for 'PostgreSQL' or 'Kubernetes' marks them as unqualified. Conversely, candidates who mechanically paste keywords can game the system. Recently, developers have tried prompting ChatGPT to rate resumes directly. But direct LLM grading is a black box: it hallucinates skills, cannot produce a reproducible mathematical score, and is susceptible to prompt injection. Our central requirement is to build a transparent, auditable system that extracts structured facts, proves every match with verbatim evidence, and leaves hiring authority with the human."*

### Demo Transition Cue
* Transition to Slide 3 to present the 10 engineering objectives formulated to solve this problem.

---

## Slide 3 — Project Objectives & Scope

### Slide Details
* **Slide Number**: 3 / 15
* **Slide Title**: Project Objectives & Engineering Scope
* **Slide Purpose**: Enumerate the 10 specific, verifiable engineering milestones accomplished across the project lifecycle.

### Visual Layout & Content
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                          10 CORE PROJECT OBJECTIVES                         │
├──────────────────────────────────────┬──────────────────────────────────────┤
│ 1. Structured Document Parsing       │ 6. Multi-Factor Hybrid Scoring       │
│    Extract text from PDF/DOCX with   │    Orthogonal fusion of rules (30%), │
│    strict reading-order preservation.│    semantics (40%), and tenure (20%).│
│                                      │                                      │
│ 2. Structured Job Analysis           │ 7. Evidence-Grounded Skill Gaps      │
│    Classify requirements into must-  │    Audit missing vs insufficient     │
│    have vs nice-to-have categories.  │    skills with verbatim citations.   │
│                                      │                                      │
│ 3. Canonical Skill Normalization     │ 8. Constrained LLM Explanations      │
│    Bidirectional alias graph with    │    Grounded briefing and advice;     │
│    false-positive technology bounds. │    zero automated hiring verdicts.   │
│                                      │                                      │
│ 4. Deterministic Requirement Match   │ 9. Interactive Recruiter Web UI      │
│    Authoritative rule engine for     │    Full-featured Next.js dashboard   │
│    hard criteria compliance.         │    with audit tables and score views.│
│                                      │                                      │
│ 5. Dense Semantic Matching           │ 10. Responsible AI & Human Oversight │
│    SentenceTransformer embeddings    │     Strict decision support; zero    │
│    as non-overriding context.        │     ranking or automated rejection.  │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

### Key Technical Points
* Comprehensive lifecycle coverage from raw PDF parsing to interactive recruiter UI.
* Strict scope boundary: Zero candidate ranking, zero automated hiring/rejection, zero score inflation by LLMs.
* All 10 objectives have been implemented, tested, and validated across 14 developmental phases.

### Speaker Notes (Estimated Duration: ~35 seconds)
> *"To address this challenge rigorously, we formulated ten engineering objectives. First, ingest raw PDF and DOCX files without layout corruption. Second, extract structured requirements from job descriptions, separating must-haves from nice-to-haves. Third, build a canonical skill taxonomy with alias mapping and strict protection between lookalike technologies. Fourth, implement an authoritative deterministic matching engine. Fifth, use local dense embeddings to capture semantic context. Sixth, formulate a hybrid scoring model that mathematically separates skills from tenure. Seventh, isolate skill gaps with verbatim quotes. Eighth, build a constrained LLM explanation adapter with zero hiring verdicts. Ninth, provide a modern recruiter web dashboard. And tenth, enforce ethical guardrails ensuring human decision authority. Let us compare this approach against conventional systems."*

### Demo Transition Cue
* Move to Slide 4 for a direct comparative analysis between conventional approaches and P_101.

---

## Slide 4 — Existing vs. Proposed Screening Model

### Slide Details
* **Slide Number**: 4 / 15
* **Slide Title**: Comparative Analysis: Conventional vs. Proposed Approach
* **Slide Purpose**: Highlight the technical superiority of P_101's decoupled design over manual review, keyword ATS, and monolithic LLM prompting.

### Visual Layout & Content
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                  PARADIGM COMPARISON: SCREENING APPROACHES                  │
├────────────────────┬────────────────────┬───────────────────┬───────────────┤
│ Dimension          │ Manual Screening   │ Keyword ATS       │ P_101 Platform│
├────────────────────┼────────────────────┼───────────────────┼───────────────┤
│ Throughput         │ Very Low (<10/hr)  │ Instantaneous     │ High (<150ms) │
│ Synonym Handling   │ Subjective / High  │ Zero (Fails "JS") │ 100% Aliases  │
│ Context Awareness  │ High               │ Zero              │ Dense Vectors │
│ Tenure Calculation │ Manual / Prone     │ None              │ Quantitative  │
│ Hallucination Risk │ None               │ None              │ Zero (Guarded)│
│ Audit Trail        │ None               │ None              │ Exact Quotes  │
│ Must-Have Gating   │ Inconsistent       │ Strict String     │ Authoritative │
│ Final Authority    │ Human Screener     │ Algorithmic Filter│ Human Decision│
└────────────────────┴────────────────────┴───────────────────┴───────────────┘
```

### Key Technical Points
* **Keyword ATS**: High speed, but completely blind to semantic context and synonyms.
* **Monolithic LLMs**: High contextual awareness, but catastrophic lack of reproducibility, transparency, and hallucination control.
* **P_101 Hybrid Architecture**: Combines the mathematical rigor of deterministic rules, the vocabulary flexibility of dense embeddings, and the synthesization clarity of constrained LLMs.
* **Ethical AI Disclaimer**: P_101 reduces reliance on demographic signals, but does not claim elimination of all bias or guaranteed hiring outcomes.

### Speaker Notes (Estimated Duration: ~45 seconds)
> *"This comparison table illustrates the fundamental trade-offs in candidate screening. Manual review offers good context understanding, but suffers from low throughput and fatigue. Keyword ATS provides high speed, but fails on simple abbreviations like 'JS' or 'K8s', lacks semantic context, and provides no audit trail. Pure generative LLM screening understands language well, but introduces severe risks: hallucinated degrees, high latency, non-reproducible scoring, and prompt injection vulnerabilities. P_101 combines the strengths of both worlds while eliminating their flaws. We use deterministic rules for hard gatekeeping, dense sentence embeddings for semantic context, and an LLM strictly for evidence-grounded summarization. The human recruiter receives an auditable, instant breakdown in under 150 milliseconds. Next, let us inspect the system architecture."*

### Demo Transition Cue
* Transition to Slide 5 to examine the five-tier decoupled architecture.

---

## Slide 5 — Five-Tier System Architecture

### Slide Details
* **Slide Number**: 5 / 15
* **Slide Title**: System Architecture & Decoupled Pipeline
* **Slide Purpose**: Present the five-tier decoupled pipeline and emphasize the critical separation between deterministic computation and LLM explanation.

### Visual Layout & Content
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FIVE-TIER ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. PRESENTATION LAYER (Next.js 16 / React 19 / Tailwind CSS v4)            │
│     Recruiter Dashboard • Job Setup • Screening Workspace • Candidate Audit │
├─────────────────────────────────────────────────────────────────────────────┤
│  2. API & ROUTING LAYER (FastAPI / Pydantic v2 / REST)                      │
│     /jobs • /resumes • /skills • /matching • /scoring • /gaps • /explanations│
├─────────────────────────────────────────────────────────────────────────────┤
│  3. PROCESSING SERVICES LAYER                                               │
│     PyMuPDF Document Parser • Rule Extractor • Canonical Skill Normalizer   │
├─────────────────────────────────────────────────────────────────────────────┤
│  4. DECISION & AI LAYER                                                     │
│     Deterministic Engine ───> SentenceTransformer ───> Multi-Layer Scorer   │
│     (Must-Have Authority)     (Dense Cosine Vectors)   (Orthogonal Weights) │
│                                         │                                   │
│                                         ▼                                   │
│                              Constrained LLM Adapter                        │
│                           (Briefing Only • Zero Scoring)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  5. DATA & PERSISTENCE LAYER (SQLAlchemy 2.0 / SQLite)                      │
│     Jobs • Candidates • Resumes • Profiles • Requirements • Scores • Gaps   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Technical Points
* **Pipe-and-Filter Pipeline**: Every stage is strongly typed with Pydantic schemas and independently testable.
* **Separation of Authority**: The LLM is strictly downstream. It receives facts determined by the deterministic engine; it cannot alter scores or satisfy requirements.
* **Database Isolation**: Historical evaluations, raw text, and extracted profiles are stored in SQLite via SQLAlchemy ORM for reproducible audit trails.

### Speaker Notes (Estimated Duration: ~45 seconds)
> *"Here is the architectural blueprint of P_101. It is structured into five strictly decoupled layers. At the top is our Presentation Layer, built with Next.js 16 and React 19. It communicates via REST with our FastAPI backend. In Layer 3, incoming resumes and job descriptions are parsed by our Document Processing services. Layer 4 is the heart of the system—the Decision and AI Layer. Notice the strict hierarchy: the Deterministic Matching Engine is the sole mathematical authority over hard requirements. The SentenceTransformer embedding model evaluates semantic proximity as supporting evidence. These feed into our Multi-Layer Hybrid Scorer. Downstream from scoring, our Constrained LLM Adapter synthesizes the verified findings into plain English. Crucially: the LLM has zero authority over the score, and cannot override missing must-haves. Finally, Layer 5 persists all data in SQLite for full auditability. Let us review the technology stack that powers this."*

### Demo Transition Cue
* Transition to Slide 6 to review the verified production technologies.

---

## Slide 6 — Production Technology Stack

### Slide Details
* **Slide Number**: 6 / 15
* **Slide Title**: Technology Stack & Local Execution Environment
* **Slide Purpose**: Provide evaluators with a verified, factual inventory of frameworks, libraries, and models used across the system.

### Visual Layout & Content
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                     VERIFIED PRODUCTION TECHNOLOGY STACK                    │
├──────────────────────┬─────────────────────────┬────────────────────────────┤
│ Subsystem            │ Framework / Library     │ Engineering Role           │
├──────────────────────┼─────────────────────────┼────────────────────────────┤
│ Backend API          │ Python 3.11+ / FastAPI  │ Async REST API & Routing   │
│ Data Validation      │ Pydantic v2             │ Schema & Type Validation   │
│ Frontend UI          │ Next.js 16 / React 19   │ Server/Client Recruiter App│
│ UI Styling & Icons   │ Tailwind CSS / Lucide   │ Modern Responsive Styling  │
│ Document Parsing     │ PyMuPDF (`fitz`)        │ High-Speed PDF Text Flow   │
│ Word Document Parser │ python-docx             │ Paragraph & Table Parser   │
│ Dense Vector NLP     │ sentence-transformers   │ Local Dense Embeddings     │
│ Pretrained Model     │ all-MiniLM-L6-v2        │ 384-Dim PyTorch Vectors    │
│ Relational Database  │ SQLite / SQLAlchemy 2.0 │ Local Persistent Storage   │
│ Backend Testing      │ pytest / pytest-asyncio │ 168 Unit & Invariant Tests │
│ Frontend Testing     │ Vitest / Testing Lib    │ 21 Component & UI Tests    │
└──────────────────────┴─────────────────────────┴────────────────────────────┘
```

### Key Technical Points
* **100% Offline Capability**: Employs local sentence embeddings and a robust `MockLLMClient` fallback, requiring zero external API keys or cloud subscriptions.
* **Zero Bloat**: Only battle-tested, standard open-source libraries are used. No unverified third-party SaaS dependencies.
* **Hardware Efficiency**: Runs seamlessly on standard multi-core consumer laptops on CPU without requiring dedicated GPU acceleration.

### Speaker Notes (Estimated Duration: ~30 seconds)
> *"This table summarizes our technology stack. Every component was selected for performance, reliability, and auditability. The backend is built on Python 3.11 with FastAPI and Pydantic v2. The frontend uses Next.js 16 with React 19, TypeScript, and Tailwind CSS. For document parsing, we utilize PyMuPDF and python-docx, which handle multi-column reading order and table deduplication. Our NLP layer runs `all-MiniLM-L6-v2` locally on CPU via `sentence-transformers`, generating 384-dimensional dense vectors in milliseconds. Persistence is handled by SQLite and SQLAlchemy. The entire system is 100% self-contained and operates completely offline with zero cloud fees. Next, let us see how resumes and job descriptions enter this pipeline."*

### Demo Transition Cue
* Transition to Slide 7 to explore document ingestion and schema structuring.

---

## Slide 7 — Unstructured Resume & JD Ingestion

### Slide Details
* **Slide Number**: 7 / 15
* **Slide Title**: Unstructured Document Processing & Structuring Pipeline
* **Slide Purpose**: Illustrate how binary resume documents and job descriptions are transformed into validated domain schemas.

### Visual Layout & Content
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DOCUMENT INGESTION & STRUCTURING                         │
├──────────────────────────────────────┬──────────────────────────────────────┤
│ 1. CANDIDATE RESUME PROCESSING       │ 2. JOB DESCRIPTION PROCESSING        │
│                                      │                                      │
│ Upload (.pdf / .docx)                │ Input (Raw Text / PDF / DOCX)        │
│   ↓                                  │   ↓                                  │
│ Binary Header Validation             │ Requirement Extraction               │
│ • %PDF & PK\x03\x04 Magic Bytes      │ • Must-Have (Hard Criteria)          │
│ • Rejects Scanned/Blank (422 Error)  │ • Nice-to-Have (Preferred Skills)    │
│   ↓                                  │   ↓                                  │
│ PyMuPDF Reading Order Extraction     │ Category Segmentation                │
│ • sort=True preserves multi-column   │ • Technical Skills                   │
│   ↓                                  │ • Experience Tenure Thresholds       │
│ Structured CandidateProfile          │ • Education Credentials              │
│ • Contact: Email, Phone, Links       │ • Responsibilities & Scope           │
│ • Categorized Skills & Dates         │   ↓                                  │
│ • Chronological Work Experience      │ Validated JobProfile Schema          │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

### Key Technical Points
* **Security & Validation**: Binary magic bytes prevent file spoofing; file size caps prevent memory overflow.
* **Layout Normalization**: Multi-column resumes are parsed in natural top-to-bottom, left-to-right reading order using PyMuPDF block sorting.
* **Scanned Document Guard**: Zero-text image-only resumes raise an informative `422 ScannedDocumentError` rather than feeding empty strings to the matching engine.

### Speaker Notes (Estimated Duration: ~40 seconds)
> *"Before evaluating a candidate, we must extract clean, structured data from messy real-world documents. On the resume side, incoming files pass binary magic-byte inspection to verify file health and prevent malicious spoofing. If a PDF is a flat image without text, our parser catches it immediately with a 422 error. For valid PDFs, PyMuPDF sorts text blocks to preserve natural reading order across multi-column layouts. We then extract clean contact details, skills, chronological employment, and education into a strongly validated Pydantic schema. Simultaneously, the job description is analyzed to extract structured requirements, categorizing them into mandatory must-haves and preferred nice-to-haves across skills, tenure, and education. Once both schemas are validated, they proceed to matching."*

### Demo Transition Cue
* Transition to Slide 8 to see how deterministic and semantic matching operate in tandem.

---

## Slide 8 — Deterministic vs. Semantic Matching

### Slide Details
* **Slide Number**: 8 / 15
* **Slide Title**: Deterministic Authority vs. Semantic Supporting Context
* **Slide Purpose**: Explain the two matching mechanisms and demonstrate how P_101 prevents semantic similarity from falsely satisfying hard rules.

### Visual Layout & Content
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                     THE DUAL MATCHING ENGINE DESIGN                         │
├──────────────────────────────────────┬──────────────────────────────────────┤
│ 1. DETERMINISTIC MATCHING ENGINE     │ 2. DENSE SEMANTIC MATCHING ENGINE    │
│    (Authoritative Gatekeeper)        │    (Supporting Contextual Relevance) │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ • Canonical Skill Normalization      │ • Pretrained all-MiniLM-L6-v2 model  │
│   (e.g., "K8s", "kube" → Kubernetes) │ • 384-dimensional dense embeddings   │
│ • Explicit Degree Hierarchy          │ • Cosine similarity bounded [0.0,1.0]│
│ • Quantitative Tenure Calculation    │ • Evaluates conceptual alignment     │
│ • Protected Technology Isolation     │ • Contextual relevance threshold 0.45│
│   (Java ≠ JS, C ≠ C++, Py ≠ PyTorch) │ • High similarity threshold 0.70     │
├──────────────────────────────────────┴──────────────────────────────────────┤
│                          CRITICAL DESIGN INVARIANT                          │
│   "Semantic similarity provides supporting evidence; it CANNOT satisfy a    │
│    missing must-have requirement or override deterministic authority."      │
│                                                                             │
│   EXAMPLE: Candidate has MySQL  |  Job requires PostgreSQL (Must-Have)      │
│   • Semantic Fit: High (~0.55)  → Recognizes relational database context     │
│   • Deterministic Match: UNMET  → PostgreSQL requirement remains unsatisfied│
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Technical Points
* **Orthogonal Roles**: Deterministic matching verifies hard facts; semantic matching measures conceptual proximity.
* **The MySQL vs. PostgreSQL Showcase**: A candidate with MySQL demonstrates database familiarity, earning high semantic similarity, but the deterministic engine strictly marks the PostgreSQL requirement as missing.
* **Protected Technology Matrix**: Guarantees zero false-positive conflation between dangerous pairs (`Java != JavaScript`, `C != C++`, `Python != PyTorch`, `React != React Native`, `AWS != AWS Lambda`).

### Speaker Notes (Estimated Duration: ~45 seconds)
> *"Slide 8 highlights our core technical innovation. We deploy two distinct matching engines. The Deterministic Engine is our authoritative gatekeeper. It resolves skill synonyms using our canonical taxonomy—for instance, mapping 'K8s' to 'Kubernetes'—while enforcing our Protected Technology Matrix to ensure Java and JavaScript or C and C++ are never conflated. It outputs four states: matched, partial, unmatched, or not evaluable. In parallel, our Semantic Engine computes dense cosine embeddings using `all-MiniLM-L6-v2` to understand project context. Now, here is our critical design invariant: semantic similarity provides supporting evidence, but it can never override a missing must-have. Consider a candidate with MySQL applying for a role demanding PostgreSQL. Our semantic engine awards them a 0.55 similarity score because it recognizes relational database context. But our deterministic engine holds the line: PostgreSQL is marked UNMET, and the candidate is flagged with 'Must-Haves Missing'. Next, let us see how these sub-scores fuse into a hybrid score."*

### Demo Transition Cue
* Transition to Slide 9 to examine the mathematical hybrid scoring formulation.

---

## Slide 9 — Multi-Factor Hybrid Scoring Model

### Slide Details
* **Slide Number**: 9 / 15
* **Slide Title**: Multi-Factor Hybrid Scoring & Orthogonal Weights
* **Slide Purpose**: Walk through the scoring formula, component weights, dynamic renormalization, and the prevention of experience double-counting.

### Visual Layout & Content
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MULTI-FACTOR HYBRID SCORING                         │
├──────────────────────┬─────────┬────────────────────────────────────────────┤
│ Component            │ Weight  │ Measurement Focus                          │
├──────────────────────┼─────────┼────────────────────────────────────────────┤
│ 1. Rule Fit          │   30%   │ Deterministic technical skill match ratio  │
│ 2. Semantic Fit      │   40%   │ Dense vector cosine alignment of evidence  │
│ 3. Experience Fit    │   20%   │ Quantitative tenure ratio: min(tenure/req) │
│ 4. LLM-Supported Fit │   10%   │ Grounded qualification depth assessment    │
├──────────────────────┴─────────┴────────────────────────────────────────────┤
│                           MATHEMATICAL PROPERTIES                           │
│                                                                             │
│ • Experience Separation: General career tenure is EXCLUDED from Rule Fit    │
│   and Semantic Fit, preventing double-counting (Invariants A, B, C, D).     │
│                                                                             │
│ • Dynamic Renormalization: If an optional component (e.g. LLM Fit) is       │
│   unavailable, active weights dynamically scale to sum exactly to 1.0.      │
│                                                                             │
│ • Gating Flag: Independent boolean flag indicates whether all must-haves    │
│   are satisfied, regardless of the overall numerical score.                 │
│                                                                             │
│ Note: Configured engineering prototype weights; not industry-optimal claims.│
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Technical Points
* **Orthogonality**: Experience tenure is evaluated strictly via the ratio formula $\min(\text{candidate\_years} / \text{required\_years}, 1.0)$ and is entirely absent from the Rule Fit and Semantic Fit equations.
* **Dynamic Weight Renormalization**: If `llm_fit` is disabled, weights renormalize ($30/90 \to 33.3\%$, $40/90 \to 44.4\%$, $20/90 \to 22.2\%$) preserving a total sum of $1.0$.
* **Auditability**: Scores are 100% reproducible down to four decimal places.

### Speaker Notes (Estimated Duration: ~45 seconds)
> *"Slide 9 shows our hybrid scoring architecture. We combine four orthogonal components: Rule Fit at 30%, Semantic Fit at 40%, Experience Fit at 20%, and LLM-Supported Fit at 10%. We emphasize that these are project-configured engineering weights, not claims of industry optimality. Notice our mathematical safeguards: during our Phase 8 audits, we proved that general career tenure was being mixed into semantic vectors and rule counts. We refactored the architecture so that experience is calculated solely through our tenure ratio formula and strictly excluded from Rule Fit and Semantic Fit. Furthermore, if an optional component like LLM Fit is disabled, our engine dynamically renormalizes the remaining weights so that they always sum to exactly 1.0. Finally, our score is accompanied by an independent 'Must-Haves Met' gating flag. Even if a candidate scores 60% on adjacent skills, recruiters instantly see if mandatory skills are missing. Let us now examine how we identify skill gaps and protect LLM integrity."*

### Demo Transition Cue
* Transition to Slide 10 to inspect skill-gap categorization and LLM guardrails.

---

## Slide 10 — Skill-Gap Auditing & LLM Guardrails

### Slide Details
* **Slide Number**: 10 / 15
* **Slide Title**: Evidence-Grounded Skill Gaps & Responsible AI Guardrails
* **Slide Purpose**: Showcase the four skill-gap dimensions and present the strict responsible-AI boundaries governing LLM text generation.

### Visual Layout & Content
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                      SKILL GAPS & RESPONSIBLE AI                            │
├──────────────────────────────────────┬──────────────────────────────────────┤
│ 1. SKILL-GAP AUDITING DIMENSIONS     │ 2. CONSTRAINED LLM GUARDRAILS        │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ • Satisfied:                         │ • Evidence Grounding:                │
│   Requirement met; anchored to       │   LLM prompt receives only upstream  │
│   verbatim resume quote.             │   deterministic facts.               │
│                                      │                                      │
│ • Insufficient:                      │ • Zero Automated Verdicts:           │
│   Skill present, but lacks required  │   Strictly prohibited from saying    │
│   depth, version, or tenure.         │   "Hire", "Reject", or "Accept".     │
│                                      │                                      │
│ • Missing:                           │ • Anti-Speculation Constraint:       │
│   Required skill completely absent   │   Cannot assume unmentioned skills   │
│   from candidate profile text.       │   (e.g., assuming Django from Python)│
│                                      │                                      │
│ • Not Evaluable:                     │ • Score Integrity:                   │
│   Subjective qualities reserved for  │   LLM cannot alter, inflate, or      │
│   live human interviews.             │   deflate upstream computed scores.  │
├──────────────────────────────────────┴──────────────────────────────────────┤
│  MANDATORY DISCLAIMER: Assistive decision support only. Matching scores and │
│  LLM recommendations do not constitute hiring or rejection decisions.      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Technical Points
* **Actionable Gap Isolation**: Recruiters see exactly what is missing and can provide constructive feedback or design targeted interview questions.
* **Immutable Scores**: The LLM acts purely as a summarizer. It has zero power to alter the mathematical score computed by the deterministic engine.
* **Human-in-the-Loop**: Prominent UI disclaimers reinforce that human recruiters make all hiring decisions.

### Speaker Notes (Estimated Duration: ~45 seconds)
> *"On Slide 10, we look at skill-gap auditing and responsible AI guardrails. In technical hiring, recruiters do not just want a score—they want to know where the candidate falls short. Our engine categorizes every requirement into one of four states: Satisfied, Insufficient, Missing, or Not Evaluable for subjective qualities like 'team player' that belong in an interview. Every satisfied item is linked to a verbatim quote from the resume. On the right, we highlight our LLM guardrails. In many modern AI systems, the LLM is given unconstrained authority. In P_101, the LLM is strictly constrained: it only receives verified facts from the deterministic engine. It is explicitly prohibited from generating hiring or rejection verdicts, it cannot speculate on unmentioned skills, and it cannot alter the mathematical score. The user interface prominently displays a human-review disclaimer. Now, let us look at the recruiter web interface where all of this comes together."*

### Demo Transition Cue
* Transition to Slide 11 to view the recruiter web dashboard and UI layout.

---

## Slide 11 — Recruiter Web Interface & UX

### Slide Details
* **Slide Number**: 11 / 15
* **Slide Title**: Recruiter Web Dashboard & Audit Interface
* **Slide Purpose**: Display the real frontend interface components implemented in Next.js and explain the recruiter screening workflow.

### Visual Layout & Content
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                          RECRUITER WORKSPACE UX                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   [ Dashboard ]             [ Job Setup ]            [ Candidate Screening ]│
│                                                                             │
│  ┌─────────────────────────────────┐   ┌─────────────────────────────────┐  │
│  │ Overall Score Badge             │   │ Score Breakdown Grid            │  │
│  │                                 │   │ • Rule Fit:        100.0%       │  │
│  │         84.1%                   │   │ • Semantic Fit:     64.3%       │  │
│  │   [ Must-Haves Met ] (Green)    │   │ • Experience Fit:  100.0%       │  │
│  │   High Match Status             │   │ • Education Fit:   100.0%       │  │
│  └─────────────────────────────────┘   └─────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Requirement Coverage Table                                            │  │
│  │ Requirement   Type       Status    Verified Verbatim Citation         │  │
│  │ Python        Must-Have  Matched   "6+ years building microservices.."│  │
│  │ FastAPI       Must-Have  Matched   "Engineered high-throughput APIs.."│  │
│  │ PostgreSQL    Must-Have  Matched   "Architected 10TB Postgres DB.."   │  │
│  │ Docker        Must-Have  Matched   "Containerized multi-tier apps.."  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────┐   ┌─────────────────────────────────┐  │
│  │ Skill Gap Analysis Card         │   │ Grounded LLM Explanation Card   │  │
│  │ • Missing: None                 │   │ Executive summary of verified   │  │
│  │ • Preferred: Kubernetes (Miss)  │   │ strengths and targeted advice.  │  │
│  └─────────────────────────────────┘   └─────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Technical Points
* **Fast, Accessible UX**: Built with Next.js 16 and Tailwind CSS v4, supporting intuitive keyboard navigation and screen-reader semantics.
* **Interactive Evidence Auditing**: Recruiters can click "Show Snippet" on any requirement row to expand the exact sentence extracted from the PDF resume.
* **Complete Transparency**: All 4 sub-scores are visible simultaneously alongside the overall percentage.

### Speaker Notes (Estimated Duration: ~45 seconds)
> *"Slide 11 shows our recruiter web interface. This is not a mockup; it is the actual Next.js application running on `localhost:3000`. At the top left, the recruiter sees the Overall Score Badge—in this case, 84.1%—accompanied by our prominent green 'Must-Haves Met' badge. To the right is our 4-quadrant Score Breakdown Card, showing Rule Fit, Semantic Fit, Experience Fit, and Education Fit independently. Below that is our Requirement Coverage Table. For every requirement, recruiters see its priority, its match status, and an expandable citation showing the exact sentence from the candidate's resume where the skill was identified. Below the table, the left panel audits Skill Gaps, while the right panel renders the grounded LLM Executive Briefing. Everything the recruiter needs to make a fair, evidence-based judgment is visible on one screen. Next, let us inspect our engineering validation results."*

### Demo Transition Cue
* Transition to Slide 12 to review the Phase 12 evaluation metrics and benchmark gates.

---

## Slide 12 — Engineering Evaluation & Results

### Slide Details
* **Slide Number**: 12 / 15
* **Slide Title**: Engineering Validation & Benchmark Gates
* **Slide Purpose**: Present the quantitative verification results from Phase 12 across 189 total regression tests.

### Visual Layout & Content
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 12 BENCHMARK & EVALUATION RESULTS                  │
├─────────────────────┬─────────────────────┬─────────────────────────────────┤
│ 10 / 10 (100%)      │ 6 / 6 (100%)        │ 7 / 7 (100%)                    │
│ Curated Benchmark   │ Mathematical Scoring│ API End-to-End                  │
│ Test Cases Passed   │ Invariants Verified │ Smoke Tests Operational         │
├─────────────────────┼─────────────────────┼─────────────────────────────────┤
│ 168 / 168 Passed    │ 21 / 21 Passed      │ 189 TOTAL PASSING               │
│ Backend Pytest Suite│ Frontend Vitest UI  │ REGRESSION TESTS                │
├─────────────────────┼─────────────────────┼─────────────────────────────────┤
│ 100% LLM Grounding  │ 0 Hallucinations    │ 0 Automated Verdicts            │
│ Verified Citations  │ Detected in Output  │ Generated Across Entire Suite   │
├─────────────────────┴─────────────────────┴─────────────────────────────────┤
│                       SYSTEM LATENCY TELEMETRY (CPU)                        │
│   • Document Parsing:   12.3 ms  |  • Hybrid Scoring:          0.2 ms       │
│   • Profile Extraction: 43.7 ms  |  • Skill-Gap Analysis:      0.8 ms       │
│   • Rule Matching:      10.8 ms  |  • Grounded Explanation:   1.9 ms       │
│   ─── TOTAL END-TO-END PIPELINE LATENCY: 72.65 ms (Median) / 130.8 ms (p95) ──│
│                                                                             │
│   Note: Project engineering validation results using synthetic benchmark    │
│   datasets; does not represent empirical claims of industry hiring efficacy.│
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Technical Points
* **189 Regression Tests**: 168 backend tests (`pytest`) + 21 frontend tests (`vitest`) passing with 100% clean exit codes.
* **100% Invariant Compliance**: Verified that experience tenure changes affect only `experience_fit`, and dynamic weight renormalization sums to 1.0.
* **Blazing Fast CPU Latency**: Complete end-to-end pipeline executes in a median of 72.65 ms on standard consumer CPU.

### Speaker Notes (Estimated Duration: ~40 seconds)
> *"On Slide 12, we present our Phase 12 engineering evaluation results. We validated our system across a synthetic benchmark dataset of 10 resumes, 5 job descriptions, and 10 curated test cases. As shown in the metric cards, 10 out of 10 curated benchmark cases passed ground-truth expectations. All 6 mathematical scoring invariants held true under testing. All 7 API smoke tests were operational. In our regression suites, all 168 backend pytest cases and all 21 frontend Vitest cases passed cleanly—a total of 189 passing tests. Across all evaluation runs, we measured 100% factual grounding in LLM citations, exactly zero hallucinated credentials, and exactly zero automated hiring verdicts. Furthermore, our pipeline latency is exceptional: on standard consumer CPU, our median end-to-end processing time is just 72.65 milliseconds. We explicitly clarify that these metrics validate software engineering correctness on synthetic data, not real-world hiring efficacy. Next, let us outline our live demonstration workflow."*

### Demo Transition Cue
* Transition to Slide 13 to introduce the live demonstration scenarios.

---

## Slide 13 — Live Demonstration Workflow

### Slide Details
* **Slide Number**: 13 / 15
* **Slide Title**: Live Demonstration Scenarios & Workflow
* **Slide Purpose**: Outline the step-by-step recruiter workflow and introduce the three candidate scenarios for the live demo handoff.

### Visual Layout & Content
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LIVE DEMO SCENARIO MATRIX (~5-6.5 MIN)                   │
├────────────────────┬────────────────────┬───────────────────────────────────┤
│ Scenario Candidate │ Target Role        │ Demonstrated Behavior & Outcome   │
├────────────────────┼────────────────────┼───────────────────────────────────┤
│ Step 1: Job Setup  │ Senior Backend     │ Ingest 01_backend_engineer.pdf;   │
│ Baseline Job       │ Engineer           │ extract 5 must-haves & 5.0 yr exp.│
├────────────────────┼────────────────────┼───────────────────────────────────┤
│ Scenario A         │ Senior Backend     │ Meets all 5 must-haves; 6.2 yr exp│
│ Alex Morgan        │ Engineer           │ Overall Score: 84.1% (High Match) │
│ (Strong Match)     │                    │ [ Must-Haves Met ] (Green Badge)  │
├────────────────────┼────────────────────┼───────────────────────────────────┤
│ Scenario B         │ Senior Backend     │ Has Python, but lacks 4 must-haves│
│ Brian Miller       │ Engineer           │ and has 0.6 yr exp. Score: 25.2%  │
│ (Weak Match)       │                    │ [ Must-Haves Missing ] (Red Badge)│
├────────────────────┼────────────────────┼───────────────────────────────────┤
│ Scenario C         │ Senior Backend     │ Has 3.0 yrs Flask/MySQL. High     │
│ Hector Vance       │ Engineer           │ Semantic Fit (55.1%), but Rule Fit│
│ (Semantic Contrast)│                    │ holds line: Must-Haves UNMET.     │
├────────────────────┴────────────────────┴───────────────────────────────────┤
│   Step 5: Recruiter Review → Expand evidence quotes & verify human oversight │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Technical Points
* **Three Diverse Archetypes**: Evaluates a strong qualified engineer, an under-qualified junior, and a candidate with adjacent web technologies.
* **The Definitive Proof in Scenario C**: Proves that P_101 does not let high semantic similarity bypass strict requirements.
* **Target Timing**: Complete live demonstration executes smoothly in 5 to 6.5 minutes.

### Speaker Notes (Estimated Duration: ~40 seconds)
> *"Slide 13 outlines the exact live demonstration we will conduct following this slide presentation. We will walk through three distinct candidate scenarios against our baseline Senior Backend Engineer position. In Step 1, we upload the job description and extract 5 must-haves and a 5-year tenure requirement. In Scenario A, we screen Alex Morgan—a strong candidate with 6.2 years of FastAPI, PostgreSQL, and Docker experience. Alex achieves an 84.1% fit score with a green 'Must-Haves Met' badge. In Scenario B, we screen Brian Miller, a junior candidate with basic Python. Despite having the Python keyword, Brian lacks 4 must-haves and has only 0.6 years tenure; the score drops to 25.2% with a red 'Must-Haves Missing' badge. In Scenario C, we screen Hector Vance, who possesses Flask and MySQL. Here, we demonstrate our hybrid advantage: Hector achieves a high semantic score of 55.1%, but our deterministic engine holds the line: must-haves remain missing. Before launching the live demo, let us review our limitations and future scope."*

### Demo Transition Cue
* Transition to Slide 14 to review system limitations and future research scope.

---

## Slide 14 — System Limitations & Future Scope

### Slide Details
* **Slide Number**: 14 / 15
* **Slide Title**: System Limitations & Future Engineering Scope
* **Slide Purpose**: Provide a candid, academic review of current technical boundaries and articulate future research directions.

### Visual Layout & Content
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       LIMITATIONS & FUTURE SCOPE                            │
├──────────────────────────────────────┬──────────────────────────────────────┤
│ CURRENT SYSTEM LIMITATIONS           │ FUTURE RESEARCH & EXTENSIONS         │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ • CPU Embedding Cold Start:          │ • Local OCR Pipeline:                │
│   Initial PyTorch model load takes   │   Integrate Tesseract / PaddleOCR to │
│   ~1.5-2.5s on first startup.        │   support image-only scanned PDFs.   │
│                                      │                                      │
│ • No Native OCR for Scanned Files:   │ • Dynamic Ontology Integration:      │
│   Image-only PDFs are rejected via   │   Incorporate public ESCO and O*NET  │
│   422 error; requires digital text.  │   skill graphs dynamically.          │
│                                      │                                      │
│ • Fixed Skill Taxonomy Bounds:       │ • Recruiter Policy Sliders:          │
│   Emergent proprietary frameworks    │   Allow recruiters to adjust weights │
│   rely on semantics, not aliases.    │   (e.g., 60% Rule Fit) per role.     │
│                                      │                                      │
│ • Single-Candidate Workspace:        │ • Consented Real-World Benchmarks:   │
│   Analyzes one candidate at a time;  │   Conduct IRB-approved studies with  │
│   no comparative stack-ranking.      │   consenting hiring organizations.   │
│                                      │                                      │
│ • Synthetic Benchmark Validation:    │ • Asynchronous Batch Queue:          │
│   Validation data is synthetic; does │   Implement Celery/Redis queue for   │
│   not prove industry hiring efficacy.│   bulk background resume processing. │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

### Key Technical Points
* **Academic Honesty**: Acknowledges existing boundaries (lack of OCR, synthetic dataset, CPU cold start) transparently.
* **Separation of Present vs. Future**: Clearly demarcates existing implemented functionality from future roadmap items.

### Speaker Notes (Estimated Duration: ~40 seconds)
> *"On Slide 14, we honestly acknowledge our current technical boundaries and outline future research. First, our document parser requires a digital text stream; scanned image-only PDFs are rejected via a 422 error rather than processed through heavy OCR models. Second, initial CPU model loading requires roughly 2 seconds on cold start, although warm inference is sub-30 milliseconds. Third, our canonical taxonomy covers major frameworks, but highly niche proprietary tools rely on dense semantics. Fourth, the system operates as a single-candidate decision-support audit tool rather than a batch ranker, and our benchmarks are synthetic. For future work, we plan to integrate a local OCR engine like Tesseract, connect to public ontologies like ESCO and O*NET, introduce configurable scoring policy sliders for recruiters, conduct consented real-world validation studies, and implement an asynchronous Celery batch processing queue. Now, let us conclude."*

### Demo Transition Cue
* Transition to Slide 15 for the final conclusion and live demo handoff.

---

## Slide 15 — Conclusion & Live Demo Handoff

### Slide Details
* **Slide Number**: 15 / 15
* **Slide Title**: Conclusion & Transition to Live Demonstration
* **Slide Purpose**: Summarize project contributions, invite questions, and hand off smoothly to the live application demonstration.

### Visual Layout & Content
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                            PROJECT CONCLUSION                               │
│                                                                             │
│  • P_101 proves that AI resume screening does NOT require opaque,           │
│    non-deterministic, end-to-end LLM decision-making.                       │
│                                                                             │
│  • Decoupling deterministic rule verification from dense semantic vectors   │
│    guarantees mathematical transparency and eliminates hallucination risks. │
│                                                                             │
│  • Skill gaps are grounded in verbatim candidate evidence, enabling fair    │
│    auditing while leaving hiring decisions with human recruiters.           │
│                                                                             │
│  • Fully validated across 189 regression tests, 6 scoring invariants,      │
│    and an end-to-end median latency of 72.65 milliseconds.                  │
│                                                                             │
│     ───────────────────────────────────────────────────────────────────     │
│                                                                             │
│                                THANK YOU!                                   │
│                                                                             │
│                       Questions & Viva Discussion                           │
│                                    │                                        │
│                                    ▼                                        │
│                     [ Launch Live Application Demo ]                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Technical Points
* Reiterate that P_101 fulfills all project requirements and academic objectives.
* Reiterate core philosophy: Transparent decision support, not automated hiring authority.
* Seamless transition to the live system demonstration.

### Speaker Notes (Estimated Duration: ~25 seconds)
> *"In conclusion, P_101 proves that AI-assisted resume screening does not require opaque, non-deterministic generative models. By decoupling deterministic rule matching, dense vector embeddings, and constrained natural language generation, we achieve rigorous mathematical transparency while eliminating AI hallucinations. Every match and skill gap is grounded in verbatim textual evidence, empowering human recruiters to make informed, fair decisions. With all 189 tests passing and all 6 scoring invariants verified, the system is fully operational. Thank you for your time and attention. I am now delighted to take your questions and transition directly into our live system demonstration."*

### Demo Transition Cue
* Switch browser window to `http://localhost:3000` to begin the 5–6.5 minute live demonstration using the script in `docs/demo.md`.

---

## Technical Viva Q&A Quick Reference

The presenter should keep these concise answers in mind if examiners ask during or immediately after the slide presentation:

| Question / Topic | Authoritative Technical Answer |
| :--- | :--- |
| **Q1: Why not let the LLM score directly?** | Generative LLMs are non-deterministic, opaque, prone to prompt injection, and hallucinate qualifications. In P_101, scoring is governed by a deterministic mathematical engine. The LLM only explains verified facts. |
| **Q2: How is experience double-counting prevented?** | General experience is excluded from Rule Fit and Semantic Fit equations. Experience Fit uses a dedicated quantitative ratio: $\min(\text{candidate\_years} / \text{required\_years}, 1.0)$. |
| **Q3: What if the candidate has MySQL but the job wants PostgreSQL?** | SentenceTransformer awards ~0.55 Semantic Fit (captures relational database context), but the Deterministic Engine strictly marks PostgreSQL as UNMET, flagging "Must-Haves Missing". |
| **Q4: Can this system auto-reject candidates?** | No. P_101 explicitly contains zero automated hiring or rejection verdicts. It is a decision-support audit tool for human recruiters. |
