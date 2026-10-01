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

## 4. Job Description Analysis & Requirement Extraction Pipeline (Phase 4)

Phase 4 introduces the job-description counterpart to resume extraction, transforming unstructured JDs into structured, validated `JobProfile` models:

```text
Job Description (Raw Text or PDF/DOCX Upload)
      ↓
Document Parser (Reuses backend/app/services/document_parser.py for files)
      ↓
Raw JD Text
      ↓
Deterministic JD Rule Extractor (backend/app/services/jd_rule_extractor.py)
      ├── Section Detection (Summary, Responsibilities, Mandatory, Preferred, Education, Experience)
      ├── Keyword Priority Classifier (must_have vs. nice_to_have)
      ├── General vs. Skill-Specific Experience Extractor (years, bounds, skill)
      ├── Education Degree & Field of Study Extractor
      ├── Certification Pattern Matcher (AWS, Azure, GCP, PMP, CISSP, etc.)
      ├── Responsibilities Extractor (clean task isolation)
      └── Other Explicit Requirements (location, work authorization, language, shifts)
      ↓
LLM Extraction Layer (backend/app/ai/llm_client.py + prompts/job_extraction.txt)
      ├── Grounded extraction: extracts only explicit requirements, no hallucinations
      ├── Classifies must-have vs. nice-to-have based on section and phrasing
      └── Categorizes skills using canonical SKILL_TAXONOMY
      ↓
JSON Sanitization & Pydantic Validation (backend/app/ai/validators.py & schemas.py)
      ├── Strips markdown formatting and validates against JobProfile schema
      └── Enforces valid skill categories and requirement types
      ↓
Ground-Truth Reconciliation (backend/app/services/jd_analyzer.py)
      ├── Overrides false must_haves if text contains 'is a plus' / 'preferred'
      ├── Enforces canonical category mapping (e.g. REST APIs -> 'other')
      ├── Guarantees zero degree hallucinations (missing degree remains empty)
      └── Populates synchronized must_have and nice_to_have collections
      ↓
Validated Job Profile (JobProfile)
```

### 4.1 Must-Have vs. Nice-to-Have Classification Strategy
- **Mandatory Requirements (`must_have`)**: Identified when skills, experience, or qualifications appear under sections such as `Requirements`, `Basic Qualifications`, `Minimum Qualifications`, or contain imperative phrasing (`required`, `mandatory`, `must have`, `essential`, `minimum`).
- **Preferred Requirements (`nice_to_have`)**: Identified when requirements appear under `Preferred Qualifications`, `Nice to Have`, `Bonus`, or contain optional phrasing (`is a plus`, `preferred`, `desired`, `bonus points`, `optional`).
- **Explicit Phrasing Override**: An in-line phrase like *"Experience with AWS is a plus"* explicitly forces the priority to `nice_to_have`, even if situated in a general requirements section.

### 4.2 Responsibilities Isolation
- Daily job responsibilities (e.g., *"Design scalable REST APIs"*, *"Mentor junior engineers"*) are captured strictly within the `responsibilities` collection.
- Responsibilities do **not** automatically pollute the `skills` list as mandatory qualifications, keeping task scope cleanly decoupled from applicant prerequisites for downstream matching.

---

## 5. Skill Normalization & Taxonomy Mapping (Phase 5)

Phase 5 introduces a common, canonical representation for both candidate skills and job requirements:

```
                    RESUME                                    JOB
                       │                                       │
                       ▼                                       ▼
                CandidateProfile                           JobProfile
                 (raw skills)                            (raw requirements)
                       │                                       │
                       ▼                                       ▼
              ┌─────────────────┐                     ┌─────────────────┐
              │ Skill Normalizer│                     │ Skill Normalizer│
              │  & Taxonomy     │                     │  & Taxonomy     │
              └─────────────────┘                     └─────────────────┘
                       │                                       │
                       ▼                                       ▼
               Canonical Skills                        Canonical Skills
              (NormalizedSkill)                       (NormalizedJobSkill)
                       │                                       │
                       └───────────────────┬───────────────────┘
                                           │
                                           ▼
                               Future Phase 6: Matching
```

### 5.1 Why Normalization Exists
Raw resumes and job postings frequently describe identical competencies using varying capitalization, acronyms, and formatting:
- Capitalization: `python`, `Python`, `PYTHON` $\rightarrow$ `Python`
- Aliases & Acronyms: `JS`, `js`, `ECMAScript` $\rightarrow$ `JavaScript`; `K8s` $\rightarrow$ `Kubernetes`; `GCP` $\rightarrow$ `Google Cloud`; `Postgres` $\rightarrow$ `PostgreSQL`
- Version Numbers: `Python 3.11`, `Python 3.x` $\rightarrow$ `Python`; `React 18` $\rightarrow$ `React`; `Postgres 14` $\rightarrow$ `PostgreSQL`
- Spaced Punctuation: `c ++` $\rightarrow$ `C++`; `c #` $\rightarrow$ `C#`

Without normalization, downstream matching algorithms either fail to recognize synonyms or generate inaccurate skill-gap penalties.

### 5.2 Canonical Skill Representation
Every normalized skill maintains strict provenance:
```json
{
  "canonical_name": "Python",
  "original_name": "Python 3.11",
  "original_names": ["Python", "python", "Python 3.11"],
  "category": "programming_language",
  "normalization_method": "version_stripped",
  "confidence": 1.0,
  "source": "resume"
}
```

For job descriptions, the requirement attributes are preserved and deduplicated:
```json
{
  "canonical_name": "Python",
  "original_name": "Python",
  "original_names": ["Python", "Python 3"],
  "category": "programming_language",
  "priority": "must_have",
  "minimum_years": 5.0,
  "evidence": "5+ years Python required; Python 3 experience is a plus",
  "normalization_method": "exact",
  "confidence": 1.0,
  "source": "job_description"
}
```

### 5.3 Controlled Taxonomy & Authoritative Categories
Skills are mapped into 10 controlled categories:
`programming_language`, `framework`, `library`, `database`, `tool`, `cloud`, `devops`, `ai_ml`, `soft_skill`, `other`.
- The taxonomy registry (`skill_taxonomy.py`) is authoritative. If an upstream extractor miscategorizes `FastAPI` as `tool` or `Python` as `other`, normalization assigns the verified category (`framework` and `programming_language` respectively).

### 5.4 Deduplication & Precedence Rules
- **Candidate Skills**: Multiple occurrences (`Python`, `python`, `Python 3`) collapse into a single canonical `Python` entry while preserving all variants in `original_names`.
- **Job Requirements**:
  - **Priority Precedence**: If any requirement variant is marked `must_have`, the deduplicated canonical skill is assigned `must_have`.
  - **Experience Precedence**: Maximum required years of experience is preserved (`max(minimum_years)`).
  - **Evidence Aggregation**: Distinct evidence phrases are concatenated with semicolons.

### 5.5 Critical Guardrails (What Phase 5 Does NOT Do)
- **Zero Hallucination for Unknown Skills**: Skills not in the registry are assigned `normalization_method="unknown"`, `category="other"` (or preserved hint category), and retain their clean original name. No LLM hallucination is permitted.
- **Punctuation Sensitivity**: `C++` $\neq$ `C`, `C#` $\neq$ `C`, `.NET` $\neq$ `Node.js`, `Node.js` $\neq$ `Next.js`.
- **False-Positive Filtering**: Generic resume/JD stopwords (`experience`, `work`, `team`, `cloud`, `data`, `model`, `code`) occurring in isolation are prevented from becoming technical skills.
- **Strict Boundary**: Phase 5 performs **no candidate-job matching**, **no similarity calculations**, **no embeddings**, and **no scoring**.

---

## 6. Candidate ↔ Job Requirement Matching Engine (Phase 6)

Phase 6 connects the normalized candidate profile and normalized job description requirements into a transparent, deterministic matching layer:

```text
Normalized Candidate Profile               Normalized Job Description
(skills, experience, education,               (skills, experience, education,
 certifications, other)                         certifications, other)
             │                                             │
             └──────────────────────┬──────────────────────┘
                                    │
                                    ▼
                Deterministic Matching Engine (Phase 6)
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
  Skill Matching           Experience Matching        Education Matching
• Canonical Exact          • Interval Union (Tenure)  • Degree Hierarchy
• Alias Normalized         • Overlap Deduplication    • Field Compatibility
• Version Compatible       • Skill-Specific Tenure    • Partial vs Matched
• Explicit Tenure Check      Verification             
         │                          │                          │
         └──────────────────────────┼──────────────────────────┘
                                    │
         ┌──────────────────────────┴──────────────────────────┐
         ▼                                                     ▼
Certification Matching                                Other Requirements
• Canonical / Alias Match                             • Verifiable Criteria
• Priority Preserved                                  • Location / Authorization
                                    │
                                    ▼
                      Structured Match Results
            (SingleRequirementMatch array + MatchingSummary)
            • Status: matched | partial | unmatched | not_evaluable
            • Method: canonical_exact | alias_normalized | ...
            • Priorities Preserved: must_have vs nice_to_have
            • Verifiable Resume & JD Text Citations
            • ZERO SCORES / PERCENTAGES / RANKINGS / LLM CALLS
```

### 6.1 Strict Scope & Architectural Guardrails
1. **100% Deterministic Execution**:
   - Zero LLM calls or generative re-interpretation.
   - Zero dense vector embeddings or cosine similarity calculations (reserved for Phase 7).
   - Zero string distance / fuzzy-matching thresholds (synonyms must resolve via the Phase 5 authoritative taxonomy).
2. **Explicit Prohibition of Premature Scoring**:
   - Phase 6 intentionally computes **no overall match score**, **no percentage**, **no ranking**, and **no hiring/shortlisting recommendation**.
   - Output contains only granular requirement evaluations and counts of satisfied/unsatisfied requirements within `MatchingSummary`.
3. **No Overclaiming / Conservative Verification**:
   - If a candidate lists a skill in their skills section but the duration of usage cannot be determined from dated work experience roles, skill-specific tenure requirements are marked `not_evaluable`, never assumed to equal total career tenure.
   - General experience is evaluated using the union of non-overlapping role date intervals, preventing double-counting of concurrent positions.

### 6.2 Match Status Taxonomy
Every requirement evaluated by the engine is assigned one of four mutually exclusive statuses:
- `matched`: The requirement is fully satisfied according to the candidate's explicit profile evidence.
- `partial`: The candidate partially satisfies the requirement (e.g. holds the required degree level but in an adjacent field; or has the required skill but with fewer years than demanded).
- `unmatched`: The candidate profile provides no verifiable evidence of possessing the required skill, credential, or background.
- `not_evaluable`: The candidate profile lacks necessary temporal or contextual details to conclusively determine satisfaction without speculation.

### 6.3 Match Method Taxonomy
Detailed metadata indicating the exact deterministic mechanism that yielded the match:
- `canonical_exact`: Direct match between canonical skill names.
- `alias_normalized`: Match established via taxonomy alias mapping (e.g. `K8s` $\rightarrow$ `Kubernetes`).
- `version_compatible`: Version-qualified match (e.g. `Python 3.11` satisfies `Python`).
- `experience_verified`: General or skill-specific experience duration met or exceeded.
- `experience_insufficient`: Experience detected but verifiable duration falls short.
- `education_match`: Both degree level and field of study meet or exceed requirement.
- `education_partial`: Degree level is satisfied, but field is adjacent or unspecified.
- `certification_match`: Recognized industry certification explicitly verified.
- `text_evidence`: Direct textual evidence extracted from candidate profile.
- `unmatched`: No qualifying evidence found.
- `not_evaluable`: Insufficient data to evaluate requirement rigorously.

### 6.4 Non-Overlapping Experience Interval Union
To evaluate total career experience without bias from moonlighting, concurrent consulting, or multiple part-time roles:
1. All dated work experiences are converted to decimal year floats (e.g., `2021-06` $\rightarrow$ `2021.417`).
2. Current roles (`is_current=True` or `end_date="Present"`) default to the current calendar date.
3. Date intervals $[S_i, E_i]$ are sorted by start date and merged into disjoint intervals:
   $$\text{Intervals}_{\text{merged}} = \bigcup [S_i, E_i]$$
4. Total tenure is computed as the sum of disjoint durations:
   $$\text{Total Years} = \sum (E_k - S_k)$$
This guarantees that a candidate working two concurrent positions from 2021 to 2023 is credited with 2.0 years of experience, not 4.0 years.

### 6.5 Education Hierarchy & Field Compatibility
Education requirements are evaluated against a 6-tier academic hierarchy:
$$\text{High School (1)} < \text{Associate (2)} < \text{Bachelor's (3)} < \text{Master's (4)} < \text{Doctorate (5)}$$
- **Degree Level Check**: Candidate must hold a degree with level $\ge$ required degree level.
- **Field Compatibility**: If the JD specifies a technical field (e.g. `Computer Science`), candidates with degrees in `Software Engineering`, `Information Technology`, `Data Science`, or `Electrical Engineering` are recognized as compatible fields.
- **Partial Degree Match**: If the candidate holds a Master's degree but in `Mechanical Engineering` for a Software role requiring a `Bachelor's in CS`, the status is categorized as `partial` with method `education_partial`.

---

## 7. Semantic Matching & Embedding Layer (Phase 7)

Phase 7 introduces a dense semantic representation layer to discover conceptually related skills and contextual evidence that cannot be captured by strict taxonomy aliases alone.

### 7.1 Objective & Decoupled Architectural Role
The semantic matching layer strictly adheres to the principle of **interpretability and decision-support**:
- **Semantic Signal Only**: It answers *"How semantically related is this candidate evidence to this job requirement?"*, NOT *"How good is this candidate overall?"*
- **No Overriding Authority**: Semantic matching **never** overrides Phase 6 deterministic matches (`canonical_exact`, `alias_normalized`, `version_compatible`, `education_match`). If a requirement is already verified deterministically, semantic matching confirms and enriches evidence rather than conflicting with it.
- **Conservative Guardrails**: Semantic matching never synthesizes years of experience and never alters degree hierarchy.
- **Zero Scores / Percentages / Rankings**: Outputs requirement-level similarity records (`similarity_score`, `semantic_status`, `confidence`, `explanation`) without aggregating into 0–100 scores or shortlists (reserved for Phase 8).

```text
RESUME PIPELINE
CandidateProfile ──→ Skill Normalization ──→ Canonical Skills
                                                  │
                                                  ▼
JOB PIPELINE                            Phase 6 Deterministic Match
JobProfile ─────────→ Skill Normalization ──→ Canonical Requirements
                                                  │
                                                  ▼
                                        Phase 7 Semantic Match
                                   (SentenceTransformers / Cosine)
                                                  │
                                                  ▼
                                       Enriched Match Evidence
                                   (Deterministic + Semantic)
                                                  │
                                                  ▼
                                      Future Phase 8 Fusion Scoring
```

### 7.2 Model Architecture & Vector Representation
- **Model**: `all-MiniLM-L6-v2` via `sentence-transformers`.
- **Dimensions**: 384-dimensional dense real-valued vector space.
- **Vector Normalization**: All embeddings are normalized to unit Euclidean length ($\|v\|_2 = 1.0$), transforming cosine similarity into a high-speed dot product:
  $$\text{Cosine Similarity}(u, v) = \frac{u \cdot v}{\|u\|_2 \|v\|_2} = u \cdot v$$
- **Hardware Profile**: CPU-first default execution. Lazy model initialization ensures test suites and application startup remain fast and lightweight, with zero external vector database dependencies (no FAISS, Chroma, Pinecone).

### 7.3 Semantic Evidence Item Extraction
To compare candidate background against requirements systematically:
1. **Candidate Evidence Items**:
   - Explicit normalized skills (with category context, e.g., `"Python (programming_language)"`).
   - Work experience roles (e.g., `"Senior Backend Engineer at CloudCorp: Led microservices architecture using FastAPI"`).
   - Project descriptions (e.g., `"Project E-Commerce API: Built high-throughput payment pipelines"`).
   - Candidate summary statement.
2. **Job Requirement Items**:
   - Canonical skill requirements (e.g., `"PostgreSQL: 3+ years experience with relational databases"`).
   - Experience scope requirements (e.g., `"5+ years of software engineering experience"`).
   - Education degree and discipline requirements.

### 7.4 Semantic Classification & Thresholds
For each job requirement, the semantic matcher calculates cosine similarities against candidate evidence items and assigns a status based on calibrated thresholds:

$$\text{Semantic Status} = \begin{cases} 
\text{semantic\_match} & \text{if } \text{similarity} \ge 0.75 \text{ (confidence: high)} \\
\text{semantic\_partial} & \text{if } 0.55 \le \text{similarity} < 0.75 \text{ (confidence: medium)} \\
\text{semantic\_unrelated} & \text{if } \text{similarity} < 0.55 \text{ (confidence: low)} \\
\text{semantic\_not\_evaluable} & \text{if candidate evidence is empty or missing}
\end{cases}$$

### 7.5 False-Positive Protection Matrix
Because embedding models can exhibit misleadingly high similarity for syntactically similar or co-occurring programming languages and cloud tools, a strict domain protection barrier is enforced:

| Requirement | Disallowed / Incompatible Candidate Item | Rationale |
|---|---|---|
| `Java` | `JavaScript`, `TypeScript` | Distinct runtimes, language families, and paradigms |
| `JavaScript` | `Java` | Scripting web runtime vs JVM enterprise language |
| `C` | `C++`, `C#` | Procedural systems language vs OOP/managed platforms |
| `C++` | `C`, `C#` | Distinct object models, runtimes, and ecosystems |
| `C#` | `C`, `C++` | .NET managed framework language vs unmanaged systems languages |
| `Python` | `PyTorch` | General-purpose programming language vs ML framework |
| `React` | `React Native` | Web DOM library vs mobile cross-platform runtime |
| `AWS` | `AWS Lambda` | Broad cloud platform vs specific serverless compute primitive |

Whenever a protected incompatibility pair is detected, the similarity score is capped at `0.0` and classified as `semantic_unrelated` to prevent false positive matches.

### 7.6 In-Memory Caching & Performance
- **Deterministic SHA-256 Cache**: An in-memory cache keyed by string SHA-256 hashes caches normalized embeddings.
- Repeated skill tokens across multiple resumes or candidate-requirement comparisons achieve near $O(1)$ lookup latency, eliminating redundant forward passes on the transformer model.

---

## 8. Multi-Layer Hybrid Fusion Scoring Engine (Phase 8)

Phase 8 combines deterministic requirement evaluations from Phase 6, semantic similarity signals from Phase 7, verifiable experience tenure, and optional LLM fit into an explainable, calibrated **Candidate Fit Score**.

### 8.1 Architectural Pipeline & Separation of Concerns
In strict compliance with decision-support principles:
- **Decision-Support Signal Only**: Computes an analytical candidate-fit score in $[0.0, 1.0]$ for recruiter inspection; does **not** make hiring decisions, rank candidates, shortlist, or auto-reject.
- **Zero Ranking Immediately After Scoring**: Scoring strictly evaluates individual candidate-job alignment. Ranking, comparative leaderboards, and Top-N selection are deferred to later phases.
- **Separate Safety Signals**: Hard constraints (e.g. `all_must_haves_satisfied`) are tracked independently and never artificially suppressed by high aggregate scores.

```text
                  Candidate + Job
                       │
          ┌────────────┴────────────┐
          ↓                         ↓
   Deterministic                Semantic
    Matching                    Matching
    Phase 6                     Phase 7
          │                         │
          └────────────┬────────────┘
                       ↓
                Hybrid Scoring
                   Phase 8
                       │
       ┌───────────────┼────────────────┐
       ↓               ↓                ↓
    Rule Fit      Semantic Fit     Experience Fit
       │               │                │
       └───────────────┼────────────────┘
                       ↓
                 LLM Fit (optional)
                       ↓
                Weighted Fusion
                       ↓
             Candidate Fit Score
                       │
                       ↓
             Phase 9 / Explainability
```

### 8.2 Four Scoring Components

Every component score is strictly normalized to the range $[0.0, 1.0]$:

```text
Rule Fit       → Deterministic non-experience requirements (skills, education, certifications, other)
Semantic Fit   → Dense vector semantic similarity (all-MiniLM-L6-v2)
Experience Fit → Career tenure / required years proportionality
LLM Fit        → Optional qualitative assessment (disabled by default)
```

1. **Rule Fit ($S_{\text{rule}}$)**:
   - Evaluates evaluable **non-experience deterministic requirements** (skills, education, certifications, and other constraints) from Phase 6. Experience requirements are intentionally excluded from Rule Fit because career tenure is represented separately and proportionally by the Experience Fit component.
   - Explicit partition:
     - $\mathcal{R}_{\text{rule}}$: Set of evaluable non-experience requirements.
     - $\mathcal{R}_{\text{exp}}$: Set of experience requirements (handled exclusively by Experience Fit).
   - Priority-aware weighting: `must_have` requirements carry weight $1.0$, whereas `nice_to_have` requirements carry weight $0.5$.
   - Status mapping:
     - `matched`: $1.0$
     - `partial`: $0.5$
     - `unmatched`: $0.0$
     - `not_evaluable`: **Excluded from denominator** under default policy (`exclude`), preventing missing candidate evidence from being penalized as failure.
   - Formula (over $\mathcal{R}_{\text{rule}}$ only):
     $$S_{\text{rule}} = \frac{\sum_{r \in \mathcal{R}_{\text{rule}}} (\text{status\_value}_r \times \text{priority\_weight}_r)}{\sum_{r \in \mathcal{R}_{\text{rule}}} \text{priority\_weight}_r}$$
   - If $\mathcal{R}_{\text{rule}} = \emptyset$ (e.g. a job posting specifying only tenure requirements), Rule Fit is marked `available = False` ($S_{\text{rule}} = \text{None}$) and its weight is dynamically renormalized to prevent an experience requirement alone from artificially producing a Rule Fit score.

2. **Semantic Fit ($S_{\text{semantic}}$)**:
   - Aggregates raw cosine similarities from Phase 7 for **non-experience requirements** ($\mathcal{R}_{\text{rule}}$ semantic items: skills, education, certifications, and explicit domain knowledge).
   - **Exclusion of Experience Requirements (Phase 8.2)**: Career experience and role tenure items (`category == "experience"` or `requirement_id` starting with `exp_`) are strictly excluded from the numerical Semantic Fit calculation. This prevents double-counting, ensuring career tenure is evaluated exclusively through the quantitative Experience Fit component.
   - **Diagnostic Evidence Preserved**: While excluded from the numerical score fusion, all Phase 7 semantic match results for experience requirements remain fully intact within `SingleRequirementMatch.semantic_result` and `CandidateJobMatchResponse.semantic_matches` for recruiter inspection and qualitative explainability.
   - Continuous similarity scores $\in [0.0, 1.0]$ rather than binary categories.
   - Priority-weighted across semantically evaluable non-experience requirements (`must_have` $1.0$, `nice_to_have` $0.5$):
     $$S_{\text{semantic}} = \frac{\sum_{r \in \mathcal{R}_{\text{rule, sem}}} (\text{similarity}_r \times \text{priority\_weight}_r)}{\sum_{r \in \mathcal{R}_{\text{rule, sem}}} \text{priority\_weight}_r}$$
   - Respects false-positive protection matrix (forced $0.0$ similarity for incompatible domains such as Java vs JavaScript).
   - If semantic matching is disabled, candidate provides no evaluable text, or the job contains only experience requirements ($\mathcal{R}_{\text{rule, sem}} = \emptyset$), Semantic Fit is marked `available = False` ($S_{\text{semantic}} = \text{None}$) and its weight is dynamically renormalized.

3. **Experience Fit ($S_{\text{experience}}$)**:
   - Evaluates verifiable non-overlapping career and skill tenure strictly from Phase 6 evidence over $\mathcal{R}_{\text{exp}}$.
   - Never uses embeddings for temporal duration.
   - Proportional fulfillment for explicit year requirements:
     $$S_{\text{indiv}} = \min\left(1.0, \frac{\text{candidate\_years}}{\text{required\_years}}\right)$$
   - Excess experience above requirement is capped at $1.0$ (no over-rewarding).
   - `not_evaluable` experience requirements (e.g. skills listed without dated role tenure) are strictly excluded from the experience denominator.

4. **LLM-Supported Fit ($S_{\text{llm}}$)**:
   - Interface for qualitative LLM reasoning.
   - By default in Phase 8, execution remains 100% deterministic (`available = False`, `score = None`), and its weight is dynamically redistributed.
   - Can consume explicit external scores when provided without fabricating values.

### 8.3 Configurable Weights & Validation
Default prototype weights:
- Rule Fit: $w_{\text{rule}} = 0.30$
- Semantic Fit: $w_{\text{semantic}} = 0.40$
- Experience Fit: $w_{\text{experience}} = 0.20$
- LLM Fit: $w_{\text{llm}} = 0.10$

**Strict Validation**:
- Every weight must be non-negative: $w_k \ge 0.0$.
- Weights must sum to $1.0$ within floating-point tolerance: $|\sum w_k - 1.0| \le 1\times 10^{-4}$.
- Invalid weights are explicitly rejected with HTTP 422 / `ValueError` rather than silently altered.

### 8.4 Dynamic Weight Renormalization
When any scoring component is unavailable (e.g., LLM fit disabled by default, or semantic matching disabled), available weights are dynamically renormalized:

$$W_A = \sum_{k \in \text{available}} w_k$$
$$w'_k = \frac{w_k}{W_A} \quad (\text{for } k \in \text{available}), \qquad w'_k = 0.0 \quad (\text{for } k \notin \text{available})$$

**Overall Candidate Fit Score**:
$$\text{candidate\_fit\_score} = \sum_{k \in \text{available}} (S_k \times w'_k)$$

The system flags `weights_renormalized: true` and exposes both `configured_weight` and `effective_weight` for complete auditability.

---

## 9. Database Schema Overview
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

## 10. Privacy & Masked Mode
- Recruiter can toggle `masked_mode`.
- When enabled, names, gender indicators, photographs, institutions, and contact details are redacted before scoring to mitigate cognitive bias.

---

## 11. Phase 9: Skill-Gap Analysis & Evidence Grounding

Phase 9 implements an evidence-grounded skill-gap analysis service that answers: *"Which job skills are not adequately demonstrated by this candidate, and what evidence supports that conclusion?"*

```text
Candidate Profile                  Job Profile
       │                                │
       ▼                                ▼
Phase 5 Skill Normalization      Phase 5 Skill Normalization
       │                                │
       ├────────────────────────────────┤
       │                                │
       ▼                                ▼
Phase 6 Deterministic Match      Phase 7 Semantic Match
       │                                │
       └────────────────┬───────────────┘
                        │
                        ▼
       Phase 9: SKILL-GAP ANALYZER
                        │
        ┌───────────────┴───────────────┐
        ▼                               ▼
Canonical Skill Gaps           Experience Gaps
(Evidence-Grounded)            (Career Tenure)
        │                               │
        └───────────────┬───────────────┘
                        ▼
             Skill Gap Summary
         (Auditable Counts & Breakdown)
```

### 11.1 Discrete Skill Gap Statuses
Every job skill requirement is classified into exactly one of four discrete statuses:
1. `satisfied`: Candidate demonstrates verifiable exact, alias, or version-compatible match satisfying all criteria (including any skill-specific tenure).
2. `missing`: Candidate profile contains no matching skill evidence whatsoever.
3. `insufficient`: Candidate demonstrates the skill, but verifiable duration falls short of the required tenure (e.g. 1.0 year demonstrated vs 3.0 years required).
4. `not_evaluable`: Candidate mentions or demonstrates the skill, but tenure cannot be verified from dated work history, or evidence is ambiguous.

### 11.2 Deterministic-First Authority (Rule 6)
- **Authoritative Deterministic Ground Truth**: Phase 6 deterministic matching outcomes are strictly authoritative.
- **No Semantic Override**: A deterministic `unmatched` status can **never** be upgraded to `satisfied` or `partial` by semantic similarity, regardless of how high the cosine similarity is. For example, if a job requires `PostgreSQL` and the candidate only has `MySQL`, the deterministic match is `unmatched`, and Phase 9 classifies the requirement strictly as `missing`.
- **Supporting Semantic Evidence**: High semantic similarity is recorded purely as diagnostic/contextual information within `semantic_evidence` and `explanation` (e.g., *"Supporting semantic evidence: Conceptually related candidate evidence 'MySQL (database)' (cosine similarity: 0.68) was detected, but cannot substitute for required skill."*), enabling recruiters to understand candidate adjacency without compromising skill rigor.

### 11.3 Quantitative Shortfall Calculation
For `insufficient` skills with tenure deficits:
$$\text{shortfall} = \max(0.0, \text{required\_years} - \text{candidate\_years})$$
- Calculated using verifiable non-overlapping calendar intervals from dated work experiences.
- Formatted with explicit units (e.g. `required_value: "3.0 years"`, `candidate_value: "1.0 years"`, `shortfall: "2.0 years"`).

### 11.4 Career Experience vs Skill Separation
General career tenure requirements (e.g., "5+ years of software engineering experience", "3+ years of backend development") are evaluated strictly in `experience_gaps` as `ExperienceGapItem` records. They are **never** converted into artificial technical skill requirements like "backend", preserving a clean separation of concerns.

### 11.5 Canonical Grouping and Alias Deduplication
When a job description mentions the same underlying canonical skill under multiple aliases (e.g., "JS" in the overview and "JavaScript" in requirements):
- The analyzer groups them under the canonical taxonomy name (`JavaScript`).
- Resolves conflicts using `must_have` priority precedence (`must_have` overrides `nice_to_have`).
- Retains the maximum required experience duration.
- Consolidates candidate and job evidence citations into a single, cohesive `SkillGapItem`.

### 11.6 Summary Arithmetic & Integrity Invariants
The `SkillGapSummary` provides exact, auditable accounting:
$$\text{total\_skill\_requirements} = \text{satisfied\_count} + \text{missing\_count} + \text{insufficient\_count} + \text{not\_evaluable\_count}$$
$$\text{must\_have\_gaps} = \text{missing}(\text{must\_have}) + \text{insufficient}(\text{must\_have})$$
- Per Section 11 requirements, `not_evaluable` indicates incomplete/unverified information and is **never** counted as a confirmed gap in `must_have_gaps`.
- `must_have_satisfied` counts verified `must_have` skills with status `satisfied`.

### 11.7 Strict Decision-Support Guardrails
Phase 9 operates strictly as an objective, evidence-grounded decision-support system:
- **Zero Candidate Rankings**: No `rank`, `rank_order`, or sorting across candidates.
- **Zero Shortlists or Top-N Cuts**: No automated selection, filtering, or tiering.
- **Zero Automated Hiring Decisions**: No `hire`, `reject`, `pass`, or `fail` classifications.
- **Zero Learning Recommendations**: No courses, training roadmaps, or interview questions (reserved for future phases).

---

## 12. Phase 10: LLM Explanations & Personalized Recommendations

Phase 10 introduces an **evidence-grounded explanation and personalized recommendation layer**.

```text
Phase 6 Deterministic Matching
             │
Phase 7 Semantic Evidence
             │
Phase 8 Hybrid Score
             │
Phase 9 Skill Gaps
             │
             ▼
      Phase 10 LLM Layer
             │
       ┌─────┴─────┐
       ▼           ▼
  Explanation   Recommendations
```

### 12.1 Critical Separation Principle
The LLM is strictly an **explanation and recommendation layer**:
- It is **NOT** an authority over:
  - deterministic matching
  - semantic matching
  - experience calculations
  - hybrid scoring
  - skill-gap classification
  - requirement priority
  - candidate ranking
  - hiring decisions
- The LLM **never** modifies or recalculates underlying structured facts or numerical scores.
- It consumes structured evidence previously computed by Phases 6–9 and translates them into transparent narrative explanations and targeted recommendations.

### 12.2 Mandatory Grounding & Anti-Hallucination Safeguards
1. **Rule 1 — No Fabricated Evidence**: The LLM cannot claim a skill or credential exists unless present in structured candidate evidence.
2. **Rule 2 — No Fabricated Experience**: Do not invent years, employers, projects, degrees, or certifications.
3. **Rule 3 — No Score Manipulation**: Numerical fit scores ($S_{\text{rule}}$, $S_{\text{semantic}}$, $S_{\text{experience}}$, $S_{\text{fit}}$) are preserved verbatim.
4. **Rule 4 — No Requirement Manipulation**: Requirements cannot be reinterpreted to alter candidate suitability.
5. **Rule 5 — Explicit Uncertainty**: Unverified evidence is explicitly labeled as not evaluable rather than guessed.
6. **Rule 6 — Semantic Invariance**: Conceptually related skills (e.g. MySQL for PostgreSQL) are explained as supporting context only; deterministic missing status is strictly maintained.

### 12.3 Personalized Recommendation Logic
Recommendations are generated **only** from actual Phase 9 gaps (status `missing`, `insufficient`, or `not_evaluable`):
- Each recommendation links directly to its source gap (`skill`, `gap_status`, `priority`).
- Explains the root cause (`reason`).
- Suggests concrete, actionable learning or project workflows (`recommendation`).
- Specifies verifiable artifacts (`evidence_to_build`, e.g. GitHub repositories, deployment manifests, benchmark logs).
- Technologies not identified as gaps in Phase 9 are never introduced.

### 12.4 LLM Explanation vs. Numerical LLM Fit Scoring
Phase 10 strictly separates LLM explanation from the Phase 8 `llm_fit` numerical score component:
- Generating an explanation does **not** fabricate an `llm_fit` score.
- If `llm_fit` was unavailable in Phase 8 (`score = None`), it remains unavailable and its weight stays renormalized.
- Explanation is a qualitative narrative audit trail; scoring is a quantitative evaluation.

### 12.5 Failure Handling & Offline Execution
- The screening pipeline degrades gracefully if the LLM provider is unavailable: Phases 1–9 execute deterministically without dependency on LLM connectivity.
- Offline and CI/CD testing utilize `MockLLMClient`, providing 100% deterministic, reproducible explanations without requiring external API keys.

---

## 13. Phase 11: Frontend Web Dashboard

Phase 11 introduces a modern, accessible web interface for recruiters and hiring managers to interact with the P_101 screening system.

```text
                    FRONTEND (Next.js + TypeScript + Tailwind)
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         ▼                            ▼                            ▼
    Job Setup                   Resume Upload              Analysis Workspace
  (/jobs/new)                     (/analysis)                  (/analysis)
         │                            │                            │
         └────────────────────────────┼────────────────────────────┘
                                      ▼
                        FASTAPI BACKEND (/api/v1)
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         ▼                            ▼                            ▼
    Deterministic                 Semantic                   Multi-Layer
       Matching                   Matching                     Scoring
      (Phase 6)                  (Phase 7)                    (Phase 8)
         │                            │                            │
         └────────────────────────────┼────────────────────────────┘
                                      ▼
                        Skill-Gap & Evidence Engine
                                 (Phase 9)
                                      │
                                      ▼
                       LLM Explanations & Recommendations
                                 (Phase 10)
```

### 13.1 Core Principles
1. **Decision-Support Dashboard**: The web UI serves strictly to empower human decision-makers. It contains zero automated hiring actions (`Hire`, `Reject`, `Shortlist`).
2. **Deterministic-First Presentation**: System-calculated scores, deterministic requirement coverage, and evidence snippets are displayed verbatim without client-side recalculation.
3. **Clear Provenance Distinction**: System facts and metrics are visually distinguished from AI-generated narrative explanations and recommendations.
4. **Mandatory Recruiter Oversight**: The human-review disclaimer is prominently and permanently rendered across all evaluation views.
5. **Single-Candidate Deep Dive**: Reflecting Phases 1–10, the dashboard evaluates single candidate fit against a job, strictly avoiding leaderboard rankings or candidate tiering.

### 13.2 Frontend Architecture & Directory Layout
```text
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx                     # System telemetry, recent screenings, workflow guide
│   │   ├── layout.tsx                   # App shell, fonts, metadata
│   │   ├── globals.css                  # Tailwind styles & semantic variables
│   │   ├── jobs/
│   │   │   ├── page.tsx                 # Active job overview and management
│   │   │   └── new/page.tsx             # Job setup (upload JD document or paste text)
│   │   ├── analysis/
│   │   │   └── page.tsx                 # Core candidate evaluation and audit workspace
│   │   └── candidates/
│   │       ├── page.tsx                 # Candidates entry view
│   │       └── [id]/page.tsx            # Dynamic candidate record view
│   ├── components/
│   │   ├── layout/                      # Header, Sidebar, AppShell
│   │   ├── score/                       # OverallScoreBadge, ScoreBreakdownCard, ScoreExplanationPanel
│   │   ├── requirements/                # RequirementCoverageTable, status indicators
│   │   ├── skill-gaps/                  # SkillGapSection, SkillGapCard, ExperienceGapCard
│   │   ├── explanation/                 # LLMExplanationView, RecommendationCard
│   │   └── ui/                          # Button, Card, Badge, Alert
│   ├── lib/
│   │   └── api/
│   │       └── client.ts                # Centralized typed API client
│   └── types/
│       └── api.ts                       # Strongly-typed interfaces mirroring backend Pydantic models
├── vitest.config.ts                     # Vitest testing configuration
└── package.json                         # Next.js 16, React 19, Tailwind CSS v4, Lucide icons
```

### 13.3 API Client Integration
The frontend interfaces with the backend exclusively via `frontend/src/lib/api/client.ts`:
- Configured with `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`).
- Provides strongly-typed async methods matching FastAPI routes:
  - `checkHealth()`: `GET /api/v1/health`
  - `analyzeJobText()`, `analyzeJobFile()`: `POST /api/v1/jobs/analyze`, `POST /api/v1/jobs/analyze/upload`
  - `parseResume()`, `extractResume()`: `POST /api/v1/resumes/parse`, `POST /api/v1/resumes/extract`
  - `matchFromFiles()`, `matchAndAnalyze()`: `POST /api/v1/matching/from-files`, `POST /api/v1/matching/analyze`
  - `explanationFromFiles()`, `analyzeExplanation()`: `POST /api/v1/explanations/from-files`, `POST /api/v1/explanations/analyze`
- Standardized error handling extracting HTTP error details (`detail` field) and converting them into user-friendly messages.



