"""
Centralized Canonical Skill Registry and Taxonomy for P_101 Resume Screening System.

Provides the single source of truth for:
- Canonical skill representations
- Category mappings (strictly mapped to VALID_SKILL_CATEGORIES)
- Known aliases, abbreviations, and case/formatting variants
- Protection against false-positive generic words
- Controlled version stripping
"""

import re
from typing import Dict, List, Optional, Tuple, Set, Any
from backend.app.schemas import VALID_SKILL_CATEGORIES

# ---------------------------------------------------------------------------
# False-Positive Words Protection (Section 11)
# Ordinary resume/JD words that must NOT be converted into canonical skills.
# ---------------------------------------------------------------------------
FALSE_POSITIVE_WORDS: Set[str] = {
    "experience",
    "work",
    "team",
    "development",
    "data",
    "model",
    "code",
    "skills",
    "years",
    "knowledge",
    "proficient",
    "requirements",
    "responsibilities",
    "qualification",
    "qualifications",
    "working",
    "using",
    "plus",
    "bonus",
    "role",
    "support",
    "building",
    "engineer",
    "developer",
    "candidate",
    "expert",
    "expertise",
    "good",
    "strong",
    "hands-on",
    "handson",
}

# ---------------------------------------------------------------------------
# Canonical Skill Registry (Section 6 & 7)
# Structured mapping of Canonical Name -> {category, aliases, description}
# ---------------------------------------------------------------------------
CANONICAL_SKILL_REGISTRY: Dict[str, Dict[str, Any]] = {
    # ---------------------------------------------------------
    # Programming Languages
    # ---------------------------------------------------------
    "Python": {
        "category": "programming_language",
        "aliases": ["python", "py", "python3", "python 3", "python2", "python 2"],
    },
    "JavaScript": {
        "category": "programming_language",
        "aliases": [
            "javascript",
            "js",
            "ecmascript",
            "es6",
            "es2015",
            "es2016",
            "es2020",
            "vanilla js",
            "vanilla javascript",
        ],
    },
    "TypeScript": {
        "category": "programming_language",
        "aliases": ["typescript", "ts"],
    },
    "Java": {
        "category": "programming_language",
        "aliases": ["java", "core java", "java se", "java ee", "java 8", "java 11", "java 17", "java 21"],
    },
    "C": {
        "category": "programming_language",
        "aliases": ["c", "c language", "c lang", "ansi c"],
    },
    "C++": {
        "category": "programming_language",
        "aliases": ["c++", "cpp", "cplusplus", "c ++", "modern c++"],
    },
    "C#": {
        "category": "programming_language",
        "aliases": ["c#", "csharp", "c-sharp", "c #"],
    },
    "Go": {
        "category": "programming_language",
        "aliases": ["go", "golang"],
    },
    "Rust": {
        "category": "programming_language",
        "aliases": ["rust", "rustlang"],
    },
    "SQL": {
        "category": "programming_language",
        "aliases": ["sql", "structured query language", "ansi sql", "t-sql", "pl/sql", "plsql"],
    },
    "HTML": {
        "category": "programming_language",
        "aliases": ["html", "html5", "html 5"],
    },
    "CSS": {
        "category": "programming_language",
        "aliases": ["css", "css3", "css 3"],
    },
    "PHP": {
        "category": "programming_language",
        "aliases": ["php", "php7", "php8"],
    },
    "Ruby": {
        "category": "programming_language",
        "aliases": ["ruby"],
    },
    "Kotlin": {
        "category": "programming_language",
        "aliases": ["kotlin"],
    },
    "Swift": {
        "category": "programming_language",
        "aliases": ["swift"],
    },
    "Scala": {
        "category": "programming_language",
        "aliases": ["scala"],
    },
    "R": {
        "category": "programming_language",
        "aliases": ["r", "r language", "r-project"],
    },
    "Bash": {
        "category": "programming_language",
        "aliases": ["bash", "shell", "shell script", "shell scripting", "bash scripting", "sh"],
    },
    "Dart": {
        "category": "programming_language",
        "aliases": ["dart"],
    },

    # ---------------------------------------------------------
    # Frameworks
    # ---------------------------------------------------------
    "FastAPI": {
        "category": "framework",
        "aliases": ["fastapi", "fast api", "fast-api"],
    },
    "Django": {
        "category": "framework",
        "aliases": ["django", "django rest framework", "drf"],
    },
    "Flask": {
        "category": "framework",
        "aliases": ["flask"],
    },
    "React": {
        "category": "framework",
        "aliases": ["react", "reactjs", "react.js", "react js"],
    },
    "Next.js": {
        "category": "framework",
        "aliases": ["next.js", "nextjs", "next js", "next"],
    },
    "Angular": {
        "category": "framework",
        "aliases": ["angular", "angularjs", "angular.js", "angular 2+"],
    },
    "Vue.js": {
        "category": "framework",
        "aliases": ["vue", "vue.js", "vuejs", "vue js"],
    },
    "Spring": {
        "category": "framework",
        "aliases": ["spring", "spring boot", "springboot", "spring framework", "spring mvc"],
    },
    "Express.js": {
        "category": "framework",
        "aliases": ["express", "express.js", "expressjs", "express js"],
    },
    ".NET": {
        "category": "framework",
        "aliases": [".net", "dotnet", ".net framework", ".net core", "asp.net", "asp.net core"],
    },
    "Node.js": {
        "category": "framework",
        "aliases": ["node.js", "nodejs", "node js", "node"],
    },
    "Tailwind CSS": {
        "category": "framework",
        "aliases": ["tailwind", "tailwindcss", "tailwind css"],
    },
    "Bootstrap": {
        "category": "framework",
        "aliases": ["bootstrap", "bootstrap 5"],
    },
    "Ruby on Rails": {
        "category": "framework",
        "aliases": ["ruby on rails", "rails", "ror"],
    },
    "Flutter": {
        "category": "framework",
        "aliases": ["flutter"],
    },

    # ---------------------------------------------------------
    # Libraries
    # ---------------------------------------------------------
    "NumPy": {
        "category": "library",
        "aliases": ["numpy", "np"],
    },
    "Pandas": {
        "category": "library",
        "aliases": ["pandas", "pd"],
    },
    "Scikit-Learn": {
        "category": "library",
        "aliases": ["scikit-learn", "scikit learn", "scikitlearn", "sklearn"],
    },
    "TensorFlow": {
        "category": "library",
        "aliases": ["tensorflow", "tf"],
    },
    "PyTorch": {
        "category": "library",
        "aliases": ["pytorch", "torch"],
    },
    "Keras": {
        "category": "library",
        "aliases": ["keras"],
    },
    "Redux": {
        "category": "library",
        "aliases": ["redux", "redux toolkit", "rtk"],
    },
    "Jest": {
        "category": "library",
        "aliases": ["jest"],
    },
    "Celery": {
        "category": "library",
        "aliases": ["celery"],
    },
    "SQLAlchemy": {
        "category": "library",
        "aliases": ["sqlalchemy"],
    },
    "Pydantic": {
        "category": "library",
        "aliases": ["pydantic"],
    },
    "OpenCV": {
        "category": "library",
        "aliases": ["opencv", "cv2"],
    },

    # ---------------------------------------------------------
    # Databases
    # ---------------------------------------------------------
    "PostgreSQL": {
        "category": "database",
        "aliases": ["postgresql", "postgres", "postgres db", "pgsql", "psql"],
    },
    "MySQL": {
        "category": "database",
        "aliases": ["mysql", "my sql"],
    },
    "MongoDB": {
        "category": "database",
        "aliases": ["mongodb", "mongo", "mongo db"],
    },
    "Redis": {
        "category": "database",
        "aliases": ["redis"],
    },
    "SQLite": {
        "category": "database",
        "aliases": ["sqlite", "sqlite3"],
    },
    "Elasticsearch": {
        "category": "database",
        "aliases": ["elasticsearch", "elastic search", "elastic"],
    },
    "Cassandra": {
        "category": "database",
        "aliases": ["cassandra", "apache cassandra"],
    },
    "DynamoDB": {
        "category": "database",
        "aliases": ["dynamodb", "dynamo db", "aws dynamodb"],
    },

    # ---------------------------------------------------------
    # Tools
    # ---------------------------------------------------------
    "Git": {
        "category": "tool",
        "aliases": ["git", "version control", "vcs"],
    },
    "GitHub": {
        "category": "tool",
        "aliases": ["github"],
    },
    "GitLab": {
        "category": "tool",
        "aliases": ["gitlab"],
    },
    "VS Code": {
        "category": "tool",
        "aliases": ["vs code", "vscode", "visual studio code"],
    },
    "Postman": {
        "category": "tool",
        "aliases": ["postman"],
    },
    "Jira": {
        "category": "tool",
        "aliases": ["jira", "atlassian jira"],
    },
    "Linux": {
        "category": "tool",
        "aliases": ["linux", "unix", "ubuntu", "debian", "centos", "rhel"],
    },
    "Webpack": {
        "category": "tool",
        "aliases": ["webpack"],
    },
    "Vite": {
        "category": "tool",
        "aliases": ["vite", "vitejs"],
    },

    # ---------------------------------------------------------
    # Cloud
    # ---------------------------------------------------------
    "AWS": {
        "category": "cloud",
        "aliases": ["aws", "amazon web services", "amazon cloud"],
    },
    "Azure": {
        "category": "cloud",
        "aliases": ["azure", "microsoft azure"],
    },
    "Google Cloud": {
        "category": "cloud",
        "aliases": ["gcp", "google cloud", "google cloud platform"],
    },

    # ---------------------------------------------------------
    # DevOps
    # ---------------------------------------------------------
    "Docker": {
        "category": "devops",
        "aliases": ["docker", "docker containers", "containerization"],
    },
    "Kubernetes": {
        "category": "devops",
        "aliases": ["kubernetes", "k8s", "k8"],
    },
    "Jenkins": {
        "category": "devops",
        "aliases": ["jenkins"],
    },
    "Terraform": {
        "category": "devops",
        "aliases": ["terraform"],
    },
    "CI/CD": {
        "category": "devops",
        "aliases": ["ci/cd", "ci cd", "cicd", "continuous integration", "continuous deployment"],
    },
    "Ansible": {
        "category": "devops",
        "aliases": ["ansible"],
    },

    # ---------------------------------------------------------
    # AI / ML
    # ---------------------------------------------------------
    "Machine Learning": {
        "category": "ai_ml",
        "aliases": ["machine learning", "ml"],
    },
    "Deep Learning": {
        "category": "ai_ml",
        "aliases": ["deep learning", "dl"],
    },
    "Natural Language Processing": {
        "category": "ai_ml",
        "aliases": ["natural language processing", "nlp"],
    },
    "Generative AI": {
        "category": "ai_ml",
        "aliases": ["generative ai", "genai", "gen ai"],
    },
    "Large Language Models": {
        "category": "ai_ml",
        "aliases": ["llm", "large language models", "large language model", "llms"],
    },
    "Computer Vision": {
        "category": "ai_ml",
        "aliases": ["computer vision", "cv"],
    },

    # ---------------------------------------------------------
    # Other / Architectural Concepts
    # ---------------------------------------------------------
    "REST APIs": {
        "category": "other",
        "aliases": ["rest apis", "rest api", "rest", "restful", "restful apis", "restful api"],
    },
    "GraphQL": {
        "category": "other",
        "aliases": ["graphql"],
    },
    "Microservices": {
        "category": "other",
        "aliases": ["microservices", "microservice", "microservice architecture", "micro-services"],
    },
    "System Design": {
        "category": "other",
        "aliases": ["system design", "distributed systems"],
    },
    "Data Structures": {
        "category": "other",
        "aliases": ["data structures", "dsa", "data structures and algorithms", "data structures & algorithms"],
    },
    "Algorithms": {
        "category": "other",
        "aliases": ["algorithms"],
    },
    "Agile": {
        "category": "other",
        "aliases": ["agile", "scrum", "kanban", "agile methodology", "agile development"],
    },

    # ---------------------------------------------------------
    # Soft Skills
    # ---------------------------------------------------------
    "Communication": {
        "category": "soft_skill",
        "aliases": ["communication", "written communication", "verbal communication"],
    },
    "Leadership": {
        "category": "soft_skill",
        "aliases": ["leadership", "team leadership"],
    },
    "Teamwork": {
        "category": "soft_skill",
        "aliases": ["teamwork", "collaboration", "cross-functional collaboration", "team player"],
    },
    "Problem Solving": {
        "category": "soft_skill",
        "aliases": ["problem solving", "problem-solving", "analytical thinking", "critical thinking"],
    },
    "Mentorship": {
        "category": "soft_skill",
        "aliases": ["mentorship", "mentoring", "coaching"],
    },
}

# ---------------------------------------------------------------------------
# Fast Lookup Inverted Indexes
# ---------------------------------------------------------------------------
_EXACT_NAME_LOOKUP: Dict[str, str] = {}
_ALIAS_LOOKUP: Dict[str, str] = {}

for canonical, meta in CANONICAL_SKILL_REGISTRY.items():
    _EXACT_NAME_LOOKUP[canonical.lower()] = canonical
    for alias in meta.get("aliases", []):
        _ALIAS_LOOKUP[alias.strip().lower()] = canonical

# Regex for stripping version numbers like "Python 3", "Python 3.11", "React 18", "Postgres 14", "Vue 3"
# Handles numbers, decimals, and plus signs (e.g. 2+)
_VERSION_SUFFIX_PATTERN = re.compile(
    r"^(.*?)(?:\s+(?:v|version\s*)?(\d+(?:\.\d+)*(?:\.x)?|\d+\+))(?:\s+.*)?$",
    re.I,
)


def lookup_canonical_skill(name: str) -> Optional[Tuple[str, str, str]]:
    """
    Deterministic lookup of a skill name in the canonical registry.

    Returns:
        (canonical_name, category, normalization_method) or None if not found.
    """
    if not name or not isinstance(name, str):
        return None

    cleaned = name.strip()
    if not cleaned:
        return None

    lowered = cleaned.lower()

    # Step 1: Reject ordinary false-positive words if appearing alone
    if lowered in FALSE_POSITIVE_WORDS:
        return None

    # Step 2: Exact canonical match (case-sensitive)
    if cleaned in CANONICAL_SKILL_REGISTRY:
        meta = CANONICAL_SKILL_REGISTRY[cleaned]
        return (cleaned, meta["category"], "exact")

    # Step 3: Exact canonical match (case-insensitive)
    if lowered in _EXACT_NAME_LOOKUP:
        canonical = _EXACT_NAME_LOOKUP[lowered]
        meta = CANONICAL_SKILL_REGISTRY[canonical]
        return (canonical, meta["category"], "case_normalized")

    # Step 4: Registered alias lookup
    if lowered in _ALIAS_LOOKUP:
        canonical = _ALIAS_LOOKUP[lowered]
        meta = CANONICAL_SKILL_REGISTRY[canonical]
        return (canonical, meta["category"], "alias")

    # Step 5: Safe punctuation spacing normalization (e.g., "c ++" -> "c++", "c #" -> "c#")
    spaced_punct = re.sub(r"\s+([+#])", r"\1", lowered)
    if spaced_punct != lowered and spaced_punct in _ALIAS_LOOKUP:
        canonical = _ALIAS_LOOKUP[spaced_punct]
        meta = CANONICAL_SKILL_REGISTRY[canonical]
        return (canonical, meta["category"], "alias")

    # Step 6: Controlled version stripping
    # Only if base is unambiguous and matches a known canonical skill/alias
    v_match = _VERSION_SUFFIX_PATTERN.match(cleaned)
    if v_match:
        base_cand = v_match.group(1).strip().lower()
        if base_cand in _EXACT_NAME_LOOKUP:
            canonical = _EXACT_NAME_LOOKUP[base_cand]
            meta = CANONICAL_SKILL_REGISTRY[canonical]
            return (canonical, meta["category"], "version_stripped")
        if base_cand in _ALIAS_LOOKUP:
            canonical = _ALIAS_LOOKUP[base_cand]
            meta = CANONICAL_SKILL_REGISTRY[canonical]
            return (canonical, meta["category"], "version_stripped")

    return None


def get_all_canonical_skills() -> Dict[str, Dict[str, Any]]:
    """Return a copy of the canonical skill registry."""
    return {k: dict(v) for k, v in CANONICAL_SKILL_REGISTRY.items()}


def get_taxonomy_categories() -> List[str]:
    """Return the list of valid skill taxonomy categories."""
    return sorted(list(VALID_SKILL_CATEGORIES))
