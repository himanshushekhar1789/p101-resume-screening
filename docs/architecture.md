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

## 8. Hybrid AI Engine Layers (Future Phases)

The screening pipeline intentionally rejects purely black-box LLM screening or purely naive keyword matching. It employs a 5-layer architecture:

### Layer 1: Rule Engine (Objective Criteria)
- Evaluates non-negotiable hard requirements: mandatory skills, minimum degree level, minimum years of experience, work authorizations.
- Produces `rule_score` (0–100) and qualification flags.

### Layer 2: NLP & Semantic Embedding Layer (Phase 7 Implemented)
- Dense semantic vector embeddings (Sentence Transformers / `all-MiniLM-L6-v2`) + cosine similarity for contextual match beyond raw strings.
- Produces `semantic_score` (0–100 in Phase 8).

### Layer 3: Experience & Project Alignment Layer
- Evaluates duration, seniority depth, and relevant project experience against JD scope.
- Produces `experience_score` (0–100 in Phase 8).

### Layer 4: LLM Explanation & Verification Layer
- Provider abstraction (`backend/app/ai/llm_client.py`) supporting Gemini, OpenAI, or local/mock runners.
- Structured JSON outputs verified against strict Pydantic schemas.
- Extracts citation evidence directly from resume text.
- Generates context-specific learning roadmaps for detected skill gaps.
- Produces `llm_score` (0–100 in Phase 8).

### Layer 5: Fusion Scoring
- Total Candidate Score = $W_{rule} \cdot S_{rule} + W_{semantic} \cdot S_{semantic} + W_{exp} \cdot S_{exp} + W_{llm} \cdot S_{llm}$
- Default configurable weights: 30% Rule Fit, 40% Semantic Skill Fit, 20% Experience Fit, 10% LLM Fit.
- Every score is stored and presented with its sub-score breakdown.

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
