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

## 4. Screening & Rankings

### `POST /jobs/{id}/screen`
Execute the screening pipeline over all uploaded resumes for the specified job.
- **Parameters**: `masked: bool` (optional, default false)
- **Response**: Summary of screened candidates.

### `GET /jobs/{id}/rankings`
Retrieve the leaderboard of candidates sorted by `total_score` descending.
- **Response**: List of candidates with full score breakdowns, matched skills, and top gaps.

### `GET /candidates/{id}`
Retrieve a candidate's complete profile, extracted experience, evidence citations, skill gaps, and personalized recommendations.

### `GET /jobs/{id}/export`
Export screening results as a CSV file with complete scores and breakdown.
