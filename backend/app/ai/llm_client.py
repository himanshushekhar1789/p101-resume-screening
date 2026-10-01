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

        # Route between resume extraction, JD analysis, and explanation generation
        if "CANDIDATE EXPLANATION PROMPT" in prompt or "evidence-grounded resume analysis assistant" in prompt or "STRUCTURED MATCHING AND GAP CONTEXT:" in prompt:
            return self._generate_heuristic_explanation_json(prompt)

        if "JOB DESCRIPTION TEXT:\n" in prompt or "Job Description (JD) analyzer" in prompt:
            return self._generate_heuristic_jd_json(prompt)

        # Fallback intelligent heuristic extractor for offline/test environments
        return self._generate_heuristic_json(prompt)


    def _generate_heuristic_explanation_json(self, prompt: str) -> str:
        """
        Parses structured matching and gap context embedded in the prompt and generates
        a deterministic, fully schema-compliant LLMExplanationResponse JSON for offline testing.
        """
        from backend.app.ai.validators import extract_json_payload

        # Extract structured context from prompt
        marker = "STRUCTURED MATCHING AND GAP CONTEXT:\n"
        if marker in prompt:
            context_raw = prompt.split(marker, 1)[1].strip()
        else:
            context_raw = prompt

        try:
            cleaned_json = extract_json_payload(context_raw)
            context = json.loads(cleaned_json)
        except Exception:
            context = {}

        candidate_data = context.get("candidate", {})
        job_data = context.get("job", {})
        matching_data = context.get("matching", {})
        score_data = context.get("score", {})
        gaps_data = context.get("gaps", {})

        cand_name = candidate_data.get("name") or candidate_data.get("personal_info", {}).get("name") or "Candidate"
        job_title = job_data.get("job_title") or "Target Position"

        strengths: List[str] = []
        key_gaps: List[str] = []
        req_explanations: List[Dict[str, Any]] = []
        recommendations: List[Dict[str, Any]] = []

        skill_templates = {
            "kubernetes": {
                "rec": "Study Kubernetes fundamentals and build a deployment project covering pods, deployments, services, config maps and scaling.",
                "artifacts": ["deployment manifests", "services", "scaling configuration", "documented project usage"]
            },
            "k8s": {
                "rec": "Study Kubernetes fundamentals and build a deployment project covering pods, deployments, services, config maps and scaling.",
                "artifacts": ["deployment manifests", "services", "scaling configuration", "documented project usage"]
            },
            "postgresql": {
                "rec": "Strengthen PostgreSQL by building a project involving schema design, queries, indexing, transactions, and database optimization.",
                "artifacts": ["schema design files", "query benchmarks", "indexing strategies", "documented database project"]
            },
            "python": {
                "rec": "Build or contribute to projects that provide sustained Python development experience and produce verifiable evidence.",
                "artifacts": ["production Python codebase", "tested modules", "package deployment"]
            },
            "docker": {
                "rec": "Build and containerize multi-service applications using Docker and Docker Compose.",
                "artifacts": ["Dockerfile specifications", "docker-compose.yml configurations", "container build logs"]
            },
            "aws": {
                "rec": "Deploy cloud infrastructure using AWS services and document architecture and resource configurations.",
                "artifacts": ["CloudFormation or Terraform templates", "documented cloud architecture", "AWS deployment artifacts"]
            },
            "redis": {
                "rec": "Implement distributed caching, rate-limiting, and session management using Redis.",
                "artifacts": ["cache integration code", "key expiration strategies", "performance benchmarks"]
            },
        }

        # Process structured skill gaps from Phase 9
        skill_gaps = gaps_data.get("skill_gaps", [])
        for gap in skill_gaps:
            skill_name = gap.get("canonical_skill_name") or gap.get("skill_name", "Skill")
            norm_key = skill_name.lower().strip()
            status = gap.get("status", "missing")
            priority = gap.get("priority", "must_have")
            req_id = gap.get("requirement_id", f"skill_{skill_name}")
            category = gap.get("category", "skill")
            cand_evidence = gap.get("candidate_evidence", [])
            req_val = gap.get("required_value")
            cand_val = gap.get("candidate_value")
            shortfall = gap.get("shortfall")
            sem_evidence = gap.get("semantic_evidence")

            if status == "satisfied":
                evidence_text = cand_evidence[0] if cand_evidence else "documented in candidate profile"
                strengths.append(f"Demonstrates verified competency in {skill_name} ({evidence_text}).")
                req_explanations.append({
                    "requirement_id": req_id,
                    "requirement_name": skill_name,
                    "category": category,
                    "priority": priority,
                    "status": "satisfied",
                    "explanation": f"The candidate demonstrates {skill_name} through documented profile evidence.",
                    "evidence_used": cand_evidence,
                })
            elif status == "missing":
                key_gaps.append(f"Missing required skill: {skill_name} ({priority})")
                if sem_evidence:
                    expl = (
                        f"Required skill {skill_name} is not directly demonstrated in the candidate profile. "
                        f"Supporting semantic evidence: {sem_evidence} was detected, but cannot substitute for required skill."
                    )
                else:
                    expl = f"Required skill {skill_name} is not directly demonstrated in the candidate profile."
                req_explanations.append({
                    "requirement_id": req_id,
                    "requirement_name": skill_name,
                    "category": category,
                    "priority": priority,
                    "status": "missing",
                    "explanation": expl,
                    "evidence_used": [],
                })
                # Recommendation for missing skill
                template = skill_templates.get(norm_key, {
                    "rec": f"Strengthen competency in {skill_name} by building a practical project demonstrating core concepts and workflows.",
                    "artifacts": [f"{skill_name} project repository", f"Documented production deployment of {skill_name}"]
                })
                recommendations.append({
                    "skill": skill_name,
                    "gap_status": "missing",
                    "priority": priority,
                    "reason": f"Required skill {skill_name} is not demonstrated in candidate evidence.",
                    "recommendation": template["rec"],
                    "evidence_to_build": template["artifacts"],
                })
            elif status == "insufficient":
                key_gaps.append(
                    f"Insufficient verified experience in {skill_name} "
                    f"({cand_val or 'unverified'} demonstrated vs {req_val or 'required'} required, shortfall of {shortfall or 'unspecified'})"
                )
                req_explanations.append({
                    "requirement_id": req_id,
                    "requirement_name": skill_name,
                    "category": category,
                    "priority": priority,
                    "status": "insufficient",
                    "explanation": (
                        f"The candidate demonstrates {skill_name} experience, but verified duration "
                        f"of {cand_val or '0 years'} falls short of the required {req_val or 'required tenure'} "
                        f"by {shortfall or 'deficit'}."
                    ),
                    "evidence_used": cand_evidence,
                })
                template = skill_templates.get(norm_key, {
                    "rec": f"Gain additional hands-on experience and contribute to production initiatives utilizing {skill_name}.",
                    "artifacts": [f"Additional documented project or work tenure using {skill_name}"]
                })
                recommendations.append({
                    "skill": skill_name,
                    "gap_status": "insufficient",
                    "priority": priority,
                    "reason": f"Demonstrated tenure ({cand_val or 'unverified'}) is below required {req_val or 'threshold'}.",
                    "recommendation": template["rec"],
                    "evidence_to_build": template["artifacts"],
                })
            elif status == "not_evaluable":
                key_gaps.append(f"Unverified tenure for {skill_name} ({priority})")
                req_explanations.append({
                    "requirement_id": req_id,
                    "requirement_name": skill_name,
                    "category": category,
                    "priority": priority,
                    "status": "not_evaluable",
                    "explanation": f"{skill_name} is listed in the candidate profile, but available evidence does not establish verified tenure.",
                    "evidence_used": cand_evidence,
                })
                template = skill_templates.get(norm_key, {
                    "rec": f"Clarify and document exact project duration and dated roles involving {skill_name}.",
                    "artifacts": [f"Dated resume entries and portfolio artifacts referencing {skill_name}"]
                })
                recommendations.append({
                    "skill": skill_name,
                    "gap_status": "not_evaluable",
                    "priority": priority,
                    "reason": f"Tenure duration for {skill_name} cannot be verified from dated roles.",
                    "recommendation": template["rec"],
                    "evidence_to_build": template["artifacts"],
                })

        # Process any non-skill matches from Phase 6 matching
        matches = matching_data.get("matches", [])
        for m in matches:
            req = m.get("requirement", {})
            req_type = req.get("type", "skill")
            if req_type != "skill":
                r_name = req.get("name", "Requirement")
                r_id = req.get("requirement_id", f"{req_type}_{r_name}")
                m_status = m.get("status", "matched")
                p = req.get("priority", "must_have")
                ev = m.get("candidate_evidence")
                ev_list = [ev] if ev else []
                if m_status == "matched":
                    strengths.append(f"Satisfies {req_type} requirement: {r_name}.")
                    req_explanations.append({
                        "requirement_id": r_id,
                        "requirement_name": r_name,
                        "category": req_type,
                        "priority": p,
                        "status": "satisfied",
                        "explanation": f"The candidate satisfies {req_type} requirement '{r_name}' with verified evidence.",
                        "evidence_used": ev_list,
                    })
                elif m_status == "unmatched":
                    key_gaps.append(f"Unmatched {req_type} requirement: {r_name}")
                    req_explanations.append({
                        "requirement_id": r_id,
                        "requirement_name": r_name,
                        "category": req_type,
                        "priority": p,
                        "status": "missing",
                        "explanation": f"The candidate does not satisfy {req_type} requirement '{r_name}'.",
                        "evidence_used": ev_list,
                    })

        # Experience explanation
        exp_gaps = gaps_data.get("experience_gaps", [])
        if exp_gaps:
            exp_parts = []
            for eg in exp_gaps:
                exp_text = eg.get("requirement_text", "Experience")
                if eg.get("status") == "satisfied":
                    exp_parts.append(
                        f"Satisfied requirement '{exp_text}': {eg.get('candidate_years')} years verified "
                        f"(meets or exceeds required {eg.get('required_years')} years)."
                    )
                else:
                    exp_parts.append(
                        f"Shortfall in '{exp_text}': {eg.get('candidate_years')} years verified vs "
                        f"{eg.get('required_years')} years required (shortfall of {eg.get('shortfall_years')} years)."
                    )
            experience_explanation = " ".join(exp_parts)
        else:
            experience_explanation = "No separate career tenure gaps identified."

        # Score explanation
        if score_data:
            c_score = score_data.get("candidate_fit_score")
            r_score = score_data.get("rule_fit_score")
            s_score = score_data.get("semantic_fit_score")
            e_score = score_data.get("experience_fit_score")
            parts = []
            if r_score is not None:
                parts.append(f"rule fit of {r_score:.2f}")
            if s_score is not None:
                parts.append(f"semantic fit of {s_score:.2f}")
            if e_score is not None:
                parts.append(f"experience fit of {e_score:.2f}")

            score_str = f"{c_score:.2f}" if c_score is not None else "N/A"
            factors = ", ".join(parts) if parts else "component metrics"
            score_explanation = (
                f"The overall candidate fit score of {score_str} reflects {factors}. "
                f"The primary factors reducing the score are the identified requirement gaps: "
                f"{', '.join(key_gaps) if key_gaps else 'none'}."
            )
        else:
            score_explanation = "Scoring breakdown was not computed for this evaluation."

        # Narrative Summary
        summary = (
            f"Candidate evaluation for {job_title}: {len(strengths)} requirement(s) verified as satisfied, "
            f"with {len(key_gaps)} identified gap(s). All assessments are grounded directly in documented resume evidence."
        )

        result_payload = {
            "candidate_id": candidate_data.get("candidate_id"),
            "candidate_name": cand_name,
            "job_id": job_data.get("job_id"),
            "job_title": job_title,
            "summary": summary,
            "strengths": strengths,
            "key_gaps": key_gaps,
            "requirement_explanations": req_explanations,
            "experience_explanation": experience_explanation,
            "score_explanation": score_explanation,
            "recommendations": recommendations,
            "disclaimer": (
                "This explanation and recommendation report is generated by an AI decision-support assistant "
                "based strictly on parsed resume and job evidence. It does not constitute a hiring or rejection decision."
            ),
        }

        return json.dumps(result_payload, indent=2)

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
