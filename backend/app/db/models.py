import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship
from backend.app.db.session import Base


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    jd_text = Column(Text, nullable=False)
    requirements_json = Column(JSON, nullable=True)
    weights_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    candidates = relationship("Candidate", back_populates="job", cascade="all, delete-orphan")
    requirements = relationship("Requirement", back_populates="job", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="job", cascade="all, delete-orphan")
    skill_gaps = relationship("SkillGap", back_populates="job", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="job", cascade="all, delete-orphan")


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    display_id = Column(String(100), nullable=False)
    masked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    job = relationship("Job", back_populates="candidates")
    resume = relationship("Resume", back_populates="candidate", uselist=False, cascade="all, delete-orphan")
    profile = relationship("Profile", back_populates="candidate", uselist=False, cascade="all, delete-orphan")
    score = relationship("Score", back_populates="candidate", uselist=False, cascade="all, delete-orphan")
    skill_gaps = relationship("SkillGap", back_populates="candidate", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="candidate", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, docx
    raw_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    # Relationship
    candidate = relationship("Candidate", back_populates="resume")


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    skills = Column(JSON, nullable=True)              # list of strings / dicts
    experience = Column(JSON, nullable=True)          # list of experience dicts
    education = Column(JSON, nullable=True)           # list of education dicts
    projects = Column(JSON, nullable=True)            # list of project dicts
    certifications = Column(JSON, nullable=True)      # list of certifications
    achievements = Column(JSON, nullable=True)        # list of achievements
    raw_metadata = Column(JSON, nullable=True)

    # Relationship
    candidate = relationship("Candidate", back_populates="profile")


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_text = Column(String(500), nullable=False)
    type = Column(String(50), nullable=False)         # 'mandatory' or 'preferred'
    importance = Column(String(50), default="high")   # 'high', 'medium', 'low'
    category = Column(String(50), default="skill")    # 'skill', 'experience', 'education'

    # Relationship
    job = relationship("Job", back_populates="requirements")


class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_score = Column(Float, default=0.0)
    semantic_score = Column(Float, default=0.0)
    experience_score = Column(Float, default=0.0)
    llm_score = Column(Float, default=0.0)
    total_score = Column(Float, default=0.0, index=True)
    score_breakdown = Column(JSON, nullable=True)     # Stores weight mappings & formula notes
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    candidate = relationship("Candidate", back_populates="score")
    job = relationship("Job", back_populates="scores")

    __table_args__ = (
        Index("idx_job_total_score", "job_id", "total_score"),
    )


class SkillGap(Base):
    __tablename__ = "skill_gaps"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    skill = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)       # 'matched', 'partial', 'missing'
    importance = Column(String(50), default="high")   # 'high', 'medium', 'low'
    evidence = Column(Text, nullable=True)            # Quotes extracted directly from resume

    # Relationships
    candidate = relationship("Candidate", back_populates="skill_gaps")
    job = relationship("Job", back_populates="skill_gaps")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    skill = Column(String(255), nullable=True)
    recommendation = Column(Text, nullable=False)
    learning_direction = Column(Text, nullable=True)
    suggested_project = Column(Text, nullable=True)
    priority = Column(String(50), default="medium")   # 'high', 'medium', 'low'

    # Relationships
    candidate = relationship("Candidate", back_populates="recommendations")
    job = relationship("Job", back_populates="recommendations")
