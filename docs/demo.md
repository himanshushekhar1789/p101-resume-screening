# P_101 — End-to-End System Demonstration Guide

This guide provides a comprehensive, repeatable, and verified **5–7 minute live demonstration script** for **P_101: LLM-Based Resume Screening System**.

Designed specifically for college project viva, evaluation committees, and technical recruiter walkthroughs, this guide walks through the exact operational steps, timing, UI panels, talking points, and safety fallbacks.

---

## 1. Demonstration Overview & Core Philosophy

### System Purpose
P_101 is an **AI-assisted recruiter decision-support system**, not an automated hiring/rejection bot. It bridges the gap between opaque "black-box" LLM scoring and brittle keyword matchers.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                           P_101 CORE ARCHITECTURE                           │
├──────────────────────────┬───────────────────────────┬──────────────────────┤
│ 1. Deterministic Engine  │ 2. Semantic Search Engine │ 3. LLM Copilot       │
│    (Authoritative)       │    (Supporting Evidence)  │    (Explanation Only)│
├──────────────────────────┼───────────────────────────┼──────────────────────┤
│ Exact skill alias graph  │ SentenceTransformer       │ Structured prompt    │
│ Strict tenure calculation│ all-MiniLM-L6-v2          │ Grounded citations   │
│ Must-have gating         │ Contextual similarity     │ Actionable gap advice│
│ 100% reproducible        │ Nuanced tech alignment    │ ZERO scoring power   │
└──────────────────────────┴───────────────────────────┴──────────────────────┘
```

### Key Demonstration Invariants
1. **Deterministic Authority**: Hard requirements (must-haves) are enforced mathematically. An LLM cannot hallucinate qualification.
2. **Separation of Concerns**: Skills, semantic proximity, and years of experience are computed independently—no double-counting.
3. **Evidence Grounding**: Every check, score, and gap statement is tied directly to verbatim snippets from the candidate's resume.
4. **Human-in-the-Loop**: The UI explicitly disclaims automated decision-making and provides an audit trail for recruiter judgment.

---

## 2. Prerequisites & Environment Setup

The system is configured to run **100% offline and locally** with zero external paid APIs, cloud keys, or internet connection required.

### System Requirements
* Python 3.11+ (in project virtual environment `.venv`)
* Node.js 18+ and npm
* Operating System: Windows, macOS, or Linux
* RAM: 4 GB minimum (8 GB recommended for local embedding model)

### Pre-Flight Verification Commands
Open two separate terminal windows in the project root: `C:\Users\himan\.gemini\antigravity\scratch\p101-resume-screening`

#### Terminal 1 — Backend (FastAPI on Port 8000)
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Verify environment variables
$env:LLM_PROVIDER = "mock"
$env:PORT = "8000"

# Start FastAPI server with live reload
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Expected log output:*
```text
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

#### Terminal 2 — Frontend (Next.js on Port 3000)
```powershell
# Navigate to frontend directory
cd frontend

# Verify .env.local contains NEXT_PUBLIC_API_URL=http://localhost:8000
# Start Next.js development server
npm run dev
```
*Expected log output:*
```text
   ▲ Next.js 16.3.8 (Turbopack)
   - Local:        http://localhost:3000
   - Environments: .env.local
 ✓ Starting...
 ✓ Ready in 1200ms
```

#### Terminal 3 — Quick Health Check
```powershell
curl http://127.0.0.1:8000/api/v1/health
```
*Expected response:*
```json
{"status":"healthy","version":"1.0.0","environment":"development"}
```

---

## 3. Demo Dataset Reference

The demo utilizes synthetic, privacy-safe, reproducible evaluation documents located in the repository:

| Asset Name | Relative Path | Candidate / Role Summary | Intended Outcome |
| :--- | :--- | :--- | :--- |
| **Job Description** | `evaluation/jobs/01_backend_engineer.pdf` (or `.txt`) | Senior Backend Engineer (Python, FastAPI, PostgreSQL, Redis, Docker, 5+ yrs) | Baseline Job Requirements |
| **Candidate A** | `evaluation/resumes/01_strong_backend.pdf` | **Alex Morgan**: 6.2 yrs exp, FastAPI, PostgreSQL, Redis, Docker, AWS | **Strong Match (84.1%)**; All Must-Haves Met |
| **Candidate B** | `evaluation/resumes/02_weak_backend.pdf` | **Brian Miller**: 0.6 yrs exp, Basic Python, HTML, CSS | **Weak Match (25.2%)**; Must-Have Failure; Tenure Deficit |
| **Candidate C** | `evaluation/resumes/08_related_skills_candidate.pdf` | **Hector Vance**: 3.0 yrs exp, Flask, MySQL, Celery, Docker | **Semantic Contrast (52.1%)**; Proximity != Exact Requirement |

*(Note: Both `.pdf` and `.txt` versions exist. The recruiter web UI accepts `.pdf` and `.docx` for resumes, and `.pdf`, `.docx`, or `.txt` for job descriptions).*

---

## 4. 5–7 Minute Step-by-Step Live Demo Script

```text
TIMELINE BREAKDOWN:
00:00 - 00:45 | Introduction & Recruiter Dashboard
00:45 - 01:30 | Step 1: Job Description Parsing & Requirement Extraction
01:30 - 03:00 | Step 2: Candidate A (Alex Morgan) — Strong Match & Evidence Grounding
03:00 - 04:15 | Step 3: Candidate B (Brian Miller) — Strict Gatekeeping & Experience Deficit
04:15 - 05:30 | Step 4: Candidate C (Hector Vance) — Semantic Proximity vs Hard Rules
05:30 - 06:30 | Step 5: Recruiter Review, Explainability & Ethical AI Guardrails
```

---

### Step 0: Introduction & Overview (0:00 – 0:45)
1. **Navigate to:** `http://localhost:3000`
2. **Screen displayed:** Recruiter Overview Dashboard (`/`).
3. **What to point out:**
   * "Welcome. This is P_101, an LLM-assisted resume screening and candidate qualification engine."
   * Point to the **System Architecture summary** on the landing page:
     - *Deterministic matching* guarantees compliance with core hard requirements.
     - *Local embedding models* evaluate conceptual contextual relevance.
     - *LLMs* provide grounded explanations and skill-gap recommendations.
     - *Human recruiter* retains sole decision authority.
4. **Presenter Talking Point:**
   > *"Traditional resume screeners suffer from two extremes: keyword matchers fail on synonyms, while generative LLMs hallucinate qualifications and rank resumes opaquely. P_101 solves this by decoupling rule evaluation from language modeling. The LLM only explains what the deterministic engine proved."*

---

### Step 1: Ingest Job Description & Requirement Extraction (0:45 – 1:30)
1. **Click on:** Top navigation link **"Job Setup"** (`/jobs/new`).
2. **Action:**
   * In the **Job Title** field, enter: `Senior Backend Engineer`
   * Select **"Upload JD File"** tab (or drag-and-drop `evaluation/jobs/01_backend_engineer.pdf`).
   * Click **"Analyze Job Description"**.
3. **What happens under the hood:**
   * The backend parses the document using PyMuPDF / python-docx.
   * The JD analyzer extracts structured requirements:
     - **Must-Have Skills**: Python, FastAPI, PostgreSQL, Docker, Redis.
     - **Experience Requirement**: 5.0 years minimum backend experience.
     - **Education**: Bachelor's in Computer Science or related.
     - **Nice-to-Have Skills**: Kubernetes, AWS, CI/CD.
4. **Inspect the UI:**
   * Point out the **"Requirements Breakdown"** table.
   * Notice the distinct badges for `Must-Have` (red/indigo) vs `Nice-to-Have` (slate).
   * Click the purple button: **"Proceed to Screening Candidate"**. (This stores the active job profile in the session and transitions to `/analysis`).

---

### Step 2: Screen Candidate A (Alex Morgan) — The Strong Match (1:30 – 3:00)
1. **Screen displayed:** Recruiter Screening Workspace (`/analysis`).
2. **Action:**
   * The Active Job indicates: `Senior Backend Engineer (Active in session)`.
   * Under **"Candidate Resume Document"**, click Browse and select:
     `evaluation/resumes/01_strong_backend.pdf`
   * Click **"Run Full Analysis"**.
3. **Observe the Pipeline Progress:**
   * "Extracting candidate profile from resume..."
   * "Evaluating requirements, hybrid scoring, and AI explanation..."
4. **Review Results Panels:**
   * **Overall Score Badge:** `84.1%` with green **"Must-Haves Met"** badge.
   * **Score Breakdown Card:**
     - `Rule Fit`: **100% (1.000)** $\to$ All mandatory and preferred technical skills found.
     - `Semantic Fit`: **64.3% (0.643)** $\to$ High cosine similarity across responsibilities.
     - `Experience Fit`: **100% (1.000)** $\to$ Candidate has 6.2 years (exceeds 5.0 years required).
     - `Education Fit`: **100% (1.000)** $\to$ Bachelor's Degree in Computer Science satisfied.
   * **Requirement Coverage Table:**
     - Show the recruiter that every single requirement has an **"Exact Evidence"** citation with highlighted keywords from Alex's resume.
   * **Skill Gap Analysis:**
     - Gaps card displays: `"No critical skill gaps identified."`
   * **LLM Explanation:**
     - Grounded summary highlighting Alex's microservices experience at Datastream Corp.
5. **Presenter Talking Point:**
   > *"Notice how the score is broken down. Experience is calculated strictly from tenure dates, not mixed into rule fit. The LLM provides an executive briefing, but every statement is backed by the evidence quotes directly visible in the audit table below."*

---

### Step 3: Screen Candidate B (Brian Miller) — Weak Match & Strict Gating (3:00 – 4:15)
1. **Action:**
   * On `/analysis`, keep the same active job.
   * Under **"Candidate Resume Document"**, select:
     `evaluation/resumes/02_weak_backend.pdf`
   * Click **"Run Full Analysis"**.
2. **Review Results Panels:**
   * **Overall Score Badge:** `25.2%` with red **"Must-Haves Missing"** badge.
   * **Score Breakdown Card:**
     - `Rule Fit`: **7.1% (0.071)** $\to$ Fails FastAPI, PostgreSQL, Docker, Redis.
     - `Experience Fit`: **12.8% (0.128)** $\to$ Candidate only has ~0.6 years out of 5.0 required years ($0.64 / 5.0 = 0.128$).
     - `Semantic Fit`: **44.8% (0.449)** $\to$ Basic Python context exists, but lacks backend infrastructure depth.
   * **Requirement Coverage Table:**
     - Rows for `FastAPI`, `PostgreSQL`, `Docker`, and `Redis` show clear red `Missing` status.
   * **Skill Gap Analysis Card:**
     - Categorizes gaps into `Missing Skills` (FastAPI, PostgreSQL, Redis, Docker) and `Insufficient Experience` (0.6 yrs vs 5.0 yrs required).
   * **Actionable Recommendations:**
     - Recommends foundational courses or junior-level pathways for building containerized REST APIs.
3. **Presenter Talking Point:**
   > *"Here is Candidate B. Notice how the system prevents automated false positives: even though Brian has the keyword 'Python', our deterministic engine flags that 4 out of 5 must-haves are missing and tenure is critically deficient. The candidate is clearly marked with 'Must-Haves Missing'."*

---

### Step 4: Screen Candidate C (Hector Vance) — Semantic Proximity vs Hard Rules (4:15 – 5:30)
*This is the key architectural showcase for examiners and technical interviewers.*

1. **Action:**
   * On `/analysis`, keep the active job.
   * Under **"Candidate Resume Document"**, select:
     `evaluation/resumes/08_related_skills_candidate.pdf`
   * Click **"Run Full Analysis"**.
2. **Examine the Candidate:**
   * Hector Vance is a seasoned Python engineer with **Flask, MySQL, Celery, and Docker** (3.0 years).
   * The job asks for **FastAPI, PostgreSQL, and Redis**.
3. **Review Results Panels:**
   * **Overall Score Badge:** `52.1%` (Moderate score, but with red `Must-Haves Missing` badge).
   * **The Contrast:**
     - `Semantic Fit`: **55.1%** $\to$ SentenceTransformer recognizes that Flask and MySQL are semantically related to backend web services and relational databases!
     - `Rule Fit`: **42.9%** $\to$ The deterministic matcher strictly marks `FastAPI` and `PostgreSQL` as NOT met.
4. **Presenter Talking Point:**
   > *"This scenario demonstrates why P_101's hybrid design is superior. In a pure LLM screener, the LLM might hallucinate that Flask is 'close enough' to satisfy a strict FastAPI requirement. In P_101, semantic matching acknowledges the candidate's adjacent web experience, boosting Semantic Fit, but the deterministic engine holds the line: must-haves are NOT met. The recruiter sees the complete, unvarnished picture."*

---

### Step 5: Recruiter Review & Ethical AI Guardrails (5:30 – 6:30)
1. **Scroll to Bottom of Analysis Screen:**
   * Highlight the **Recruiter Human Review Notice**:
     > *"Human Review Required: P_101 is an automated screening assistant designed to aid human recruiters. Matching scores and LLM recommendations do not constitute hiring or rejection decisions."*
2. **Highlight Privacy & Compliance:**
   * Zero PII bias: No demographic, gender, age, or ethnic information is utilized in scoring.
   * 100% reproducible: Same resume + same job produces the exact same score down to four decimal places.
3. **Conclude Demo:**
   * Open the floor for questions from committee or audience.

---

## 5. Visual Inspection Guide for UI Panels

When presenting each panel to evaluators, refer to these specific visual cues:

### 1. Overall Score Badge
* **Location:** Top left card in analysis results.
* **Display Elements:**
  - Large numerical percentage (e.g., `84.1%`).
  - Gating pill: `Must-Haves Met` (Green) or `Must-Haves Missing` (Red with AlertTriangle icon).
  - Status indicator: `High Match` ($Score \ge 75\%$), `Moderate Match` ($50\% \le Score < 75\%$), or `Low Match` ($Score < 50\%$).

### 2. Score Breakdown Card
* **Location:** Top right 4-quadrant grid.
* **Component Weights:**
  - **Rule Fit (40%)**: Ratio of satisfied requirements (skills, education, certs). Excludes tenure.
  - **Semantic Fit (30%)**: Cosine similarity of candidate evidence against skill requirements. Excludes tenure.
  - **Experience Fit (20%)**: Continuous tenure ratio $\min(\text{candidate\_years} / \text{required\_years}, 1.0)$.
  - **Education Fit (10%)**: Degree level satisfaction ($1.0$ if met, $0.5$ if related/partial, $0.0$ if missing).

### 3. Requirement Coverage Table
* **Location:** Middle full-width data table.
* **Columns:** Requirement Name | Type | Priority (Must-Have vs Nice-to-Have) | Status (Satisfied / Missing) | Confidence | Verified Evidence Snippet.
* **Key Detail:** Clicking "Show Snippet" expands the exact sentence extracted from the PDF resume.

### 4. Skill Gap Analysis Card
* **Location:** Left lower column.
* **Panels:**
  - **Missing Skills**: Requirements with zero evidence found in the resume.
  - **Insufficient Experience**: Areas where the candidate has the skill but lacks sufficient tenure or depth.
  - **Un-evaluable Items**: Subjective qualities (e.g., "fast learner") transparently flagged as requiring an interview.

### 5. LLM Explanation & Recommendations
* **Location:** Right lower column.
* **Panels:**
  - **Executive Summary**: 2-3 sentence grounded synthesis.
  - **Strengths & Matches**: Bulleted citations of verified candidate achievements.
  - **Candidate Recommendations**: Tailored development actions addressing identified skill gaps.

---

## 6. Demo Safety & Fallback Troubleshooting

If an unexpected condition arises during a live demonstration, use these instant remedies:

| Symptom | Probable Cause | Instant Remedy |
| :--- | :--- | :--- |
| **"Failed to fetch" on frontend** | Backend server is not running on port 8000 | In Terminal 1, restart: `uvicorn backend.app.main:app --port 8000 --reload` |
| **"Unsupported file format"** | Uploading `.txt` resume directly into parser | Use the provided `.pdf` file in `evaluation/resumes/` (e.g. `01_strong_backend.pdf`) |
| **Port 8000 already in use** | Stray background python process | In PowerShell: `Get-Process python* \| Stop-Process -Force`, then restart uvicorn |
| **Port 3000 already in use** | Prior `npm run dev` session running | In PowerShell: `npx kill-port 3000`, then rerun `npm run dev` |
| **Browser state stale** | Old session job cached in localStorage | Click "Configure Job Description" or refresh page with `Ctrl+Shift+R` |
| **No internet connection** | Wi-Fi dropped in demo room | **System is 100% offline.** Local embeddings and MockLLM require zero network connectivity. |
