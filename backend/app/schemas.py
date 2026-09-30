from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


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
# Candidate Profile Schemas
# ---------------------------------------------------------
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
