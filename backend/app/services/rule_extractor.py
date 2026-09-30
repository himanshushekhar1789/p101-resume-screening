import re
from typing import Optional, Dict, List, Tuple, Any

EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

# Supports standard international, US/Canada, and Indian phone representations
PHONE_REGEX = re.compile(
    r"(?:(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}|\+\d{1,3}[-.\s]?\d{10})"
)

LINKEDIN_REGEX = re.compile(
    r"https?://(?:www\.)?linkedin\.com/in/[A-Za-z0-9_\-%]+", re.IGNORECASE
)

GITHUB_REGEX = re.compile(
    r"https?://(?:www\.)?github\.com/[A-Za-z0-9_\-%]+", re.IGNORECASE
)

SECTION_PATTERNS: Dict[str, re.Pattern] = {
    "summary": re.compile(
        r"^(?:professional\s+summary|career\s+summary|profile\s+summary|summary|profile|about\s+me|career\s+objective|objective)\b",
        re.IGNORECASE,
    ),
    "skills": re.compile(
        r"^(?:technical\s+skills|core\s+competencies|technologies|skills\s+and\s+abilities|skills|areas\s+of\s+expertise)\b",
        re.IGNORECASE,
    ),
    "experience": re.compile(
        r"^(?:work\s+experience|professional\s+experience|employment\s+history|experience|work\s+history|internships)\b",
        re.IGNORECASE,
    ),
    "education": re.compile(
        r"^(?:education(?:\s+and\s+qualifications)?|academic\s+background|academics|qualifications)\b",
        re.IGNORECASE,
    ),
    "projects": re.compile(
        r"^(?:technical\s+projects|academic\s+projects|personal\s+projects|key\s+projects|projects)\b",
        re.IGNORECASE,
    ),
    "certifications": re.compile(
        r"^(?:certifications(?:\s+and\s+licenses)?|certificates|licenses)\b",
        re.IGNORECASE,
    ),
    "achievements": re.compile(
        r"^(?:honors(?:\s+and\s+awards)?|awards|achievements|key\s+achievements|accomplishments)\b",
        re.IGNORECASE,
    ),
}

# Accurate Skill Categorization Directory
SKILL_TAXONOMY: Dict[str, str] = {
    # Programming Languages
    "python": "programming_language",
    "c++": "programming_language",
    "c": "programming_language",
    "java": "programming_language",
    "javascript": "programming_language",
    "typescript": "programming_language",
    "go": "programming_language",
    "golang": "programming_language",
    "rust": "programming_language",
    "ruby": "programming_language",
    "php": "programming_language",
    "c#": "programming_language",
    "csharp": "programming_language",
    "scala": "programming_language",
    "kotlin": "programming_language",
    "swift": "programming_language",
    "html": "programming_language",
    "html5": "programming_language",
    "css": "programming_language",
    "css3": "programming_language",
    "sql": "database",

    # Frameworks
    "fastapi": "framework",
    "react": "framework",
    "next.js": "framework",
    "nextjs": "framework",
    "django": "framework",
    "flask": "framework",
    "express": "framework",
    "spring": "framework",
    "spring boot": "framework",
    "angular": "framework",
    "vue": "framework",
    "vue.js": "framework",
    "node.js": "framework",
    "nodejs": "framework",

    # Libraries
    "numpy": "library",
    "pandas": "library",
    "redux": "library",
    "tailwind css": "library",
    "tailwind": "library",
    "scipy": "library",
    "scikit-learn": "library",
    "matplotlib": "library",
    "bootstrap": "library",

    # Databases
    "postgresql": "database",
    "postgres": "database",
    "mysql": "database",
    "mongodb": "database",
    "redis": "database",
    "sqlite": "database",
    "oracle": "database",
    "cassandra": "database",
    "elasticsearch": "database",

    # Tools
    "git": "tool",
    "webpack": "tool",
    "vite": "tool",
    "postman": "tool",
    "jira": "tool",
    "vs code": "tool",
    "vscode": "tool",
    "npm": "tool",

    # Cloud
    "aws": "cloud",
    "gcp": "cloud",
    "azure": "cloud",
    "digitalocean": "cloud",
    "google cloud": "cloud",

    # DevOps
    "docker": "devops",
    "kubernetes": "devops",
    "k8s": "devops",
    "ci/cd": "devops",
    "terraform": "devops",
    "jenkins": "devops",
    "ansible": "devops",
    "linux": "devops",

    # AI / ML
    "machine learning": "ai_ml",
    "deep learning": "ai_ml",
    "pytorch": "ai_ml",
    "tensorflow": "ai_ml",
    "nlp": "ai_ml",
    "natural language processing": "ai_ml",
    "computer vision": "ai_ml",
    "keras": "ai_ml",

    # Soft Skills
    "communication": "soft_skill",
    "leadership": "soft_skill",
    "teamwork": "soft_skill",
    "problem solving": "soft_skill",
    "collaboration": "soft_skill",
    "mentorship": "soft_skill",

    # Other (Architectures, Protocols, Concepts)
    "rest apis": "other",
    "rest api": "other",
    "rest": "other",
    "microservices": "other",
    "graphql": "other",
    "agile": "other",
    "scrum": "other",
    "system design": "other",
    "oauth": "other",
    "unit testing": "other",
}


def extract_email(text: str) -> Optional[str]:
    """Find and return the first valid email address in text."""
    matches = EMAIL_REGEX.findall(text)
    if matches:
        return matches[0].strip().lower()
    return None


def extract_phone(text: str) -> Optional[str]:
    """Find and return the first valid phone number in text."""
    matches = PHONE_REGEX.findall(text)
    for match in matches:
        cleaned = match.strip()
        digits = re.sub(r"\D", "", cleaned)
        if 7 <= len(digits) <= 15:
            return cleaned
    return None


def extract_links(text: str) -> Dict[str, Optional[str]]:
    """Extract LinkedIn and GitHub profile URLs."""
    linkedin_match = LINKEDIN_REGEX.search(text)
    github_match = GITHUB_REGEX.search(text)
    return {
        "linkedin_url": linkedin_match.group(0).strip() if linkedin_match else None,
        "github_url": github_match.group(0).strip() if github_match else None,
    }


def extract_sections(text: str) -> Dict[str, str]:
    """
    Split resume text into sections based on recognized headings.
    Returns a dictionary mapping section keys to their corresponding text content.
    """
    lines = text.splitlines()
    detected_headers: List[Tuple[int, str]] = []

    for idx, line in enumerate(lines):
        stripped = line.strip().rstrip(":-_")
        if not stripped or len(stripped) > 50:
            continue

        for section_name, pattern in SECTION_PATTERNS.items():
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


def categorize_skill(skill_name: str) -> str:
    """Return the normalized category for a given skill name according to the system taxonomy."""
    cleaned = skill_name.strip().lower()
    return SKILL_TAXONOMY.get(cleaned, "other")


def parse_date_range(text: str) -> Tuple[Optional[str], Optional[str], bool]:
    """
    Extract start_date, end_date, and is_current flag from a date range string.
    Supports formats like '2019 - 2022', '2022 - Present', 'Jan 2019 – Mar 2022'.
    """
    is_current = bool(re.search(r"\b(present|current|now|ongoing)\b", text, re.I))

    # Match 4-digit years (optionally preceded by month names or abbreviations)
    date_pattern = re.compile(
        r"(?:(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+)?\b(19\d\d|20\d\d)\b",
        re.I,
    )

    matches = date_pattern.findall(text)
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    if matches:
        month0, year0 = matches[0]
        start_date = f"{month0} {year0}".strip() if month0 else year0
        if is_current:
            end_date = None
        elif len(matches) > 1:
            month1, year1 = matches[1]
            end_date = f"{month1} {year1}".strip() if month1 else year1
            # Sanity check: if both are pure years and end_date < start_date, fix inversion
            if year0.isdigit() and year1.isdigit() and int(year1) < int(year0):
                start_date, end_date = end_date, start_date

    return start_date, end_date, is_current


def parse_experience_blocks(experience_text: str) -> List[Dict[str, Any]]:
    """
    Robust rule-based segmentation of multiple experience entries.
    Identifies job boundaries using title/company delimiters and date ranges.
    """
    if not experience_text or not experience_text.strip():
        return []

    lines = [l.strip() for l in experience_text.splitlines() if l.strip()]
    if not lines:
        return []

    # Regex identifying position headers (e.g., 'Senior Engineer - CloudCorp (2022 - Present)')
    header_regex = re.compile(
        r"^(?P<title>[^-\|,\n]+?)\s*(?:-|at|@|\||,)\s*(?P<company>[^-\|,\(\n]+?)\s*(?:\((?P<parens_dates>[^)]+)\)|(?P<inline_dates>(?:19|20)\d\d.*))?$",
        re.I,
    )

    # Line index markers for start of each experience item
    entry_indices: List[int] = []
    for idx, line in enumerate(lines):
        # A line starting with bullet point is definitely description, not a header
        if line.startswith(("-", "*", "•", "–")):
            continue
        # Check if line contains a date range or matches title/company pattern
        has_dates = bool(re.search(r"\b(19\d\d|20\d\d)\s*[-–]\s*(19\d\d|20\d\d|present|current)\b", line, re.I))
        has_delim = bool(re.search(r"(\s+-\s+|\s+at\s+|\s+\|\s+)", line, re.I))
        if has_dates or (has_delim and idx == 0) or (has_delim and lines[idx - 1].startswith(("-", "*", "•"))):
            entry_indices.append(idx)

    # If no delimiter pattern caught, fall back to blank-line or first line
    if not entry_indices:
        entry_indices = [0]

    experiences: List[Dict[str, Any]] = []
    for i in range(len(entry_indices)):
        start_idx = entry_indices[i]
        end_idx = entry_indices[i + 1] if i + 1 < len(entry_indices) else len(lines)
        block_lines = lines[start_idx:end_idx]

        header_line = block_lines[0]
        desc_lines = block_lines[1:]

        title = "Software Engineer"
        company = None
        dates_text = ""

        # Try parsing header line
        m = header_regex.match(header_line)
        if m:
            t = m.group("title").strip()
            c = m.group("company").strip()
            dates_text = m.group("parens_dates") or m.group("inline_dates") or ""
            if t:
                title = t
            if c:
                company = c
        else:
            # Fallback delimiters
            parts = re.split(r"\s+[-–|]\s+", header_line)
            if len(parts) >= 2:
                title = parts[0].strip()
                company_and_dates = parts[1].strip()
                date_m = re.search(r"\(?((?:19|20)\d\d.*)\)?", company_and_dates)
                if date_m:
                    dates_text = date_m.group(1)
                    company = company_and_dates[: date_m.start()].strip().rstrip("(- ")
                else:
                    company = company_and_dates
            else:
                title = header_line

        # If company not found on header line, check next line if not a bullet
        if not company and desc_lines and not desc_lines[0].startswith(("-", "*", "•")):
            company = desc_lines.pop(0)

        # If dates not found in header, scan block lines
        if not dates_text:
            for l in block_lines:
                if re.search(r"\b(19\d\d|20\d\d)\b", l):
                    dates_text = l
                    break

        start_date, end_date, is_current = parse_date_range(dates_text or header_line)

        # Clean description: filter out date lines or company repeats
        clean_desc_lines = []
        for l in desc_lines:
            if l == dates_text or l == company:
                continue
            clean_desc_lines.append(l.lstrip("-*• ").strip())

        description = " ".join(clean_desc_lines) if clean_desc_lines else None

        # Extract skills mentioned in this experience block
        skills_in_block = []
        block_text_corpus = " ".join(block_lines)
        for s_name in SKILL_TAXONOMY.keys():
            if len(s_name) > 2 and re.search(r"\b" + re.escape(s_name) + r"\b", block_text_corpus, re.I):
                canonical = s_name.title() if not s_name.isupper() else s_name
                if canonical not in skills_in_block:
                    skills_in_block.append(canonical)

        # Make sure company never contains bullet points or long descriptions
        if company and (company.startswith(("-", "*", "•")) or len(company) > 60):
            company = None

        experiences.append({
            "title": title,
            "company": company,
            "location": None,
            "start_date": start_date,
            "end_date": end_date,
            "is_current": is_current,
            "description": description,
            "skills": skills_in_block[:5],
        })

    return experiences


def parse_education_blocks(education_text: str) -> List[Dict[str, Any]]:
    """
    Robust extraction of degree, institution, field of study, and years.
    Handles multi-line, dash-delimited, and comma-delimited education formats.
    """
    if not education_text or not education_text.strip():
        return []

    lines = [l.strip() for l in education_text.splitlines() if l.strip()]
    if not lines:
        return []

    degree_pattern = re.compile(
        r"\b(B\.?Tech(?:nology)?|Bachelor(?:\s+of\s+[A-Za-z]+)?|B\.?S\.|B\.?S\b|B\.?A\.|B\.?A\b|M\.?Tech|Master(?:\s+of\s+[A-Za-z]+)?|M\.?S\.|M\.?S\b|Ph\.?D\.|Ph\.?D\b|Diploma\b)",
        re.I,
    )

    field_pattern = re.compile(
        r"(?:in\s+|,\s*|—\s*|\s*-\s*)([A-Za-z\s]+?(?:Engineering|Science|Technology|Mathematics|Studies|Arts|Business))",
        re.I,
    )

    edu_items: List[Dict[str, Any]] = []

    # If lines clearly represent separate educational qualifications (e.g. B.S. and M.S.)
    edu_line_groups: List[List[str]] = []
    current_group: List[str] = []

    for line in lines:
        if degree_pattern.search(line) and current_group:
            edu_line_groups.append(current_group)
            current_group = [line]
        else:
            current_group.append(line)
    if current_group:
        edu_line_groups.append(current_group)

    for group in edu_line_groups:
        full_block = " — ".join(group)
        clean_block = re.sub(r"\s*\(\s*\d{4}\s*[-–]\s*(?:\d{4}|present)\s*\)", "", full_block, flags=re.I)
        clean_block = re.sub(r"\s*\(\s*\d{4}\s*\)", "", clean_block)

        degree = None
        field = None
        institution = None
        grade = None

        # Degree
        deg_m = degree_pattern.search(clean_block)
        if deg_m:
            degree = deg_m.group(0).strip()

        # Field of study (e.g. 'in Computer Science', 'in Artificial Intelligence')
        field_m = re.search(r"\bin\s+([^—\n,-]+?)(?=\s*[-–—,]|\s+(?:from|at)\s+|\s*\(\d{4}|$)", clean_block, re.I)
        if field_m:
            f_cand = field_m.group(1).strip()
            if not any(k in f_cand.lower() for k in ["university", "college", "institute", "school"]):
                field = f_cand

        # Years
        years = re.findall(r"\b(19\d\d|20\d\d)\b", full_block)
        start_year = int(years[0]) if len(years) >= 2 else None
        end_year = int(years[1]) if len(years) >= 2 else (int(years[0]) if len(years) == 1 else None)
        if start_year and end_year and end_year < start_year:
            start_year, end_year = end_year, start_year

        # Institution: find line or token containing University/College/Institute
        inst_pattern = re.compile(r"([^—\n,-]+?(?:University|College|Institute|School|Academy)[^—\n,-]*)", re.I)
        inst_m = inst_pattern.search(clean_block)
        if inst_m:
            institution = inst_m.group(1).strip()
        elif len(group) >= 2:
            cand_line = group[1].strip()
            if not re.search(r"^\b(19|20)\d\d\b", cand_line):
                institution = cand_line

        # Clean institution so it never contains degree, field, or lingering dates/parentheses
        if institution and degree:
            institution = re.sub(re.escape(degree), "", institution, flags=re.I).strip(" -—,")
        if institution and field:
            institution = re.sub(re.escape(field), "", institution, flags=re.I).strip(" -—,in ")
        if institution:
            institution = re.sub(r"[\(\[\{].*?[\)\]\}]", "", institution).strip(" -—,")

        # Grade / GPA
        grade_m = re.search(r"\b(GPA:\s*[\d.]+(?:/\d\.\d)?|CGPA:\s*[\d.]+(?:/\d+)?|Grade:\s*[A-Za-z0-9.+]+)\b", full_block, re.I)
        if grade_m:
            grade = grade_m.group(0).strip()

        edu_items.append({
            "degree": degree,
            "institution": institution,
            "field": field,
            "start_year": start_year,
            "end_year": end_year,
            "grade": grade,
        })

    return edu_items


def parse_project_blocks(projects_text: str) -> List[Dict[str, Any]]:
    """
    Robust extraction of project name, description, and technologies.
    Guarantees project name is separate from description.
    """
    if not projects_text or not projects_text.strip():
        return []

    lines = [l.strip() for l in projects_text.splitlines() if l.strip()]
    if not lines:
        return []

    projects: List[Dict[str, Any]] = []
    current_proj: Optional[Dict[str, Any]] = None

    for line in lines:
        stripped_line = line.lstrip("-*• \t").strip()
        colon_split = re.split(r":\s+", stripped_line, maxsplit=1)
        dash_split = re.split(r"\s+[-–—]\s+", stripped_line, maxsplit=1)

        is_new_proj = False
        name = ""
        desc = None

        if len(colon_split) == 2 and not stripped_line.lower().startswith(("technologies:", "tools:", "tech stack:", "github:", "url:")):
            name = colon_split[0].strip()
            desc = colon_split[1].strip()
            is_new_proj = True
        elif len(dash_split) == 2 and not stripped_line.lower().startswith(("technologies", "tools", "tech stack")):
            name = dash_split[0].strip()
            desc = dash_split[1].strip()
            is_new_proj = True
        elif len(stripped_line.split()) <= 6 and not stripped_line.lower().startswith(("technologies", "tools", "built with")):
            name = stripped_line
            desc = None
            is_new_proj = True

        if is_new_proj and name:
            if current_proj:
                projects.append(current_proj)
            current_proj = {
                "name": name,
                "description": desc,
                "technologies": [],
                "url": None,
                "start_date": None,
                "end_date": None,
            }
        elif current_proj:
            # Check for technologies line
            tech_m = re.search(r"(?:Technologies|Tech Stack|Tools|Built with):\s*(.*)", line, re.I)
            if tech_m:
                tech_str = tech_m.group(1)
                found_techs = [t.strip() for t in re.split(r"[,|;]", tech_str) if t.strip()]
                current_proj["technologies"].extend(found_techs)
            else:
                # Append to description
                clean_l = line.lstrip("-*• ").strip()
                if current_proj["description"]:
                    current_proj["description"] += " " + clean_l
                else:
                    current_proj["description"] = clean_l

    if current_proj:
        projects.append(current_proj)

    # Extract technologies from description if not explicitly found
    for p in projects:
        if not p["technologies"] and p.get("description"):
            for s_name in SKILL_TAXONOMY.keys():
                if len(s_name) > 2 and re.search(r"\b" + re.escape(s_name) + r"\b", p["description"], re.I):
                    canonical = s_name.title() if not s_name.isupper() else s_name
                    if canonical not in p["technologies"]:
                        p["technologies"].append(canonical)

    return projects
