import abc
import json
import logging
import re
from typing import Optional, List, Dict, Any
import httpx
from backend.app.config import get_settings
from backend.app.services.rule_extractor import (
    extract_email,
    extract_phone,
    extract_links,
    extract_sections,
    categorize_skill,
    parse_experience_blocks,
    parse_education_blocks,
    parse_project_blocks,
    SKILL_TAXONOMY,
)

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Base exception for LLM provider errors."""
    pass


class LLMUnavailableError(LLMError):
    """Raised when the LLM service or network endpoint cannot be reached."""
    pass


class BaseLLMClient(abc.ABC):
    """Abstract base class for all LLM provider implementations."""

    @abc.abstractmethod
    async def generate(self, prompt: str, temperature: float = 0.2) -> str:
        """Generate text completion from prompt."""
        pass


class MockLLMClient(BaseLLMClient):
    """
    Mock LLM Client for testing, CI/CD, and offline development.
    Can return pre-queued responses or intelligently parse the prompt using rules.
    """

    def __init__(self, responses: Optional[List[str]] = None):
        self.responses: List[str] = list(responses) if responses else []
        self.call_history: List[str] = []

    def set_responses(self, responses: List[str]) -> None:
        self.responses = list(responses)

    async def generate(self, prompt: str, temperature: float = 0.2) -> str:
        self.call_history.append(prompt)

        # If a predefined response is queued, return it first
        if self.responses:
            return self.responses.pop(0)

        # Route between resume extraction and job description analysis
        if "JOB DESCRIPTION TEXT:\n" in prompt or "Job Description (JD) analyzer" in prompt:
            return self._generate_heuristic_jd_json(prompt)

        # Fallback intelligent heuristic extractor for offline/test environments
        return self._generate_heuristic_json(prompt)

    def _generate_heuristic_jd_json(self, prompt: str) -> str:
        """Parses job description embedded in prompt using heuristic JD rule extractor."""
        from backend.app.services.jd_rule_extractor import parse_job_profile_rules

        marker = "JOB DESCRIPTION TEXT:\n"
        if marker in prompt:
            jd_text = prompt.split(marker, 1)[1].strip()
        else:
            jd_text = prompt

        payload = parse_job_profile_rules(jd_text)
        return json.dumps(payload, indent=2)

    def _generate_heuristic_json(self, prompt: str) -> str:
        """
        Parses resume text embedded in the prompt using heuristic sectioning and regex.
        Guarantees a valid, high-fidelity JSON structure matching the target schema.
        """
        # Extract the resume text portion from the prompt
        marker = "RESUME TEXT:\n"
        if marker in prompt:
            resume_text = prompt.split(marker, 1)[1].strip()
        else:
            resume_text = prompt

        lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
        name = None
        if lines:
            # Candidate name is often the first non-empty line
            first_line = lines[0]
            if len(first_line.split()) <= 4 and not any(char in first_line for char in "@/:"):
                name = first_line

        email = extract_email(resume_text)
        phone = extract_phone(resume_text)
        links = extract_links(resume_text)
        sections = extract_sections(resume_text)

        # 1. Skills
        skills: List[Dict[str, str]] = []
        skills_text = sections.get("skills", "")
        search_corpus = f"{skills_text} {resume_text}"
        seen_skills = set()

        display_map = {
            "fastapi": "FastAPI",
            "postgresql": "PostgreSQL",
            "postgres": "PostgreSQL",
            "mysql": "MySQL",
            "mongodb": "MongoDB",
            "javascript": "JavaScript",
            "js": "JS",
            "typescript": "TypeScript",
            "ts": "TS",
            "k8s": "K8s",
            "next.js": "Next.js",
            "nextjs": "Next.js",
            "node.js": "Node.js",
            "nodejs": "Node.js",
            "tailwind css": "Tailwind CSS",
            "tailwind": "Tailwind CSS",
            "rest apis": "REST APIs",
            "rest api": "REST APIs",
            "rest": "REST APIs",
            "ci/cd": "CI/CD",
            "gcp": "GCP",
            "aws": "AWS",
            "sql": "SQL",
            "html": "HTML",
            "html5": "HTML5",
            "css": "CSS",
            "css3": "CSS3",
            "nlp": "NLP",
            "pytorch": "PyTorch",
            "tensorflow": "TensorFlow",
        }

        for skill_key in SKILL_TAXONOMY.keys():
            if re.search(r"\b" + re.escape(skill_key) + r"\b", search_corpus, re.IGNORECASE):
                display_name = display_map.get(skill_key, skill_key.title() if not skill_key.isupper() else skill_key)
                if display_name not in seen_skills:
                    seen_skills.add(display_name)
                    skills.append({
                        "name": display_name,
                        "category": categorize_skill(skill_key),
                    })

        # 2. Summary
        summary = sections.get("summary", None)
        if summary:
            summary = " ".join(summary.split()).strip()

        # 3. Education (Multi-entry aware)
        education = parse_education_blocks(sections.get("education", ""))

        # 4. Experience (Multi-entry aware, distinct boundaries)
        experience = parse_experience_blocks(sections.get("experience", ""))

        # 5. Projects (Name separated from description and technologies)
        projects = parse_project_blocks(sections.get("projects", ""))

        # 6. Certifications
        certifications = []
        cert_text = sections.get("certifications", "")
        if cert_text:
            for cl in cert_text.splitlines():
                cl_clean = cl.strip().lstrip("-*• ")
                if cl_clean:
                    parts = re.split(r"\s+[-–]\s+", cl_clean)
                    c_name = parts[0].strip()
                    c_org = parts[1].strip() if len(parts) > 1 else None
                    date_m = re.search(r"\(?((?:19|20)\d\d)\)?", cl_clean)
                    date = date_m.group(1) if date_m else None
                    if c_org and date:
                        c_org = re.sub(r"\(?(?:19|20)\d\d\)?", "", c_org).strip(" -—") or c_org
                    certifications.append({
                        "name": c_name,
                        "issuing_organization": c_org,
                        "issue_date": date,
                        "credential_id": None,
                        "url": None,
                    })

        # 7. Achievements
        achievements = []
        ach_text = sections.get("achievements", "")
        if ach_text:
            for al in ach_text.splitlines():
                al_clean = al.strip().lstrip("-*• ")
                if al_clean:
                    date_m = re.search(r"\(?((?:19|20)\d\d)\)?", al_clean)
                    date = date_m.group(1) if date_m else None
                    title = al_clean
                    if date:
                        title = re.sub(r"\s*\(?(?:19|20)\d\d\)?", "", al_clean).strip(" -—")
                    achievements.append({
                        "title": title,
                        "description": None,
                        "date": date,
                    })

        result_payload = {
            "personal_info": {
                "name": name,
                "email": email,
                "phone": phone,
                "location": None,
                "linkedin_url": links.get("linkedin_url"),
                "github_url": links.get("github_url"),
            },
            "summary": summary,
            "skills": skills,
            "education": education,
            "experience": experience,
            "projects": projects,
            "certifications": certifications,
            "achievements": achievements,
        }

        return json.dumps(result_payload, indent=2)


class GeminiLLMClient(BaseLLMClient):
    """Gemini API provider using official REST endpoint and structured JSON generation."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        self.endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        )

    async def generate(self, prompt: str, temperature: float = 0.2) -> str:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "response_mime_type": "application/json",
            },
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.endpoint, json=payload)
                if response.status_code != 200:
                    logger.error(f"Gemini API returned status code {response.status_code}: {response.text}")
                    raise LLMError(f"Gemini API error (Status {response.status_code})")

                data = response.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    raise LLMError("Gemini API returned no completion candidates.")

                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts or "text" not in parts[0]:
                    raise LLMError("Malformed response structure from Gemini API.")

                return parts[0]["text"]
        except httpx.RequestError as e:
            logger.error(f"Network error communicating with Gemini API: {str(e)}")
            raise LLMUnavailableError(f"Unable to connect to Gemini LLM provider: {str(e)}")


class OpenAILLMClient(BaseLLMClient):
    """OpenAI API provider using Chat Completions and JSON mode."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.endpoint = "https://api.openai.com/v1/chat/completions"

    async def generate(self, prompt: str, temperature: float = 0.2) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.endpoint, headers=headers, json=payload)
                if response.status_code != 200:
                    logger.error(f"OpenAI API returned status code {response.status_code}")
                    raise LLMError(f"OpenAI API error (Status {response.status_code})")

                data = response.json()
                choices = data.get("choices", [])
                if not choices:
                    raise LLMError("OpenAI API returned no completion choices.")

                return choices[0]["message"]["content"]
        except httpx.RequestError as e:
            logger.error(f"Network error communicating with OpenAI API: {str(e)}")
            raise LLMUnavailableError(f"Unable to connect to OpenAI LLM provider: {str(e)}")


def get_llm_client(provider: Optional[str] = None) -> BaseLLMClient:
    """
    Factory function to retrieve the configured LLM client.
    Defaults to MockLLMClient if no API key is configured or if mock mode is requested.
    """
    settings = get_settings()
    active_provider = (provider or settings.llm_provider).lower()

    if active_provider == "gemini" and settings.llm_api_key:
        return GeminiLLMClient(api_key=settings.llm_api_key, model=settings.llm_model)

    if active_provider == "openai" and settings.llm_api_key:
        return OpenAILLMClient(api_key=settings.llm_api_key, model=settings.llm_model)

    # Default/fallback to mock provider for local offline and testing execution
    return MockLLMClient()
