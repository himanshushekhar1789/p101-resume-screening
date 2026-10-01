# P_101 — Technical Documentation Index

Welcome to the technical documentation repository for **P_101: LLM-Based Resume Screening System**. This index provides a structured directory of all architectural, evaluative, operational, and demonstration documentation.

---

## 1. Primary Documentation Suite

| Document | File Path | Target Audience | Primary Focus |
| :--- | :--- | :--- | :--- |
| **Final Technical Report** | [`docs/final-project-report.md`](file:///C:/Users/himan/.gemini/antigravity/scratch/p101-resume-screening/docs/final-project-report.md) | Faculty, Evaluators, Examiners | Formal 29-section academic and technical report covering system vision, problem statement, architecture, mathematical formulation, evaluation results, and ethical considerations. |
| **System Architecture Guide** | [`docs/architecture.md`](file:///C:/Users/himan/.gemini/antigravity/scratch/p101-resume-screening/docs/architecture.md) | System Architects, Engineers | In-depth engineering specifications, data flow diagrams, pipeline invariants, false-positive protection matrices, and component decoupling rules. |
| **Evaluation & Benchmark Suite** | [`docs/evaluation.md`](file:///C:/Users/himan/.gemini/antigravity/scratch/p101-resume-screening/docs/evaluation.md) | Reviewers, QA Engineers | Comprehensive evaluation methodology across 10 synthetic candidates, 5 job descriptions, 10 curated test cases, scoring invariants (A–F), and pipeline latency telemetry. |
| **Live Demonstration Script** | [`docs/demo.md`](file:///C:/Users/himan/.gemini/antigravity/scratch/p101-resume-screening/docs/demo.md) | Presenters, Demonstrators | Minute-by-minute 5–7 minute live presentation script with click-by-click instructions, UI inspection cues, talking points, and emergency troubleshooting fallbacks. |
| **Demo Checklist & Viva Q&A** | [`docs/demo-checklist.md`](file:///C:/Users/himan/.gemini/antigravity/scratch/p101-resume-screening/docs/demo-checklist.md) | Viva Candidates, Examiners | Pre-demo flight checks, during-demo checkpoints, post-demo cleanup, and authoritative answers to the 6 most common technical viva defense questions. |
| **Project Presentation Deck (MD)** | [`docs/presentation.md`](file:///C:/Users/himan/.gemini/antigravity/scratch/p101-resume-screening/docs/presentation.md) | Presenters, Evaluators | Complete 15-slide presentation source-of-truth outline with visual layouts, key points, timed speaker notes (8–12 min), and demo handoff. |
| **Interactive Slide Deck (HTML)** | [`docs/presentation.html`](file:///C:/Users/himan/.gemini/antigravity/scratch/p101-resume-screening/docs/presentation.html) | Presenters, Faculty | Standalone, full-screen interactive slide presentation runnable in any browser with keyboard shortcuts (arrows/spacebar) and speaker notes drawer. |
| **PowerPoint Slide Deck (.pptx)** | [`docs/presentation.pptx`](file:///C:/Users/himan/.gemini/antigravity/scratch/p101-resume-screening/docs/presentation.pptx) | Presenters, Faculty | Native 16:9 widescreen Microsoft PowerPoint presentation file with formatted dark theme cards, tables, and integrated speaker notes. |
| **REST API Reference** | [`docs/api.md`](file:///C:/Users/himan/.gemini/antigravity/scratch/p101-resume-screening/docs/api.md) | API Consumers, Integrators | Complete specifications of all 13 FastAPI endpoints under `/api/v1` with request/response schemas, error codes, and curl examples. |

---

## 2. Evaluation Reports & Telemetry

* **Latest Markdown Benchmark Report**: [`evaluation/reports/latest.md`](file:///C:/Users/himan/.gemini/antigravity/scratch/p101-resume-screening/evaluation/reports/latest.md)
* **Latest Machine-Readable Telemetry (JSON)**: [`evaluation/reports/latest.json`](file:///C:/Users/himan/.gemini/antigravity/scratch/p101-resume-screening/evaluation/reports/latest.json)
* **Evaluation Manifest & Ground-Truth Test Cases**: [`evaluation/evaluation_manifest.json`](file:///C:/Users/himan/.gemini/antigravity/scratch/p101-resume-screening/evaluation/evaluation_manifest.json)

---

## 3. Quick Reference: System Invariants & Philosophy

1. **Deterministic Authority**: Hard requirements (must-have skills, minimum tenure) are governed solely by mathematical set logic. Dense embeddings and LLMs provide supporting context and explanations but cannot override missing hard requirements.
2. **Orthogonal Scoring**: Rule Fit (30%), Semantic Fit (40%), Experience Fit (20%), and LLM-Supported Fit (10%) are strictly orthogonal. General career tenure is completely excluded from Rule Fit and Semantic Fit to prevent double-counting.
3. **Evidence Grounding**: Every score, satisfied requirement, and identified skill gap is anchored directly to verbatim text extracts from the candidate's resume.
4. **Decision Support Only**: The system does not rank candidates, generate leaderboards, or produce automated hire/reject decisions. Sole decision authority remains with human recruiters.
