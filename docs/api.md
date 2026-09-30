# API Specification — P_101 Resume Screening System

All endpoints follow RESTful conventions, using JSON for request and response bodies unless multipart file uploads are specified.

## Base URL
`/api/v1`

---

## 1. System & Health

### `GET /health`
Returns the status of the server, database connectivity, and configured AI providers.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": "connected",
  "environment": "development",
  "llm_provider": "mock"
}
```

---

## 2. Jobs Management

### `POST /jobs`
Create a job and initiate JD requirement analysis.
- **Body**: `{ "title": "Senior Backend Engineer", "jd_text": "...", "weights": {...} }`
- **Response**: `JobResponse` (includes extracted requirements)

### `GET /jobs`
List all jobs with candidate counts and screening status.

### `GET /jobs/{id}`
Retrieve job details and requirements.

### `PUT /jobs/{id}/requirements`
Allows recruiter review and manual editing of mandatory/preferred requirements before screening.

---

## 3. Resume Upload & Processing

### `POST /resumes/parse`
Extract text and structural metrics from an uploaded `.pdf` or `.docx` resume file.

- **Request**: Multipart Form Data: `file: UploadFile`
- **Supported MIME Types**: `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **Response (200 OK)**:
```json
{
  "filename": "alex_rivera_resume.pdf",
  "file_type": "pdf",
  "page_count": 1,
  "character_count": 160,
  "word_count": 20,
  "text": "Alex Rivera\nSenior Full Stack Developer\nSkills: Python, FastAPI, React, PostgreSQL, Docker\nExperience: 5 years at TechCorp designing cloud-native microservices."
}
```
- **Error Responses**:
  - `400 Bad Request`: Empty file, corrupt file header, or unsupported format (`.png`, `.txt`, etc.)
  - `413 Payload Too Large`: File exceeds configured maximum size limit (default 10 MB)
  - `422 Unprocessable Content`: Scanned/image-only PDF with no extractable text layer

### `POST /resumes/extract`
Parses and transforms an uploaded `.pdf` or `.docx` resume into a structured, validated candidate profile (`CandidateProfile`).

- **Request**: Multipart Form Data: `file: UploadFile`
- **Supported MIME Types**: `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **Response (200 OK)**:
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
      { "name": "FastAPI", "category": "framework" },
      { "name": "PostgreSQL", "category": "database" },
      { "name": "Docker", "category": "devops" }
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
        "title": "Senior Software Engineer - CloudCorp (2022 - Present)",
        "company": "CloudCorp",
        "location": null,
        "start_date": "2022",
        "end_date": null,
        "is_current": true,
        "description": "Designed and maintained high-throughput REST APIs.",
        "skills": ["Python", "FastAPI", "PostgreSQL"]
      }
    ],
    "projects": [
      {
        "name": "E-Commerce Microservices",
        "description": "Scalable order processing engine.",
        "technologies": ["Python", "FastAPI", "Docker"],
        "url": null,
        "start_date": null,
        "end_date": null
      }
    ],
    "certifications": [],
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
- **Error Responses**:
  - `400 Bad Request`: Empty file, corrupt file, or unsupported file format
  - `413 Payload Too Large`: Uploaded file exceeds size ceiling
  - `422 Unprocessable Content`: Scanned/image-only PDF or schema validation failure
  - `503 Service Unavailable`: AI provider unreachable

### `POST /jobs/{id}/resumes`
Upload one or multiple resumes (`.pdf`, `.docx`) associated with a job posting.
- **Form Data**: `files: List[UploadFile]`
- **Response**: List of uploaded and parsed candidate IDs with parsing summaries.

---

## 4. Job Description Analysis (Phase 4)

### `POST /jobs/analyze`
Extracts structured requirements, experience, education, certifications, and responsibilities from raw Job Description text.

- **Request Body (JSON)**:
```json
{
  "title": "Senior Backend Engineer",
  "text": "Job Summary: Looking for a Senior Backend Engineer...\nRequirements:\n- 5+ years of experience with Python and FastAPI\n- Solid knowledge of PostgreSQL and Docker\n- Kubernetes experience is a plus\nEducation: Bachelor's in Computer Science required."
}
```
- **Response (200 OK)**:
```json
{
  "title": "Senior Backend Engineer",
  "profile": {
    "title": "Senior Backend Engineer",
    "summary": "Looking for a Senior Backend Engineer...",
    "responsibilities": ["Design and maintain high-throughput microservices"],
    "skills": [
      {
        "name": "Python",
        "category": "programming_language",
        "priority": "must_have",
        "minimum_years": 5.0,
        "evidence": "5+ years of experience with Python"
      },
      {
        "name": "Kubernetes",
        "category": "devops",
        "priority": "nice_to_have",
        "minimum_years": null,
        "evidence": "Kubernetes experience is a plus"
      }
    ],
    "experience": {
      "minimum_years": 5.0,
      "maximum_years": null,
      "level": "senior",
      "field": "Software Engineering",
      "evidence": "5+ years of experience"
    },
    "education": {
      "degree_level": "Bachelor's",
      "fields_of_study": ["Computer Science"],
      "is_required": true,
      "evidence": "Bachelor's in Computer Science required"
    },
    "certifications": [],
    "other_requirements": [],
    "must_have": ["Python", "FastAPI", "PostgreSQL", "Docker", "Bachelor's in Computer Science"],
    "nice_to_have": ["Kubernetes"],
    "normalized_skills": [
      {
        "canonical_name": "Python",
        "original_name": "Python",
        "category": "programming_language",
        "priority": "must_have",
        "minimum_years": 5.0,
        "evidence": "5+ years of experience with Python",
        "normalization_method": "exact",
        "confidence": 1.0,
        "source": "job_description"
      }
    ]
  },
  "metadata": {
    "character_count": 256,
    "word_count": 38,
    "section_count": 3,
    "must_have_count": 5,
    "nice_to_have_count": 1,
    "llm_provider": "mock"
  }
}
```

### `POST /jobs/analyze/upload`
Extracts structured requirements from an uploaded Job Description file (`.txt`, `.pdf`, `.docx`).

- **Request**: Multipart Form Data: `file: UploadFile`, `title: Optional[str]`
- **Response (200 OK)**: Same schema as `/jobs/analyze`.

---

## 5. Skill Normalization & Taxonomy (Phase 5)

### `POST /skills/normalize`
Normalizes a list of raw skill strings into deduplicated canonical skill records.

- **Request Body (JSON)**:
```json
{
  "skills": ["python", "Python 3.11", "k8s", "Postgres", "AWS", "Docker"]
}
```
- **Response (200 OK)**:
```json
{
  "skills": [
    {
      "canonical_name": "Python",
      "original_name": "python",
      "original_names": ["python", "Python 3.11"],
      "category": "programming_language",
      "normalization_method": "exact",
      "confidence": 1.0,
      "source": "manual"
    },
    {
      "canonical_name": "Kubernetes",
      "original_name": "k8s",
      "original_names": ["k8s"],
      "category": "devops",
      "normalization_method": "alias",
      "confidence": 1.0,
      "source": "manual"
    }
  ]
}
```

### `GET /skills/taxonomy`
Retrieves the full controlled taxonomy of skills grouped by canonical category.

- **Response (200 OK)**:
```json
{
  "categories": {
    "programming_language": ["Python", "JavaScript", "TypeScript", "Go", "Java", "C++", "C#", "Rust"],
    "framework": ["FastAPI", "Django", "Flask", "React", "Next.js", "Vue.js", "Angular"],
    "database": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite"],
    "cloud": ["AWS", "Google Cloud", "Azure"],
    "devops": ["Docker", "Kubernetes", "Terraform", "CI/CD", "Git"]
  },
  "total_skills": 95,
  "total_categories": 10
}
```

---

## 6. Candidate ↔ Job Matching Engine (Phase 6)

### `POST /matching/analyze`
Deterministically evaluates a candidate against a job description's structured requirements.

- **Request Body (JSON)**:
```json
{
  "candidate": { ... },     // CandidateProfile or candidate dict
  "job": { ... }            // JobProfile or job dict
}
```
Alternatively, raw texts can be supplied in `candidate_text` and `job_text`.

- **Response (200 OK)**:
```json
{
  "matches": [
    {
      "requirement": {
        "requirement_id": "skill_Python",
        "category": "skill",
        "name": "Python",
        "priority": "must_have",
        "required_value": "Python (>= 5.0 years)",
        "source_text": "5+ years of experience with Python"
      },
      "status": "matched",
      "match_method": "canonical_exact",
      "candidate_evidence": "Python (programming_language); Verified Experience: Senior Software Engineer at CloudCorp (2020-2024)",
      "candidate_value": "5.0 years",
      "explanation": "Canonical exact skill match: 'Python' satisfies requirement 'Python'. Verifiable role duration: 5.0 years meets required 5.0 years."
    },
    {
      "requirement": {
        "requirement_id": "edu_bachelors",
        "category": "education",
        "name": "Bachelor's",
        "priority": "must_have",
        "required_value": "Bachelor's in Computer Science",
        "source_text": "Bachelor's in Computer Science required"
      },
      "status": "matched",
      "match_method": "education_match",
      "candidate_evidence": "B.Tech in Computer Science from State Tech University (2015-2019)",
      "candidate_value": "B.Tech (level 3) in Computer Science",
      "explanation": "Degree level Bachelor's satisfied (candidate level 3 >= required level 3) and field 'Computer Science' is compatible."
    }
  ],
  "summary": {
    "total_requirements": 8,
    "must_have_total": 6,
    "must_have_matched": 6,
    "must_have_partial": 0,
    "must_have_unmatched": 0,
    "must_have_not_evaluable": 0,
    "nice_to_have_total": 2,
    "nice_to_have_matched": 1,
    "nice_to_have_partial": 0,
    "nice_to_have_unmatched": 1,
    "nice_to_have_not_evaluable": 0,
    "all_must_haves_satisfied": true
  }
}
```

### `POST /matching/from-files`
Executes end-to-end deterministic matching directly from uploaded resume and JD documents (`.pdf`, `.docx`, `.txt`).

- **Request**: Multipart Form Data:
  - `resume_file`: UploadFile (PDF or DOCX)
  - `jd_file`: UploadFile (PDF, DOCX, or TXT)
- **Response (200 OK)**: `CandidateJobMatchResponse` with detailed requirement evaluations and summary.

---

## 7. Future Phases: Screening & Rankings

### `POST /jobs/{id}/screen`
Execute the multi-layer hybrid screening pipeline over all uploaded resumes for a job posting.

### `GET /jobs/{id}/rankings`
Retrieve the leaderboard of candidates sorted by `total_score` descending.

### `GET /candidates/{id}`
Retrieve a candidate's complete profile, evidence citations, skill gaps, and personalized recommendations.

### `GET /jobs/{id}/export`
Export screening results as a CSV file with complete scores and breakdown.
