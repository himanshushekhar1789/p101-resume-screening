import re
from typing import Dict, List, Optional, Tuple, Any
from backend.app.services.rule_extractor import SKILL_TAXONOMY, categorize_skill

# Recognized section headings in job descriptions (must be standalone headings, not content bullets)
JD_SECTION_PATTERNS: Dict[str, re.Pattern] = {
    "summary": re.compile(
        r"^(?:about(?:\s+the)?\s+(?:role|job|position|team|company|us)|job\s+(?:summary|overview|purpose|description)|role\s+summary|summary|overview|the\s+opportunity)(?:\s*:)?$",
        re.I,
    ),
    "responsibilities": re.compile(
        r"^(?:responsibilities|what\s+you(?:\x27ll|'ll|\s+will)\s+do|duties(?:\s+and\s+responsibilities)?|key\s+responsibilities|core\s+tasks|your\s+role|role\s+and\s+responsibilities)(?:\s*:)?$",
        re.I,
    ),
    "mandatory_requirements": re.compile(
        r"^(?:required(?:\s+qualifications|\s+skills|\s+experience)?|requirements|basic\s+qualifications|minimum\s+qualifications|must\s*[-–]?\s*have(?:\s+requirements)?|what\s+you\s+need|mandatory\s+requirements|qualifications)(?:\s*:)?$",
        re.I,
    ),
    "preferred_requirements": re.compile(
        r"^(?:preferred(?:\s+qualifications|\s+skills|\s+experience)?|nice\s*[-–]?\s*to\s*[-–]?\s*have(?:\s+requirements)?|good\s+to\s+have|bonus(?:\s+points)?|desired(?:\s+qualifications)?|what\s+gives\s+you\s+an\s+edge|additional\s+qualifications)(?:\s*:)?$",
        re.I,
    ),
    "education": re.compile(
        r"^(?:education(?:\s+and\s+experience)?|educational\s+requirements|academic\s+requirements|degree\s+requirements)(?:\s*:)?$",
        re.I,
    ),
    "experience": re.compile(
        r"^(?:years\s+of\s+experience|experience(?:\s+requirements)?|work\s+experience|prior\s+experience)(?:\s*:)?$",
        re.I,
    ),
    "benefits": re.compile(
        r"^(?:benefits|perks|what\s+we\s+offer|compensation(?:\s+and\s+benefits)?)(?:\s*:)?$",
        re.I,
    ),
}

# Explicit keyword indicators for priority
NICE_TO_HAVE_KEYWORDS = [
    "preferred",
    "nice to have",
    "nice-to-have",
    "good to have",
    "bonus",
    "plus",
    "a plus",
    "is a plus",
    "optional",
    "desired",
    "advantageous",
    "helpful",
    "ideal",
    "not required but",
]

MUST_HAVE_KEYWORDS = [
    "required",
    "mandatory",
    "must have",
    "must possess",
    "must be",
    "essential",
    "minimum",
    "strict requirement",
    "non-negotiable",
    "necessary",
]

DEGREE_PATTERN = re.compile(
    r"\b(B\.?Tech(?:nology)?|Bachelor(?:'s)?(?:\s+degree)?|B\.?S\.|B\.?S\b|B\.?A\.|B\.?A\b|B\.E\.|M\.?Tech|M\.?S\.|M\.?S\b|Master(?:'s)?(?:\s+degree)?|Ph\.?D\.|Ph\.?D\b|Doctorate|Diploma)(?=\s|$|[,—\-]|\b)",
    re.I,
)

FIELD_OF_STUDY_PATTERN = re.compile(
    r"\bin\s+([A-Za-z\s,/]*?(?:Computer Science|Software Engineering|Information Technology|Data Science|Artificial Intelligence|Machine Learning|Engineering|Mathematics|Statistics|related field|STEM)(?:\s+or\s+related\s+(?:technical\s+)?field)?)",
    re.I,
)

CERT_PATTERNS = [
    re.compile(r"\b(AWS\s+Certified(?:\s+[A-Za-z\s]+?(?:Architect|Developer|DevOps|SysOps|Specialty|Associate|Professional))?)\b", re.I),
    re.compile(r"\b(Azure\s+Certified(?:\s+[A-Za-z\s]+)?|Microsoft\s+Certified(?:\s+[A-Za-z\s]+)?)\b", re.I),
    re.compile(r"\b(Google\s+Cloud\s+Certified(?:\s+[A-Za-z\s]+)?|GCP\s+Certified(?:\s+[A-Za-z\s]+)?)\b", re.I),
    re.compile(r"\b(PMP|CISSP|CISA|CISM|CKA|CKAD|CKS|CompTIA(?:\s+[A-Za-z+]+)?)\b", re.I),
]


def extract_jd_sections(text: str) -> Dict[str, str]:
    """
    Segment job description text into logical sections based on recognized headings.
    Handles colon-based, numbered, and standalone headers. Skips bullet points.
    """
    lines = text.splitlines()
    detected_headers: List[Tuple[int, str]] = []

    for idx, line in enumerate(lines):
        raw_s = line.strip()
        # A section header must NOT be a bullet point item!
        if not raw_s or raw_s.startswith(("-", "*", "•")):
            continue
        stripped = raw_s.rstrip(":-_")
        stripped = re.sub(r"^(?:#{1,6}|\d+\.)\s*", "", stripped).strip()
        if not stripped or len(stripped) > 60:
            continue

        for section_name, pattern in JD_SECTION_PATTERNS.items():
            if pattern.match(stripped):
                detected_headers.append((idx, section_name))
                break

    sections: Dict[str, str] = {}
    if not detected_headers:
        sections["content"] = text
        return sections

    if detected_headers[0][0] > 0:
        intro_lines = lines[:detected_headers[0][0]]
        sections["header"] = "\n".join(intro_lines).strip()

    for i in range(len(detected_headers)):
        start_idx, sec_name = detected_headers[i]
        end_idx = detected_headers[i + 1][0] if i + 1 < len(detected_headers) else len(lines)
        section_content = lines[start_idx + 1 : end_idx]
        sections[sec_name] = "\n".join(section_content).strip()

    return sections


def detect_priority(text: str, default_priority: str = "must_have") -> str:
    """
    Determine whether a requirement is 'must_have' or 'nice_to_have'
    based on explicit phrasing in the surrounding text sentence or clause.
    """
    lower = text.lower()
    for kw in NICE_TO_HAVE_KEYWORDS:
        if kw in lower:
            return "nice_to_have"
    for kw in MUST_HAVE_KEYWORDS:
        if kw in lower:
            return "must_have"
    return default_priority


def extract_experience_requirements(text: str, sections: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Extract required years of experience, both general and skill-specific.
    """
    exp_items: List[Dict[str, Any]] = []
    seen_texts = set()

    # Search in experience, mandatory_requirements, and preferred_requirements sections first
    target_texts = [
        (sections.get("experience", ""), "must_have"),
        (sections.get("mandatory_requirements", ""), "must_have"),
        (sections.get("preferred_requirements", ""), "nice_to_have"),
    ]
    # If no sections, search full text
    if not any(t[0] for t in target_texts):
        target_texts = [(text, "must_have")]

    year_pattern = re.compile(
        r"([^.\n;]*?(?:(?:at\s+least|minimum\s+of)?\s*(\d+(?:\.\d+)?)\s*(?:-\s*(\d+(?:\.\d+)?))?\s*\+?\s*years?|entry-level|fresh\s+graduates?\s+welcome)[^.\n;]*)",
        re.I,
    )

    for target_block, default_sec_priority in target_texts:
        if not target_block:
            continue
        for match in year_pattern.finditer(target_block):
            full_clause = match.group(0).strip().lstrip("-*• ")
            if not full_clause or full_clause.lower() in seen_texts:
                continue
            seen_texts.add(full_clause.lower())

            # Check years
            m_yr = re.search(r"(\d+(?:\.\d+)?)\s*(?:-\s*(\d+(?:\.\d+)?))?\s*\+?\s*years?", full_clause, re.I)
            min_years: Optional[float] = None
            max_years: Optional[float] = None

            if m_yr:
                min_years = float(m_yr.group(1))
                if m_yr.group(2):
                    max_years = float(m_yr.group(2))
            elif re.search(r"\b(entry-level|fresh\s+graduates?\s+welcome)\b", full_clause, re.I):
                min_years = 0.0

            # Associate specific skill if mentioned in the clause
            found_skill = None
            for s_name in SKILL_TAXONOMY.keys():
                if len(s_name) > 2 and re.search(r"\b" + re.escape(s_name) + r"\b", full_clause, re.I):
                    found_skill = s_name.title() if not s_name.isupper() else s_name
                    break

            priority = detect_priority(full_clause, default_priority=default_sec_priority)

            exp_items.append({
                "skill": found_skill,
                "minimum_years": min_years,
                "maximum_years": max_years,
                "priority": priority,
                "text": full_clause,
                "evidence": full_clause,
            })

    return exp_items


def extract_education_requirements(text: str, sections: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Extract explicit educational requirements (degree and field of study).
    Does NOT invent degree requirements if not mentioned in the JD.
    """
    edu_items: List[Dict[str, Any]] = []
    seen_degrees = set()

    target_texts = [
        (sections.get("education", ""), "must_have"),
        (sections.get("mandatory_requirements", ""), "must_have"),
        (sections.get("preferred_requirements", ""), "nice_to_have"),
    ]
    if not any(t[0] for t in target_texts):
        target_texts = [(text, "must_have")]

    for target_block, default_sec_priority in target_texts:
        if not target_block:
            continue
        for line in target_block.splitlines():
            clean_line = line.strip().lstrip("-*• ")
            deg_m = DEGREE_PATTERN.search(clean_line)
            if deg_m:
                degree = deg_m.group(0).strip()
                deg_key = degree.lower()
                if deg_key in seen_degrees:
                    continue
                seen_degrees.add(deg_key)

                # Extract field
                field = None
                field_m = FIELD_OF_STUDY_PATTERN.search(clean_line)
                if field_m:
                    field = field_m.group(1).strip()

                priority = detect_priority(clean_line, default_priority=default_sec_priority)

                edu_items.append({
                    "degree": degree,
                    "field": field,
                    "priority": priority,
                    "evidence": clean_line,
                })

    return edu_items


def extract_certification_requirements(text: str, sections: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Extract explicit certification requirements. Does NOT invent certifications.
    """
    cert_items: List[Dict[str, Any]] = []
    seen_certs = set()

    target_texts = [
        (sections.get("mandatory_requirements", ""), "must_have"),
        (sections.get("preferred_requirements", ""), "nice_to_have"),
        (sections.get("content", text), "must_have"),
    ]

    for target_block, default_sec_priority in target_texts:
        if not target_block:
            continue
        for pat in CERT_PATTERNS:
            for m in pat.finditer(target_block):
                cert_name = m.group(0).strip()
                if cert_name.lower() in seen_certs:
                    continue
                seen_certs.add(cert_name.lower())

                # Find line/sentence for evidence & priority
                evidence = cert_name
                for line in target_block.splitlines():
                    if cert_name in line:
                        evidence = line.strip().lstrip("-*• ")
                        break

                priority = detect_priority(evidence, default_priority=default_sec_priority)
                cert_items.append({
                    "name": cert_name,
                    "priority": priority,
                    "evidence": evidence,
                })

    return cert_items


def extract_skill_requirements(text: str, sections: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Extract required and preferred skills using the standard system skill taxonomy.
    """
    skills: List[Dict[str, Any]] = []
    seen_skills = set()

    # Priority contexts
    mand_text = sections.get("mandatory_requirements", "")
    pref_text = sections.get("preferred_requirements", "")
    other_text = f"{sections.get('summary', '')} {sections.get('content', text)}"

    display_map = {
        "fastapi": "FastAPI",
        "postgresql": "PostgreSQL",
        "postgres": "PostgreSQL",
        "mysql": "MySQL",
        "mongodb": "MongoDB",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
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
        pat = re.compile(r"\b" + re.escape(skill_key) + r"\b", re.I)

        # Check preferred section first
        in_pref = bool(pref_text and pat.search(pref_text))
        in_mand = bool(mand_text and pat.search(mand_text))
        in_other = bool(pat.search(other_text))

        if in_pref or in_mand or in_other:
            display_name = display_map.get(skill_key, skill_key.title() if not skill_key.isupper() else skill_key)
            if display_name in seen_skills:
                continue
            seen_skills.add(display_name)

            # Determine priority & evidence
            priority = "must_have"
            evidence = None
            min_years = None

            if in_pref:
                priority = "nice_to_have"
                for line in pref_text.splitlines():
                    if pat.search(line):
                        evidence = line.strip().lstrip("-*• ")
                        break
            elif in_mand:
                priority = "must_have"
                for line in mand_text.splitlines():
                    if pat.search(line):
                        evidence = line.strip().lstrip("-*• ")
                        break
            else:
                # In generic text, search surrounding sentence
                for line in text.splitlines():
                    if pat.search(line):
                        clean_line = line.strip().lstrip("-*• ")
                        evidence = clean_line
                        priority = detect_priority(clean_line, default_priority="must_have")
                        break

            # If evidence has 'is a plus' or 'preferred', ensure nice_to_have
            if evidence:
                priority = detect_priority(evidence, default_priority=priority)
                # Check for minimum years explicitly attached
                y_m = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*years?", evidence, re.I)
                if y_m:
                    min_years = float(y_m.group(1))

            skills.append({
                "name": display_name,
                "category": categorize_skill(skill_key),
                "priority": priority,
                "minimum_years": min_years,
                "evidence": evidence,
            })

    return skills


def extract_responsibilities(sections: Dict[str, str]) -> List[str]:
    """
    Extract explicit job responsibilities separately from qualification requirements.
    """
    resp_text = sections.get("responsibilities", "")
    if not resp_text:
        return []

    responsibilities: List[str] = []
    for line in resp_text.splitlines():
        clean = line.strip().lstrip("-*• ")
        clean = re.sub(r"^\d+\.\s*", "", clean).strip()
        if clean and len(clean.split()) >= 3:
            responsibilities.append(clean)

    return responsibilities


def extract_other_requirements(text: str, sections: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Extract other explicit requirements (location, work authorization, language, shifts).
    """
    other_items: List[Dict[str, Any]] = []
    seen_texts = set()

    patterns = [
        ("location", re.compile(r"([^.\n;]*?(?:must\s+be\s+located|must\s+reside|based\s+in|authorized\s+to\s+work|work\s+authorization)[^.\n;]*)", re.I)),
        ("language", re.compile(r"([^.\n;]*?(?:fluent\s+in|bilingual|proficiency\s+in\s+English|communication\s+skills)[^.\n;]*)", re.I)),
        ("other", re.compile(r"([^.\n;]*?(?:night\s+shifts?|on-call|travel\s+up\s+to\s+\d+%|background\s+check)[^.\n;]*)", re.I)),
    ]

    combined_text = f"{sections.get('mandatory_requirements', '')}\n{sections.get('preferred_requirements', '')}\n{text}"

    for req_type, pat in patterns:
        for m in pat.finditer(combined_text):
            clause = m.group(0).strip().lstrip("-*• ")
            if not clause or clause.lower() in seen_texts:
                continue
            seen_texts.add(clause.lower())

            priority = detect_priority(clause, default_priority="must_have")
            other_items.append({
                "type": req_type,
                "text": clause,
                "priority": priority,
                "evidence": clause,
            })

    return other_items


def extract_job_metadata(text: str, sections: Dict[str, str], initial_title: Optional[str] = None) -> Dict[str, Optional[str]]:
    """
    Extract job title, company name, location, and brief summary.
    """
    job_title = initial_title
    company = None
    location = None

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Job title detection if not provided
    if not job_title and lines:
        for line in lines[:5]:
            m_title = re.search(r"^(?:Job\s+Title|Position|Role):\s*(.*)", line, re.I)
            if m_title:
                job_title = m_title.group(1).strip()
                break
        if not job_title:
            first_line = lines[0].lstrip("#-•* ")
            if len(first_line.split()) <= 6 and not any(c in first_line for c in "@/:"):
                job_title = first_line

    # Company detection
    for line in lines[:8]:
        m_co = re.search(r"^(?:Company|Organization|About\s+([A-Za-z0-9\s]+)):\s*(.*)", line, re.I)
        if m_co:
            company = (m_co.group(2) or m_co.group(1)).strip()
            break

    # Location detection
    for line in lines[:8]:
        m_loc = re.search(r"^(?:Location|Work\s+Location):\s*(.*)", line, re.I)
        if m_loc:
            location = m_loc.group(1).strip()
            break

    # Summary
    summary = sections.get("summary", None)
    if summary:
        summary = " ".join(summary.split()).strip()

    return {
        "job_title": job_title,
        "company": company,
        "location": location,
        "summary": summary,
    }


def parse_job_profile_rules(text: str, initial_title: Optional[str] = None) -> Dict[str, Any]:
    """
    High-confidence deterministic extraction of all JobProfile components.
    """
    sections = extract_jd_sections(text)
    metadata = extract_job_metadata(text, sections, initial_title)

    skills = extract_skill_requirements(text, sections)
    experience_reqs = extract_experience_requirements(text, sections)
    education_reqs = extract_education_requirements(text, sections)
    certification_reqs = extract_certification_requirements(text, sections)
    responsibilities = extract_responsibilities(sections)
    other_reqs = extract_other_requirements(text, sections)

    # Build must_have and nice_to_have collections
    must_have: List[Dict[str, Any]] = []
    nice_to_have: List[Dict[str, Any]] = []

    # Map skills
    for s in skills:
        item = {
            "text": s["evidence"] or f"Experience with {s['name']}",
            "type": "skill",
            "priority": s["priority"],
            "skill": s["name"],
            "minimum_years": s.get("minimum_years"),
            "evidence": s["evidence"],
        }
        if s["priority"] == "must_have":
            must_have.append(item)
        else:
            nice_to_have.append(item)

    # Map experience
    for exp in experience_reqs:
        item = {
            "text": exp["text"],
            "type": "experience",
            "priority": exp["priority"],
            "skill": exp.get("skill"),
            "minimum_years": exp.get("minimum_years"),
            "evidence": exp["evidence"],
        }
        if exp["priority"] == "must_have":
            must_have.append(item)
        else:
            nice_to_have.append(item)

    # Map education
    for edu in education_reqs:
        item = {
            "text": edu["evidence"] or f"{edu['degree']} in {edu.get('field', 'related field')}",
            "type": "education",
            "priority": edu["priority"],
            "skill": None,
            "minimum_years": None,
            "evidence": edu["evidence"],
        }
        if edu["priority"] == "must_have":
            must_have.append(item)
        else:
            nice_to_have.append(item)

    # Map certifications
    for cert in certification_reqs:
        item = {
            "text": cert["evidence"] or cert["name"],
            "type": "certification",
            "priority": cert["priority"],
            "skill": None,
            "minimum_years": None,
            "evidence": cert["evidence"],
        }
        if cert["priority"] == "must_have":
            must_have.append(item)
        else:
            nice_to_have.append(item)

    # Map other requirements
    for oth in other_reqs:
        item = {
            "text": oth["text"],
            "type": oth.get("type", "other"),
            "priority": oth["priority"],
            "skill": None,
            "minimum_years": None,
            "evidence": oth["evidence"],
        }
        if oth["priority"] == "must_have":
            must_have.append(item)
        else:
            nice_to_have.append(item)

    return {
        "job_title": metadata["job_title"],
        "company": metadata["company"],
        "location": metadata["location"],
        "summary": metadata["summary"],
        "skills": skills,
        "experience_requirements": experience_reqs,
        "education_requirements": education_reqs,
        "certification_requirements": certification_reqs,
        "other_requirements": other_reqs,
        "responsibilities": responsibilities,
        "must_have": must_have,
        "nice_to_have": nice_to_have,
    }
