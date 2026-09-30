import re
from typing import Optional, Dict, List, Tuple


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
        # Ensure it contains at least 7 digits and no invalid character repetitions
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
        # If no explicit headings detected, return entire body under 'content'
        sections["content"] = text
        return sections

    # Capture header intro/contact info before first heading
    if detected_headers[0][0] > 0:
        intro_lines = lines[:detected_headers[0][0]]
        sections["header"] = "\n".join(intro_lines).strip()

    # Slice between detected headers
    for i in range(len(detected_headers)):
        start_idx, sec_name = detected_headers[i]
        end_idx = detected_headers[i + 1][0] if i + 1 < len(detected_headers) else len(lines)
        section_content = lines[start_idx + 1 : end_idx]
        sections[sec_name] = "\n".join(section_content).strip()

    return sections
