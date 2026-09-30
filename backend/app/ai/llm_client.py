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

        # Fallback intelligent heuristic extractor for offline/test environments
        return self._generate_heuristic_json(prompt)

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

        # Heuristic Skills
        skills: List[Dict[str, str]] = []
        skills_text = sections.get("skills", "")
        # Common skill keywords
        skill_catalog = {
            "Python": "programming_language",
            "C++": "programming_language",
            "Java": "programming_language",
            "JavaScript": "programming_language",
            "TypeScript": "programming_language",
            "SQL": "database",
            "PostgreSQL": "database",
            "MySQL": "database",
            "MongoDB": "database",
            "FastAPI": "framework",
            "React": "framework",
            "Next.js": "framework",
            "Django": "framework",
            "Flask": "framework",
            "Node.js": "framework",
            "Docker": "devops",
            "Kubernetes": "devops",
            "Git": "tool",
            "AWS": "cloud",
            "GCP": "cloud",
            "Azure": "cloud",
            "Machine Learning": "ai_ml",
            "PyTorch": "ai_ml",
            "TensorFlow": "ai_ml",
            "REST APIs": "framework",
        }

        # Check full text and skills section
        search_corpus = f"{skills_text} {resume_text}"
        for skill_name, category in skill_catalog.items():
            if re.search(r"\b" + re.escape(skill_name) + r"\b", search_corpus, re.IGNORECASE):
                skills.append({"name": skill_name, "category": category})

        # Summary
        summary = sections.get("summary", None)
        if summary:
            summary = summary.replace("\n", " ").strip()

        # Education
        education = []
        edu_text = sections.get("education", "")
        if edu_text:
            edu_entry: Dict[str, Any] = {
                "degree": None,
                "institution": None,
                "field": None,
                "start_year": None,
                "end_year": None,
                "grade": None,
            }
            # Look for degree tokens
            degree_match = re.search(r"\b(B\.?Tech|B\.?S|M\.?S|Ph\.?D|Bachelor|Master|Diploma)\b", edu_text, re.I)
            if degree_match:
                edu_entry["degree"] = degree_match.group(0)

            # Look for years
            years = re.findall(r"\b(20\d\d|19\d\d)\b", edu_text)
            if len(years) >= 2:
                edu_entry["start_year"] = int(years[0])
                edu_entry["end_year"] = int(years[1])
            elif len(years) == 1:
                edu_entry["end_year"] = int(years[0])

            # Extract first line of education as institution if present
            edu_lines = [l for l in edu_text.splitlines() if l.strip()]
            if edu_lines:
                edu_entry["institution"] = edu_lines[0]

            education.append(edu_entry)

        # Experience
        experience = []
        exp_text = sections.get("experience", "")
        if exp_text:
            exp_lines = [l for l in exp_text.splitlines() if l.strip()]
            exp_entry: Dict[str, Any] = {
                "title": exp_lines[0] if exp_lines else "Software Engineer",
                "company": exp_lines[1] if len(exp_lines) > 1 else None,
                "location": None,
                "start_date": None,
                "end_date": None,
                "is_current": "present" in exp_text.lower(),
                "description": " ".join(exp_lines[2:]) if len(exp_lines) > 2 else exp_text,
                "skills": [s["name"] for s in skills[:3]],
            }
            dates = re.findall(r"\b(20\d\d|19\d\d)\b", exp_text)
            if dates:
                exp_entry["start_date"] = dates[0]
                if len(dates) > 1:
                    exp_entry["end_date"] = dates[1]
            experience.append(exp_entry)

        # Projects
        projects = []
        proj_text = sections.get("projects", "")
        if proj_text:
            proj_lines = [l for l in proj_text.splitlines() if l.strip()]
            proj_entry = {
                "name": proj_lines[0] if proj_lines else "Key Project",
                "description": " ".join(proj_lines[1:]) if len(proj_lines) > 1 else None,
                "technologies": [s["name"] for s in skills[:4]],
                "url": None,
                "start_date": None,
                "end_date": None,
            }
            projects.append(proj_entry)

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
            "certifications": [],
            "achievements": [],
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
