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

### `POST /jobs/{id}/resumes`
Upload one or multiple resumes (`.pdf`, `.docx`).
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
