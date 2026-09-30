import re
from enum import Enum
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ---------------------------------------------------------
# Health Check Schema
# ---------------------------------------------------------
class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    environment: str
    llm_provider: str


# ---------------------------------------------------------
# Document Parsing Schema (Phase 2)
# ---------------------------------------------------------
class DocumentParseResponse(BaseModel):
    filename: str
    file_type: str
    page_count: int
    character_count: int
    word_count: int
    text: str



# ---------------------------------------------------------
# Scoring Configuration Schema
# ---------------------------------------------------------
class ScoringWeights(BaseModel):
    rule_fit: float = Field(default=0.30, ge=0.0, le=1.0)
    semantic_fit: float = Field(default=0.40, ge=0.0, le=1.0)
    experience_fit: float = Field(default=0.20, ge=0.0, le=1.0)
    llm_fit: float = Field(default=0.10, ge=0.0, le=1.0)


# ---------------------------------------------------------
# Requirement Schemas
# ---------------------------------------------------------
class RequirementBase(BaseModel):
    requirement_text: str
    type: str = Field(default="mandatory", description="'mandatory' or 'preferred'")
    importance: str = Field(default="high", description="'high', 'medium', or 'low'")
    category: str = Field(default="skill", description="'skill', 'experience', 'education'")


class RequirementCreate(RequirementBase):
    pass


class RequirementResponse(RequirementBase):
    id: int
    job_id: int

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Job Schemas
# ---------------------------------------------------------
class JobBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    jd_text: str = Field(..., min_length=10)


class JobCreate(JobBase):
    weights: Optional[ScoringWeights] = None


class JobUpdateRequirements(BaseModel):
    requirements: List[RequirementCreate]


class JobResponse(JobBase):
    id: int
    requirements_json: Optional[Dict[str, Any]] = None
    weights_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    requirements: List[RequirementResponse] = []
    candidate_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Candidate Profile Schemas (Phase 3)
# ---------------------------------------------------------
class PersonalInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip().lower()
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, v):
            raise ValueError(f"Invalid email address format: '{v}'")
        return v

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone_format(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        return str(v).strip()


VALID_SKILL_CATEGORIES = {
    "programming_language",
    "framework",
    "library",
    "database",
    "tool",
    "cloud",
    "devops",
    "ai_ml",
    "soft_skill",
    "other",
}


class SkillItem(BaseModel):
    name: str
    category: Optional[str] = Field(
        default="other",
        description="programming_language, framework, library, database, tool, cloud, devops, ai_ml, soft_skill, other",
    )

    @field_validator("category", mode="before")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> str:
        if not v:
            return "other"
        cleaned = str(v).strip().lower()
        return cleaned if cleaned in VALID_SKILL_CATEGORIES else "other"


class EducationItem(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    field: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    grade: Optional[str] = None


class ExperienceItem(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    description: Optional[str] = None
    skills: List[str] = []

    @field_validator("company", mode="before")
    @classmethod
    def sanitize_company(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        cleaned = str(v).strip()
        if cleaned.startswith(("-", "*", "•", "–")) or len(cleaned) > 80:
            return None
        return cleaned


class ProjectItem(BaseModel):
    name: str
    description: Optional[str] = None
    technologies: List[str] = []
    url: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class CertificationItem(BaseModel):
    name: str
    issuing_organization: Optional[str] = None
    issue_date: Optional[str] = None
    credential_id: Optional[str] = None
    url: Optional[str] = None


class AchievementItem(BaseModel):
    title: str
    description: Optional[str] = None
    date: Optional[str] = None


# ---------------------------------------------------------
# Skill Normalization Schemas (Phase 5)
# ---------------------------------------------------------
RequirementPriority = Literal["must_have", "nice_to_have"]


class NormalizationMethod(str, Enum):
    EXACT = "exact"
    CASE_NORMALIZED = "case_normalized"
    ALIAS = "alias"
    VERSION_STRIPPED = "version_stripped"
    UNKNOWN = "unknown"


class NormalizedSkill(BaseModel):
    """Canonical representation of an extracted candidate skill with provenance."""
    canonical_name: str = Field(..., description="Standardized canonical skill name from taxonomy")
    original_name: str = Field(..., description="First or primary original skill string extracted")
    original_names: List[str] = Field(default_factory=list, description="All original text variants merged into this canonical skill")
    category: str = Field(default="other", description="Standardized category from VALID_SKILL_CATEGORIES")
    normalization_method: str = Field(default="exact", description="'exact', 'case_normalized', 'alias', 'version_stripped', 'unknown'")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score of normalization (1.0 for registry match, 0.5 for unknown)")
    source: Optional[str] = Field(default="resume", description="'resume', 'job_description', or other provenance")

    @field_validator("category", mode="before")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> str:
        if not v:
            return "other"
        cleaned = str(v).strip().lower()
        return cleaned if cleaned in VALID_SKILL_CATEGORIES else "other"


class NormalizedJobSkill(BaseModel):
    """Canonical representation of an extracted job skill requirement with priority and provenance."""
    canonical_name: str = Field(..., description="Standardized canonical skill name from taxonomy")
    original_name: str = Field(..., description="First or primary original skill string extracted from JD")
    original_names: List[str] = Field(default_factory=list, description="All original text variants from JD merged into this canonical requirement")
    category: str = Field(default="other", description="Standardized category from VALID_SKILL_CATEGORIES")
    priority: RequirementPriority = Field(default="must_have", description="'must_have' or 'nice_to_have'")
    minimum_years: Optional[float] = Field(default=None, ge=0.0, description="Minimum required years if specified in JD")
    evidence: Optional[str] = Field(default=None, description="Exact phrase or sentence from the JD")
    normalization_method: str = Field(default="exact", description="'exact', 'case_normalized', 'alias', 'version_stripped', 'unknown'")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score of normalization")
    source: Optional[str] = Field(default="job_description", description="Provenance indicator")

    @field_validator("category", mode="before")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> str:
        if not v:
            return "other"
        cleaned = str(v).strip().lower()
        return cleaned if cleaned in VALID_SKILL_CATEGORIES else "other"

    @field_validator("priority", mode="before")
    @classmethod
    def validate_priority(cls, v: Any) -> str:
        if not v:
            return "must_have"
        cleaned = str(v).strip().lower().replace("-", "_")
        if any(w in cleaned for w in ["preferred", "nice", "bonus", "plus", "optional", "desired", "good_to_have"]):
            return "nice_to_have"
        return "must_have"


class SkillNormalizeRequest(BaseModel):
    skills: List[str] = Field(..., min_length=1, description="List of raw skill strings to normalize")
    source: Optional[str] = Field(default="manual", description="Source/provenance of skills")


class SkillNormalizeResponse(BaseModel):
    count: int
    normalized_skills: List[NormalizedSkill]


class CandidateProfile(BaseModel):
    personal_info: PersonalInfo = Field(default_factory=PersonalInfo)
    summary: Optional[str] = None
    skills: List[SkillItem] = []
    normalized_skills: List[NormalizedSkill] = []
    education: List[EducationItem] = []
    experience: List[ExperienceItem] = []
    projects: List[ProjectItem] = []
    certifications: List[CertificationItem] = []
    achievements: List[AchievementItem] = []


class ResumeExtractionResponse(BaseModel):
    filename: str
    file_type: str
    profile: CandidateProfile
    extraction_metadata: Optional[Dict[str, Any]] = None


class ProfileBase(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: Optional[List[Any]] = []
    experience: Optional[List[Dict[str, Any]]] = []
    education: Optional[List[Dict[str, Any]]] = []
    projects: Optional[List[Dict[str, Any]]] = []
    certifications: Optional[List[str]] = []
    achievements: Optional[List[str]] = []


class ProfileResponse(ProfileBase):
    id: int
    candidate_id: int

    model_config = ConfigDict(from_attributes=True)



# ---------------------------------------------------------
# Score & Gap Schemas
# ---------------------------------------------------------
class ScoreResponse(BaseModel):
    rule_score: float
    semantic_score: float
    experience_score: float
    llm_score: float
    total_score: float
    score_breakdown: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class SkillGapResponse(BaseModel):
    id: int
    skill: str
    status: str  # 'matched', 'partial', 'missing'
    importance: str  # 'high', 'medium', 'low'
    evidence: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RecommendationResponse(BaseModel):
    id: int
    skill: Optional[str] = None
    recommendation: str
    learning_direction: Optional[str] = None
    suggested_project: Optional[str] = None
    priority: str

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Candidate Schemas
# ---------------------------------------------------------
class CandidateRankingItem(BaseModel):
    id: int
    job_id: int
    display_id: str
    masked: bool
    total_score: float
    rule_score: float
    semantic_score: float
    experience_score: float
    llm_score: float
    top_matched_skills: List[str] = []
    top_skill_gaps: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class CandidateDetailResponse(BaseModel):
    id: int
    job_id: int
    display_id: str
    masked: bool
    created_at: datetime
    profile: Optional[ProfileResponse] = None
    score: Optional[ScoreResponse] = None
    skill_gaps: List[SkillGapResponse] = []
    recommendations: List[RecommendationResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Job Description & Requirements Schemas (Phase 4)
# ---------------------------------------------------------

RequirementType = Literal[
    "skill",
    "experience",
    "education",
    "certification",
    "location",
    "language",
    "responsibility",
    "other",
]


class JobSkillRequirement(BaseModel):
    name: str = Field(..., description="Canonical or explicit skill name")
    category: Optional[str] = Field(
        default="other",
        description="programming_language, framework, library, database, tool, cloud, devops, ai_ml, soft_skill, other",
    )
    priority: RequirementPriority = Field(
        default="must_have",
        description="'must_have' (mandatory) or 'nice_to_have' (preferred)",
    )
    minimum_years: Optional[float] = Field(
        default=None, description="Minimum years of experience required for this skill if specified"
    )
    evidence: Optional[str] = Field(
        default=None, description="Exact phrase or sentence from the JD mentioning this skill requirement"
    )

    @field_validator("category", mode="before")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> str:
        if not v:
            return "other"
        cleaned = str(v).strip().lower()
        return cleaned if cleaned in VALID_SKILL_CATEGORIES else "other"

    @field_validator("priority", mode="before")
    @classmethod
    def validate_priority(cls, v: Any) -> str:
        if not v:
            return "must_have"
        cleaned = str(v).strip().lower().replace("-", "_")
        if any(w in cleaned for w in ["preferred", "nice", "bonus", "plus", "optional", "desired", "good_to_have"]):
            return "nice_to_have"
        return "must_have"


class JobExperienceRequirement(BaseModel):
    skill: Optional[str] = Field(
        default=None, description="Specific skill if tied to experience, or null for general experience"
    )
    minimum_years: Optional[float] = Field(
        default=None, ge=0.0, description="Minimum required years of experience"
    )
    maximum_years: Optional[float] = Field(
        default=None, ge=0.0, description="Maximum experience years if bounded (e.g. 2-4 years)"
    )
    priority: RequirementPriority = Field(
        default="must_have", description="'must_have' or 'nice_to_have'"
    )
    text: str = Field(..., description="Description of the experience requirement")
    evidence: Optional[str] = Field(
        default=None, description="Verbatim text from JD"
    )

    @field_validator("priority", mode="before")
    @classmethod
    def validate_priority(cls, v: Any) -> str:
        if not v:
            return "must_have"
        cleaned = str(v).strip().lower().replace("-", "_")
        if any(w in cleaned for w in ["preferred", "nice", "bonus", "plus", "optional", "desired", "good_to_have"]):
            return "nice_to_have"
        return "must_have"


class JobEducationRequirement(BaseModel):
    degree: Optional[str] = Field(
        default=None, description="Degree level (e.g. Bachelor's, Master's, Ph.D., B.Tech, Diploma)"
    )
    field: Optional[str] = Field(
        default=None, description="Field of study (e.g. Computer Science, Engineering, Mathematics)"
    )
    priority: RequirementPriority = Field(
        default="must_have", description="'must_have' or 'nice_to_have'"
    )
    evidence: Optional[str] = Field(
        default=None, description="Exact phrase or sentence from the JD"
    )

    @field_validator("priority", mode="before")
    @classmethod
    def validate_priority(cls, v: Any) -> str:
        if not v:
            return "must_have"
        cleaned = str(v).strip().lower().replace("-", "_")
        if any(w in cleaned for w in ["preferred", "nice", "bonus", "plus", "optional", "desired", "good_to_have"]):
            return "nice_to_have"
        return "must_have"


class JobCertificationRequirement(BaseModel):
    name: str = Field(..., description="Certification title (e.g. AWS Certified Solutions Architect)")
    priority: RequirementPriority = Field(
        default="must_have", description="'must_have' or 'nice_to_have'"
    )
    evidence: Optional[str] = Field(
        default=None, description="Exact text from JD"
    )

    @field_validator("priority", mode="before")
    @classmethod
    def validate_priority(cls, v: Any) -> str:
        if not v:
            return "must_have"
        cleaned = str(v).strip().lower().replace("-", "_")
        if any(w in cleaned for w in ["preferred", "nice", "bonus", "plus", "optional", "desired", "good_to_have"]):
            return "nice_to_have"
        return "must_have"


class JobOtherRequirement(BaseModel):
    type: str = Field(default="other", description="'location', 'language', 'other'")
    text: str = Field(..., description="Requirement description")
    priority: RequirementPriority = Field(
        default="must_have", description="'must_have' or 'nice_to_have'"
    )
    evidence: Optional[str] = Field(
        default=None, description="Exact quote from JD"
    )

    @field_validator("priority", mode="before")
    @classmethod
    def validate_priority(cls, v: Any) -> str:
        if not v:
            return "must_have"
        cleaned = str(v).strip().lower().replace("-", "_")
        if any(w in cleaned for w in ["preferred", "nice", "bonus", "plus", "optional", "desired", "good_to_have"]):
            return "nice_to_have"
        return "must_have"


class JobRequirementItem(BaseModel):
    """Unified / reusable requirement item model."""
    text: str
    type: RequirementType
    priority: RequirementPriority = "must_have"
    skill: Optional[str] = None
    minimum_years: Optional[float] = None
    evidence: Optional[str] = None


class JobProfile(BaseModel):
    job_title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: List[JobSkillRequirement] = []
    normalized_skills: List[NormalizedJobSkill] = []
    experience_requirements: List[JobExperienceRequirement] = []
    education_requirements: List[JobEducationRequirement] = []
    certification_requirements: List[JobCertificationRequirement] = []
    other_requirements: List[JobOtherRequirement] = []
    responsibilities: List[str] = []
    must_have: List[JobRequirementItem] = []
    nice_to_have: List[JobRequirementItem] = []


class JobAnalysisRequest(BaseModel):
    job_description: str = Field(..., min_length=10, description="Raw job description text")
    job_title: Optional[str] = Field(default=None, description="Optional override or initial job title")


class JobAnalysisMetadata(BaseModel):
    character_count: int
    word_count: int
    source_type: str = Field(default="text", description="'text', 'pdf', or 'docx'")
    llm_provider: str


class JobAnalysisResponse(BaseModel):
    job_title: Optional[str] = None
    profile: JobProfile
    metadata: JobAnalysisMetadata


# ---------------------------------------------------------
# Candidate ↔ Job Matching Schemas (Phase 6)
# ---------------------------------------------------------
class MatchStatus(str, Enum):
    MATCHED = "matched"
    PARTIAL = "partial"
    UNMATCHED = "unmatched"
    NOT_EVALUABLE = "not_evaluable"


class MatchMethod(str, Enum):
    CANONICAL_EXACT = "canonical_exact"
    ALIAS_NORMALIZED = "alias_normalized"
    VERSION_COMPATIBLE = "version_compatible"
    EXPERIENCE_VERIFIED = "experience_verified"
    EXPERIENCE_INSUFFICIENT = "experience_insufficient"
    EDUCATION_MATCH = "education_match"
    EDUCATION_PARTIAL = "education_partial"
    CERTIFICATION_MATCH = "certification_match"
    TEXT_EVIDENCE = "text_evidence"
    UNMATCHED = "unmatched"
    NOT_EVALUABLE = "not_evaluable"


class RequirementReference(BaseModel):
    """Reference identifying a specific job requirement being evaluated."""
    name: str = Field(..., description="Requirement identifier (skill name, role scope, degree, cert)")
    type: RequirementType = Field(default="skill", description="'skill', 'experience', 'education', 'certification', 'other'")
    priority: RequirementPriority = Field(default="must_have", description="'must_have' or 'nice_to_have'")
    minimum_years: Optional[float] = Field(default=None, description="Minimum years if experience/skill-tenure based")
    category: Optional[str] = Field(default=None, description="Skill category if applicable")
    context: Optional[str] = Field(default=None, description="Original verbatim requirement text from JD")


class SingleRequirementMatch(BaseModel):
    """Structured evaluation of a single requirement against candidate profile evidence."""
    requirement: RequirementReference
    status: MatchStatus
    match_method: MatchMethod
    candidate_evidence: List[str] = Field(default_factory=list, description="Verbatim or traceable quotes from candidate profile")
    requirement_evidence: List[str] = Field(default_factory=list, description="Verbatim quotes from job description")
    reason: Optional[str] = Field(default=None, description="Deterministic explanation of how the decision was reached")
    semantic_result: Optional["SemanticMatchResult"] = Field(default=None, description="Optional Phase 7 semantic evaluation for this requirement")


class MatchingSummary(BaseModel):
    """Aggregate counts of matched, partial, unmatched, and not_evaluable requirements. (No score/percentage)."""
    total_requirements: int = 0
    matched: int = 0
    partial: int = 0
    unmatched: int = 0
    not_evaluable: int = 0
    must_have_total: int = 0
    must_have_matched: int = 0
    nice_to_have_total: int = 0
    nice_to_have_matched: int = 0


class CandidateJobMatchResponse(BaseModel):
    """Top-level match evaluation report for a Candidate against a Job Profile."""
    candidate_id: Optional[str] = None
    job_id: Optional[str] = None
    job_title: Optional[str] = None
    matches: List[SingleRequirementMatch] = []
    summary: MatchingSummary
    semantic_matches: Optional[List["SemanticMatchResult"]] = Field(default=None, description="Optional Phase 7 semantic matching results")


class MatchingAnalyzeRequest(BaseModel):
    """Request model for matching a CandidateProfile against a JobProfile directly."""
    candidate: CandidateProfile
    job: JobProfile
    candidate_id: Optional[str] = None
    job_id: Optional[str] = None
    include_semantic: Optional[bool] = Field(default=False, description="Whether to execute Phase 7 semantic matching alongside Phase 6")


# ---------------------------------------------------------
# Semantic Matching Schemas (Phase 7)
# ---------------------------------------------------------
class SemanticStatus(str, Enum):
    SEMANTIC_MATCH = "semantic_match"
    SEMANTIC_PARTIAL = "semantic_partial"
    SEMANTIC_UNRELATED = "semantic_unrelated"
    SEMANTIC_NOT_EVALUABLE = "semantic_not_evaluable"


class SemanticMatchResult(BaseModel):
    """Detailed semantic evaluation of a single requirement against candidate evidence."""
    requirement_id: str = Field(..., description="Target requirement identifier (e.g. 'skill_FastAPI')")
    requirement_text: str = Field(..., description="Contextual text representation of the job requirement")
    category: str = Field(default="skill", description="'skill', 'experience', 'education', 'certification', 'other'")
    priority: RequirementPriority = Field(default="must_have", description="'must_have' or 'nice_to_have'")
    similarity: float = Field(..., description="Raw cosine similarity [-1.0, 1.0]")
    semantic_status: SemanticStatus = Field(..., description="semantic_match, semantic_partial, semantic_unrelated, semantic_not_evaluable")
    candidate_evidence: Optional[str] = Field(default=None, description="Best candidate evidence string matched")
    candidate_source: Optional[str] = Field(default=None, description="Source section in candidate profile: 'skills', 'experience', 'projects', 'certifications'")
    candidate_text: Optional[str] = Field(default=None, description="Contextual candidate string embedded")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Embedding model name used")
    model_version: Optional[str] = Field(default=None, description="Model version if available")
    explanation: Optional[str] = Field(default=None, description="Human-readable explanation of semantic comparison")


class SemanticMatchSummary(BaseModel):
    """Summary of semantic evaluation across evaluated requirements."""
    total_evaluated: int = 0
    semantic_match_count: int = 0
    semantic_partial_count: int = 0
    semantic_unrelated_count: int = 0
    semantic_not_evaluable_count: int = 0
    high_threshold: float = 0.75
    medium_threshold: float = 0.55


class CandidateJobSemanticMatchResponse(BaseModel):
    """Response model for dedicated semantic matching endpoint POST /api/v1/matching/semantic."""
    candidate_id: Optional[str] = None
    candidate_name: Optional[str] = None
    job_id: Optional[str] = None
    job_title: Optional[str] = None
    semantic_results: List[SemanticMatchResult] = Field(default_factory=list)
    summary: SemanticMatchSummary
    embedding_model: str = "all-MiniLM-L6-v2"
    thresholds: Dict[str, float] = Field(default_factory=dict)



