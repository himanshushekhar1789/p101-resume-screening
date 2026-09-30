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
