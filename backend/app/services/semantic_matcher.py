"""Semantic matching service using embeddings and cosine similarity (Phase 7).

Evaluates conceptual similarity between candidate evidence and job requirements
without overriding deterministic matching, taxonomy mappings, or hallucinating experience.

Architectural Principles:
1. Answers "How semantically related is this candidate evidence to this job requirement?"
2. Does NOT calculate overall candidate score, ranking, or hiring recommendations.
3. Does NOT override Phase 6 deterministic exact, alias, or version matches.
4. Does NOT invent years of experience or degree hierarchy equivalence.
5. Protects against false positives between distinct technologies (Java != JavaScript, C != C++, etc.).
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from backend.app.config import get_settings
from backend.app.schemas import (
    CandidateProfile,
    CandidateJobSemanticMatchResponse,
    JobProfile,
    RequirementPriority,
    SemanticMatchResult,
    SemanticMatchSummary,
    SemanticStatus,
    SingleRequirementMatch,
)
from backend.app.services.embedding_service import EmbeddingService, get_embedding_service

logger = logging.getLogger(__name__)

# Known distinct technology pairs that must NEVER be conflated semantically
# even if vector embeddings yield moderate or high lexical similarity (Section 19 & 43)
PROTECTED_INCOMPATIBLE_PAIRS: Set[frozenset] = {
    frozenset({"java", "javascript"}),
    frozenset({"c", "c++"}),
    frozenset({"c", "c#"}),
    frozenset({"python", "pytorch"}),
    frozenset({"aws", "aws lambda"}),
    frozenset({"react", "react native"}),
}


@dataclass
class CandidateEvidenceItem:
    """A granular, contextual piece of candidate evidence extracted from profile."""
    source: str  # 'skills', 'experience', 'projects', 'education', 'certifications'
    name: str    # Identifier (skill name, role title, project name, etc.)
    category: Optional[str]
    context: str  # Descriptive quote or bullet point
    full_text: str  # Structured string representation formatted for embedding


@dataclass
class RequirementSemanticItem:
    """A structured requirement representation formatted for embedding."""
    requirement_id: str
    name: str
    category: str  # 'skill', 'experience', 'education', 'certification', 'other'
    priority: RequirementPriority
    minimum_years: Optional[float]
    context: str
    full_text: str  # Structured string representation formatted for embedding


def is_protected_incompatible(req_name: str, cand_name: str) -> bool:
    """Check if requirement and candidate evidence names constitute a protected conflict."""
    r_clean = req_name.strip().lower()
    c_clean = cand_name.strip().lower()
    if r_clean == c_clean:
        return False
    return frozenset({r_clean, c_clean}) in PROTECTED_INCOMPATIBLE_PAIRS


def extract_candidate_evidence_items(candidate: CandidateProfile) -> List[CandidateEvidenceItem]:
    """Build structured, contextual candidate evidence items from the structured profile."""
    items: List[CandidateEvidenceItem] = []

    # 1. Candidate Skills (enriched with normalized name and category)
    if candidate.normalized_skills:
        for skill in candidate.normalized_skills:
            full_text = f"Skill: {skill.canonical_name} | Category: {skill.category}"
            items.append(
                CandidateEvidenceItem(
                    source="skills",
                    name=skill.canonical_name,
                    category=skill.category,
                    context=skill.canonical_name,
                    full_text=full_text,
                )
            )
    elif candidate.skills:
        for skill in candidate.skills:
            full_text = f"Skill: {skill.name} | Category: {skill.category or 'other'}"
            items.append(
                CandidateEvidenceItem(
                    source="skills",
                    name=skill.name,
                    category=skill.category,
                    context=skill.name,
                    full_text=full_text,
                )
            )

    # 2. Candidate Work Experience
    for exp in candidate.experience:
        role_title = exp.title or "Professional Experience"
        company = exp.company or "Company"
        skills_str = ", ".join(exp.skills) if exp.skills else "None specified"
        desc = (exp.description or "").strip()
        full_text = (
            f"Experience: {role_title} at {company} | "
            f"Description: {desc} | "
            f"Technologies: {skills_str}"
        )
        items.append(
            CandidateEvidenceItem(
                source="experience",
                name=role_title,
                category="experience",
                context=desc if desc else f"{role_title} at {company}",
                full_text=full_text,
            )
        )

    # 3. Candidate Projects
    for proj in candidate.projects:
        tech_str = ", ".join(proj.technologies) if proj.technologies else "None specified"
        desc = (proj.description or "").strip()
        full_text = (
            f"Project: {proj.name} | "
            f"Technologies: {tech_str} | "
            f"Description: {desc}"
        )
        items.append(
            CandidateEvidenceItem(
                source="projects",
                name=proj.name,
                category="project",
                context=desc if desc else f"Project {proj.name} using {tech_str}",
                full_text=full_text,
            )
        )

    # 4. Candidate Certifications
    for cert in candidate.certifications:
        issuer = cert.issuing_organization or "Issuing Organization"
        full_text = f"Certification: {cert.name} | Issuer: {issuer}"
        items.append(
            CandidateEvidenceItem(
                source="certifications",
                name=cert.name,
                category="certification",
                context=f"{cert.name} ({issuer})",
                full_text=full_text,
            )
        )

    return items


def extract_job_requirement_semantic_items(job: JobProfile) -> List[RequirementSemanticItem]:
    """Construct structured semantic requirement representations from the JobProfile."""
    items: List[RequirementSemanticItem] = []

    # 1. Skill Requirements
    if job.normalized_skills:
        for skill in job.normalized_skills:
            evidence_str = skill.evidence or skill.canonical_name
            req_text = (
                f"Required skill: {skill.canonical_name} | "
                f"Category: {skill.category} | "
                f"Priority: {skill.priority.value if hasattr(skill.priority, 'value') else skill.priority} | "
                f"Job requirement: {evidence_str}"
            )
            items.append(
                RequirementSemanticItem(
                    requirement_id=f"skill_{skill.canonical_name}",
                    name=skill.canonical_name,
                    category="skill",
                    priority=skill.priority,
                    minimum_years=skill.minimum_years,
                    context=evidence_str,
                    full_text=req_text,
                )
            )
    else:
        for skill in job.skills:
            evidence_str = skill.evidence or skill.name
            req_text = (
                f"Required skill: {skill.name} | "
                f"Category: {skill.category or 'other'} | "
                f"Priority: {skill.priority.value if hasattr(skill.priority, 'value') else skill.priority} | "
                f"Job requirement: {evidence_str}"
            )
            items.append(
                RequirementSemanticItem(
                    requirement_id=f"skill_{skill.name}",
                    name=skill.name,
                    category="skill",
                    priority=skill.priority,
                    minimum_years=skill.minimum_years,
                    context=evidence_str,
                    full_text=req_text,
                )
            )

    # 2. General / Specific Experience Requirements
    for exp_req in job.experience_requirements:
        evidence_str = exp_req.evidence or exp_req.text
        req_text = (
            f"Experience requirement: {exp_req.text} | "
            f"Priority: {exp_req.priority} | "
            f"Scope: {evidence_str}"
        )
        items.append(
            RequirementSemanticItem(
                requirement_id=f"exp_{exp_req.text[:20]}",
                name=exp_req.text,
                category="experience",
                priority=exp_req.priority,
                minimum_years=exp_req.minimum_years,
                context=evidence_str,
                full_text=req_text,
            )
        )

    # 3. Education Requirements
    for edu_req in job.education_requirements:
        degree_name = getattr(edu_req, "degree", None) or getattr(edu_req, "degree_level", None) or "Degree"
        field_val = getattr(edu_req, "field", None)
        if field_val:
            fields_str = field_val
        elif getattr(edu_req, "fields_of_study", None):
            fields_str = ", ".join(edu_req.fields_of_study)
        else:
            fields_str = "Computer Science"

        is_req = getattr(edu_req, "is_required", None)
        if is_req is None:
            is_req = (edu_req.priority == "must_have")

        evidence_str = edu_req.evidence or f"{degree_name} in {fields_str}"
        req_text = (
            f"Education requirement: {degree_name} in {fields_str} | "
            f"Required: {is_req} | "
            f"Evidence: {evidence_str}"
        )

        items.append(
            RequirementSemanticItem(
                requirement_id=f"edu_{degree_name}",
                name=f"{degree_name} in {fields_str}",
                category="education",
                priority=edu_req.priority,
                minimum_years=None,
                context=evidence_str,
                full_text=req_text,
            )
        )


    # 4. Certifications
    for cert in job.certification_requirements:
        evidence_str = cert.evidence or cert.name
        req_text = (
            f"Certification requirement: {cert.name} | "
            f"Priority: {cert.priority} | "
            f"Evidence: {evidence_str}"
        )
        items.append(
            RequirementSemanticItem(
                requirement_id=f"cert_{cert.name}",
                name=cert.name,
                category="certification",
                priority=cert.priority,
                minimum_years=None,
                context=evidence_str,
                full_text=req_text,
            )
        )

    return items


class SemanticMatcher:
    """Service orchestrating semantic matching and threshold evaluation."""

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        high_threshold: Optional[float] = None,
        medium_threshold: Optional[float] = None,
    ):
        settings = get_settings()
        self.embedding_service: EmbeddingService = embedding_service or get_embedding_service()
        self.high_threshold: float = high_threshold if high_threshold is not None else settings.semantic_high_threshold
        self.medium_threshold: float = medium_threshold if medium_threshold is not None else settings.semantic_medium_threshold

    def match_candidate_to_job(
        self,
        candidate: CandidateProfile,
        job: JobProfile,
        candidate_id: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> CandidateJobSemanticMatchResponse:
        """Evaluate semantic similarity across all job requirements against candidate evidence."""
        evidence_items = extract_candidate_evidence_items(candidate)
        requirement_items = extract_job_requirement_semantic_items(job)

        results: List[SemanticMatchResult] = []
        summary = SemanticMatchSummary(
            total_evaluated=len(requirement_items),
            high_threshold=self.high_threshold,
            medium_threshold=self.medium_threshold,
        )

        if not requirement_items:
            return CandidateJobSemanticMatchResponse(
                candidate_id=candidate_id,
                candidate_name=candidate.personal_info.name if candidate.personal_info else None,
                job_id=job_id,
                job_title=job.job_title,
                semantic_results=[],
                summary=summary,
                embedding_model=self.embedding_service.model_name,
                thresholds={"high": self.high_threshold, "medium": self.medium_threshold},
            )

        if not evidence_items:
            # Candidate has zero extractable evidence items
            for req in requirement_items:
                res = SemanticMatchResult(
                    requirement_id=req.requirement_id,
                    requirement_text=req.full_text,
                    category=req.category,
                    priority=req.priority,
                    similarity=0.0,
                    semantic_status=SemanticStatus.SEMANTIC_NOT_EVALUABLE,
                    candidate_evidence=None,
                    candidate_source=None,
                    candidate_text=None,
                    embedding_model=self.embedding_service.model_name,
                    model_version=self.embedding_service.model_version,
                    explanation="No candidate evidence items available to evaluate semantic similarity.",
                )
                results.append(res)
                summary.semantic_not_evaluable_count += 1

            return CandidateJobSemanticMatchResponse(
                candidate_id=candidate_id,
                candidate_name=candidate.personal_info.name if candidate.personal_info else None,
                job_id=job_id,
                job_title=job.job_title,
                semantic_results=results,
                summary=summary,
                embedding_model=self.embedding_service.model_name,
                thresholds={"high": self.high_threshold, "medium": self.medium_threshold},
            )

        # Batch embed candidate evidence items and requirements
        evidence_texts = [item.full_text for item in evidence_items]
        req_texts = [req.full_text for req in requirement_items]

        evidence_vectors = self.embedding_service.embed_texts(evidence_texts)
        req_vectors = self.embedding_service.embed_texts(req_texts)

        for req_idx, req in enumerate(requirement_items):
            req_vec = req_vectors[req_idx]
            best_sim = -1.0
            best_evidence: Optional[CandidateEvidenceItem] = None

            for ev_idx, ev_item in enumerate(evidence_items):
                ev_vec = evidence_vectors[ev_idx]
                sim = self.embedding_service.cosine_similarity(req_vec, ev_vec)

                # Check false-positive protection: if strictly incompatible, discard or cap
                if is_protected_incompatible(req.name, ev_item.name):
                    # Incompatible technologies (e.g. Java vs JavaScript) must not match
                    continue

                if sim > best_sim:
                    best_sim = sim
                    best_evidence = ev_item

            # Determine semantic status and build explanation
            if best_evidence is None or best_sim < 0.0:
                # No compatible evidence found
                sim_val = 0.0
                status = SemanticStatus.SEMANTIC_UNRELATED
                cand_quote = None
                cand_source = None
                cand_full = None
                explanation = (
                    f"No semantically compatible evidence found for requirement '{req.name}'. "
                    f"Potential cross-language false positives were filtered."
                )
                summary.semantic_unrelated_count += 1
            else:
                sim_val = round(best_sim, 4)
                cand_quote = best_evidence.context
                cand_source = best_evidence.source
                cand_full = best_evidence.full_text

                if sim_val >= self.high_threshold:
                    status = SemanticStatus.SEMANTIC_MATCH
                    summary.semantic_match_count += 1
                    explanation = (
                        f"Strong semantic similarity ({sim_val} >= {self.high_threshold}) with "
                        f"candidate {best_evidence.source}: '{best_evidence.context}'."
                    )
                elif sim_val >= self.medium_threshold:
                    status = SemanticStatus.SEMANTIC_PARTIAL
                    summary.semantic_partial_count += 1
                    explanation = (
                        f"Moderate semantic similarity ({sim_val} >= {self.medium_threshold}) indicating "
                        f"conceptually related experience from {best_evidence.source}: '{best_evidence.context}'."
                    )
                else:
                    status = SemanticStatus.SEMANTIC_UNRELATED
                    summary.semantic_unrelated_count += 1
                    explanation = (
                        f"Low semantic similarity ({sim_val} < {self.medium_threshold}); candidate evidence "
                        f"is not closely related to requirement '{req.name}'."
                    )

                # Guardrail: Skill-specific experience duration caveat (Section 25 & 26)
                if req.minimum_years and req.minimum_years > 0:
                    explanation += (
                        f" Note: Semantic similarity reflects conceptual relation but cannot verify the required "
                        f"{req.minimum_years} years of experience without explicit dated role evidence."
                    )

            res = SemanticMatchResult(
                requirement_id=req.requirement_id,
                requirement_text=req.full_text,
                category=req.category,
                priority=req.priority,
                similarity=sim_val,
                semantic_status=status,
                candidate_evidence=cand_quote,
                candidate_source=cand_source,
                candidate_text=cand_full,
                embedding_model=self.embedding_service.model_name,
                model_version=self.embedding_service.model_version,
                explanation=explanation,
            )
            results.append(res)

        return CandidateJobSemanticMatchResponse(
            candidate_id=candidate_id,
            candidate_name=candidate.personal_info.name if candidate.personal_info else None,
            job_id=job_id,
            job_title=job.job_title,
            semantic_results=results,
            summary=summary,
            embedding_model=self.embedding_service.model_name,
            thresholds={"high": self.high_threshold, "medium": self.medium_threshold},
        )


def evaluate_semantic_matches(
    candidate: CandidateProfile,
    job: JobProfile,
    embedding_service: Optional[EmbeddingService] = None,
) -> CandidateJobSemanticMatchResponse:
    """Convenience helper to execute semantic matching using default settings."""
    settings = get_settings()
    matcher = SemanticMatcher(
        embedding_service=embedding_service,
        high_threshold=settings.semantic_high_threshold,
        medium_threshold=settings.semantic_medium_threshold,
    )
    return matcher.match_candidate_to_job(candidate, job)
