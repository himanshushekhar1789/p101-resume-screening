"""
Candidate ↔ Job Requirement Matching Engine for P_101 Resume Screening System (Phase 6).

Evaluates whether a structured CandidateProfile satisfies individual structured requirements
from a JobProfile across:
- Technical and soft skills (canonical exact, alias normalized, version compatible, or unmatched)
- General and skill-specific experience duration
- Education level and field of study (full match vs partial match)
- Industry certifications
- Other explicit requirements

STRICT SCOPE & PRINCIPLES:
- Deterministic only (0 LLM calls, 0 fuzzy-wuzzy string thresholds)
- Preserves requirement priority (must_have vs nice_to_have)
- Preserves explicit evidence/traceability from structured source data
- Uses 'not_evaluable' when evidence is incomplete (avoids false rejections)
- NO overall candidate scores, percentages, rankings, or recommendations.
"""

import re
import logging
from typing import List, Optional, Tuple, Dict, Any, Set

from backend.app.schemas import (
    CandidateProfile,
    JobProfile,
    NormalizedSkill,
    NormalizedJobSkill,
    JobExperienceRequirement,
    JobEducationRequirement,
    JobCertificationRequirement,
    JobOtherRequirement,
    MatchStatus,
    MatchMethod,
    RequirementReference,
    SingleRequirementMatch,
    MatchingSummary,
    CandidateJobMatchResponse,
)
from backend.app.services.skill_normalizer import (
    normalize_candidate_skills,
    normalize_job_skills,
)
from backend.app.services.skill_taxonomy import lookup_canonical_skill

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Degree Equivalence & Rank Mapping (Section 15 & 16)
# ---------------------------------------------------------------------------
DEGREE_LEVEL_HIERARCHY: Dict[str, int] = {
    "diploma": 1,
    "associate": 1,
    "bachelor": 2,
    "master": 3,
    "doctorate": 4,
}

BACHELOR_SYNONYMS: Set[str] = {
    "bachelor",
    "bachelor's",
    "bachelors",
    "b.s.",
    "bs",
    "b.tech",
    "btech",
    "b.e.",
    "be",
    "b.a.",
    "ba",
    "b.sc",
    "bsc",
    "undergraduate",
}

MASTER_SYNONYMS: Set[str] = {
    "master",
    "master's",
    "masters",
    "m.s.",
    "ms",
    "m.tech",
    "mtech",
    "m.e.",
    "me",
    "m.a.",
    "ma",
    "m.sc",
    "msc",
    "postgraduate",
    "graduate",
}

DOCTORATE_SYNONYMS: Set[str] = {
    "ph.d.",
    "phd",
    "doctorate",
    "doctoral",
    "d.phil",
}

DIPLOMA_SYNONYMS: Set[str] = {
    "diploma",
    "associate",
    "associates",
    "a.s.",
    "a.a.",
}

# ---------------------------------------------------------------------------
# Field of Study Families
# ---------------------------------------------------------------------------
CS_FIELD_FAMILY: Set[str] = {
    "computer science",
    "cs",
    "computer engineering",
    "software engineering",
    "information technology",
    "it",
    "computing",
    "computer applications",
    "bca",
    "mca",
    "informatics",
}

DATA_FIELD_FAMILY: Set[str] = {
    "data science",
    "statistics",
    "mathematics",
    "math",
    "machine learning",
    "analytics",
    "applied mathematics",
    "computational statistics",
}


def parse_degree_level(degree_raw: Optional[str]) -> Optional[str]:
    """Normalize raw degree text into a canonical level: bachelor, master, doctorate, diploma."""
    if not degree_raw:
        return None
    cleaned = degree_raw.strip().lower()
    for syn in DOCTORATE_SYNONYMS:
        if re.search(r"\b" + re.escape(syn) + r"\b", cleaned):
            return "doctorate"
    for syn in MASTER_SYNONYMS:
        if re.search(r"\b" + re.escape(syn) + r"\b", cleaned):
            return "master"
    for syn in BACHELOR_SYNONYMS:
        # Extra care: avoid matching plain word 'be' if not dotted or preceded by b
        if syn == "be" and not re.search(r"\bb\.e\.?\b", cleaned):
            continue
        if re.search(r"\b" + re.escape(syn) + r"\b", cleaned):
            return "bachelor"
    for syn in DIPLOMA_SYNONYMS:
        if re.search(r"\b" + re.escape(syn) + r"\b", cleaned):
            return "diploma"
    return None


def is_field_of_study_compatible(cand_field: Optional[str], req_field_text: Optional[str]) -> bool:
    """Deterministic compatibility check between candidate field and required field(s)."""
    if not req_field_text:
        return True  # Any field is acceptable if JD did not specify
    if not cand_field:
        return False

    c_clean = cand_field.strip().lower()
    r_clean = req_field_text.strip().lower()

    # Direct substring / containment match
    if c_clean in r_clean or r_clean in c_clean:
        return True

    # CS family cross-check
    cand_is_cs = any(term in c_clean for term in CS_FIELD_FAMILY)
    req_is_cs = any(term in r_clean for term in CS_FIELD_FAMILY)
    if cand_is_cs and req_is_cs:
        return True

    # Data family cross-check
    cand_is_data = any(term in c_clean for term in DATA_FIELD_FAMILY)
    req_is_data = any(term in r_clean for term in DATA_FIELD_FAMILY)
    if cand_is_data and req_is_data:
        return True

    return False


# ---------------------------------------------------------------------------
# Experience Duration Helpers (Section 12 & 14)
# ---------------------------------------------------------------------------
def parse_date_to_year_float(date_str: Optional[str], current_year: float = 2026.0) -> Optional[float]:
    """Parse a date string into a decimal year float (e.g. '2022' -> 2022.0, '06/2019' -> 2019.46)."""
    if not date_str or not isinstance(date_str, str):
        return None

    cleaned = date_str.strip()
    if cleaned.lower() in ["present", "current", "now", "ongoing"]:
        return current_year

    # Check for month/year: e.g. 06/2019
    m_slash = re.search(r"\b(0?[1-9]|1[0-2])/(\d{4})\b", cleaned)
    if m_slash:
        month = int(m_slash.group(1))
        year = int(m_slash.group(2))
        return year + (month - 0.5) / 12.0

    # Check for named month: e.g. June 2019
    months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    m_named = re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{4})\b", cleaned, re.I)
    if m_named:
        month_idx = months.index(m_named.group(1).lower()) + 1
        year = int(m_named.group(2))
        return year + (month_idx - 0.5) / 12.0

    # Check for 4-digit year: e.g. 2019
    m_year = re.search(r"\b(19\d\d|20\d\d)\b", cleaned)
    if m_year:
        return float(m_year.group(1))

    return None


def calculate_non_overlapping_tenure(intervals: List[Tuple[float, float]]) -> float:
    """
    Calculate total duration from a list of (start_year, end_year) intervals
    without double-counting overlapping periods (Section 14).
    """
    valid = [iv for iv in intervals if iv[0] is not None and iv[1] is not None and iv[1] >= iv[0]]
    if not valid:
        return 0.0

    # Sort intervals by start date
    valid.sort(key=lambda x: x[0])
    merged = []
    for start, end in valid:
        if not merged:
            merged.append([start, end])
        else:
            prev = merged[-1]
            if start <= prev[1]:
                prev[1] = max(prev[1], end)
            else:
                merged.append([start, end])

    return sum(end - start for start, end in merged)


# ---------------------------------------------------------------------------
# Matching Engine Implementation
# ---------------------------------------------------------------------------
class MatchingEngine:
    """
    Deterministic matching engine executing requirement satisfaction logic
    between CandidateProfile and JobProfile.
    """

    def __init__(self, current_year: float = 2026.0):
        self.current_year = current_year

    def match_candidate_to_job(
        self,
        candidate: CandidateProfile,
        job: JobProfile,
        candidate_id: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> CandidateJobMatchResponse:
        """
        Evaluate all structured requirements of a job against candidate evidence.
        """
        # Ensure canonical skills are populated
        cand_norm_skills = candidate.normalized_skills or normalize_candidate_skills(candidate.skills)
        job_norm_skills = job.normalized_skills or normalize_job_skills(job.skills)

        # Build candidate lookup indexes
        cand_skills_by_canonical: Dict[str, NormalizedSkill] = {
            s.canonical_name.lower(): s for s in cand_norm_skills
        }

        matches: List[SingleRequirementMatch] = []

        # 1. Evaluate Skills
        for req_skill in job_norm_skills:
            match_res = self._evaluate_skill_requirement(req_skill, candidate, cand_skills_by_canonical)
            matches.append(match_res)

        # 2. Evaluate Experience Requirements
        for exp_req in job.experience_requirements:
            match_res = self._evaluate_experience_requirement(exp_req, candidate)
            matches.append(match_res)

        # 3. Evaluate Education Requirements
        for edu_req in job.education_requirements:
            match_res = self._evaluate_education_requirement(edu_req, candidate)
            matches.append(match_res)

        # 4. Evaluate Certification Requirements
        for cert_req in job.certification_requirements:
            match_res = self._evaluate_certification_requirement(cert_req, candidate)
            matches.append(match_res)

        # 5. Evaluate Other Requirements (deterministic & conservative)
        for oth_req in job.other_requirements:
            match_res = self._evaluate_other_requirement(oth_req, candidate)
            matches.append(match_res)

        # Compute Summary (Counts only, NO percentage/score!)
        summary = self._compute_summary(matches)

        return CandidateJobMatchResponse(
            candidate_id=candidate_id or getattr(candidate.personal_info, "email", None),
            job_id=job_id or job.job_title,
            job_title=job.job_title,
            matches=matches,
            summary=summary,
        )

    # -----------------------------------------------------------------------
    # Skill Requirement Evaluation
    # -----------------------------------------------------------------------
    def _evaluate_skill_requirement(
        self,
        req: NormalizedJobSkill,
        candidate: CandidateProfile,
        cand_skills_map: Dict[str, NormalizedSkill],
    ) -> SingleRequirementMatch:
        req_ref = RequirementReference(
            name=req.canonical_name,
            type="skill",
            priority=req.priority,
            minimum_years=req.minimum_years,
            category=req.category,
            context=req.evidence or f"{req.canonical_name} ({req.priority})",
        )

        req_evidence = [req.evidence] if req.evidence else [f"Requirement: {req.canonical_name}"]
        key = req.canonical_name.lower()

        cand_skill = cand_skills_map.get(key)

        # Check candidate evidence from experience & projects
        exp_evidence = []
        for exp in candidate.experience:
            role_desc = f"{exp.title or 'Role'} at {exp.company or 'Company'}"
            exp_text = f"{exp.title or ''} {exp.description or ''} {' '.join(exp.skills)}"
            if re.search(r"\b" + re.escape(req.canonical_name) + r"\b", exp_text, re.I):
                exp_evidence.append(f"{role_desc} ({exp.start_date or ''} - {exp.end_date or 'Present'})")

        proj_evidence = []
        for proj in candidate.projects:
            proj_text = f"{proj.name} {proj.description or ''} {' '.join(proj.technologies)}"
            if re.search(r"\b" + re.escape(req.canonical_name) + r"\b", proj_text, re.I):
                proj_evidence.append(f"Project: {proj.name}")

        if cand_skill:
            cand_evidence = [
                f"Skill: {', '.join(cand_skill.original_names)} (Canonical: {cand_skill.canonical_name})"
            ] + exp_evidence + proj_evidence

            # Determine match method
            if cand_skill.normalization_method == "alias":
                method = MatchMethod.ALIAS_NORMALIZED
            elif cand_skill.normalization_method == "version_stripped":
                method = MatchMethod.VERSION_COMPATIBLE
            else:
                method = MatchMethod.CANONICAL_EXACT

            # Handle skill-specific tenure if required (Section 13)
            if req.minimum_years and req.minimum_years > 0:
                # Skill has minimum years requirement; check if explicit tenure can be verified
                tenure_intervals = []
                for exp in candidate.experience:
                    exp_text = f"{exp.title or ''} {exp.description or ''} {' '.join(exp.skills)}"
                    if re.search(r"\b" + re.escape(req.canonical_name) + r"\b", exp_text, re.I):
                        s_yr = parse_date_to_year_float(exp.start_date, self.current_year)
                        e_yr = parse_date_to_year_float(
                            exp.end_date if not exp.is_current else "Present", self.current_year
                        )
                        if s_yr is not None and e_yr is not None:
                            tenure_intervals.append((s_yr, e_yr))

                verified_skill_years = calculate_non_overlapping_tenure(tenure_intervals)

                if verified_skill_years >= req.minimum_years:
                    return SingleRequirementMatch(
                        requirement=req_ref,
                        status=MatchStatus.MATCHED,
                        match_method=MatchMethod.EXPERIENCE_VERIFIED,
                        candidate_evidence=cand_evidence,
                        requirement_evidence=req_evidence,
                        reason=f"Candidate satisfies {req.canonical_name} with ~{round(verified_skill_years, 1)} verified years (>= {req.minimum_years} required).",
                    )
                elif verified_skill_years > 0:
                    return SingleRequirementMatch(
                        requirement=req_ref,
                        status=MatchStatus.PARTIAL,
                        match_method=MatchMethod.EXPERIENCE_INSUFFICIENT,
                        candidate_evidence=cand_evidence,
                        requirement_evidence=req_evidence,
                        reason=f"Candidate has ~{round(verified_skill_years, 1)} verified years of {req.canonical_name}, which is below required {req.minimum_years} years.",
                    )
                else:
                    # Section 13: "If the resume only says Software Developer and separately lists Python under skills,
                    # do not automatically claim 5 years of Python experience. Return: not_evaluable"
                    return SingleRequirementMatch(
                        requirement=req_ref,
                        status=MatchStatus.NOT_EVALUABLE,
                        match_method=MatchMethod.NOT_EVALUABLE,
                        candidate_evidence=cand_evidence,
                        requirement_evidence=req_evidence,
                        reason=f"Candidate possesses {req.canonical_name} as a skill, but specific {req.minimum_years}+ year tenure cannot be verified from dated roles.",
                    )

            # No tenure required: pure skill match
            return SingleRequirementMatch(
                requirement=req_ref,
                status=MatchStatus.MATCHED,
                match_method=method,
                candidate_evidence=cand_evidence,
                requirement_evidence=req_evidence,
                reason=f"Candidate possesses canonical skill {req.canonical_name}.",
            )

        # Not in candidate skills list, but mentioned in experience/projects
        if exp_evidence or proj_evidence:
            return SingleRequirementMatch(
                requirement=req_ref,
                status=MatchStatus.PARTIAL,
                match_method=MatchMethod.TEXT_EVIDENCE,
                candidate_evidence=exp_evidence + proj_evidence,
                requirement_evidence=req_evidence,
                reason=f"Mentioned in projects/experience, but not listed as a primary verified skill.",
            )

        # Unmatched
        return SingleRequirementMatch(
            requirement=req_ref,
            status=MatchStatus.UNMATCHED,
            match_method=MatchMethod.UNMATCHED,
            candidate_evidence=[],
            requirement_evidence=req_evidence,
            reason=f"No matching evidence for {req.canonical_name} found in candidate profile.",
        )

    # -----------------------------------------------------------------------
    # Experience Requirement Evaluation
    # -----------------------------------------------------------------------
    def _evaluate_experience_requirement(
        self,
        req: JobExperienceRequirement,
        candidate: CandidateProfile,
    ) -> SingleRequirementMatch:
        req_ref = RequirementReference(
            name=req.text or (f"{req.minimum_years}+ years" if req.minimum_years else "Experience"),
            type="experience",
            priority=req.priority,
            minimum_years=req.minimum_years,
            context=req.evidence or req.text,
        )

        req_evidence = [req.evidence] if req.evidence else [req.text]

        # Case 1: Skill-specific experience requirement (e.g. "3+ years Python")
        if req.skill:
            # Look up canonical skill name
            lookup = lookup_canonical_skill(req.skill)
            target_skill_name = lookup[0] if lookup else req.skill

            cand_intervals = []
            exp_evidence_lines = []
            for exp in candidate.experience:
                role_desc = f"{exp.title or 'Role'} at {exp.company or 'Company'}"
                full_text = f"{exp.title or ''} {exp.description or ''} {' '.join(exp.skills)}"
                if re.search(r"\b" + re.escape(target_skill_name) + r"\b", full_text, re.I):
                    s_yr = parse_date_to_year_float(exp.start_date, self.current_year)
                    e_yr = parse_date_to_year_float(
                        exp.end_date if not exp.is_current else "Present", self.current_year
                    )
                    if s_yr is not None and e_yr is not None:
                        cand_intervals.append((s_yr, e_yr))
                    exp_evidence_lines.append(f"{role_desc} ({exp.start_date or ''} - {exp.end_date or 'Present'})")

            verified_tenure = calculate_non_overlapping_tenure(cand_intervals)
            req_years = req.minimum_years or 0.0

            if verified_tenure >= req_years:
                return SingleRequirementMatch(
                    requirement=req_ref,
                    status=MatchStatus.MATCHED,
                    match_method=MatchMethod.EXPERIENCE_VERIFIED,
                    candidate_evidence=exp_evidence_lines or [f"Verified ~{round(verified_tenure, 1)} years"],
                    requirement_evidence=req_evidence,
                    reason=f"Verified ~{round(verified_tenure, 1)} years of {target_skill_name} experience (>= {req_years} required).",
                )
            elif verified_tenure > 0:
                return SingleRequirementMatch(
                    requirement=req_ref,
                    status=MatchStatus.UNMATCHED,
                    match_method=MatchMethod.EXPERIENCE_INSUFFICIENT,
                    candidate_evidence=exp_evidence_lines,
                    requirement_evidence=req_evidence,
                    reason=f"Candidate has ~{round(verified_tenure, 1)} years of {target_skill_name}, below required {req_years} years.",
                )
            else:
                # Skill might be in skills list without dated tenure
                cand_has_skill = any(
                    s.canonical_name.lower() == target_skill_name.lower()
                    for s in candidate.normalized_skills
                ) or any(s.name.lower() == target_skill_name.lower() for s in candidate.skills)

                if cand_has_skill:
                    return SingleRequirementMatch(
                        requirement=req_ref,
                        status=MatchStatus.NOT_EVALUABLE,
                        match_method=MatchMethod.NOT_EVALUABLE,
                        candidate_evidence=[f"Skill {target_skill_name} is listed, but exact duration is not documented in role dates."],
                        requirement_evidence=req_evidence,
                        reason=f"Candidate lists {target_skill_name}, but tenure cannot be reliably calculated from dated roles.",
                    )
                else:
                    return SingleRequirementMatch(
                        requirement=req_ref,
                        status=MatchStatus.UNMATCHED,
                        match_method=MatchMethod.UNMATCHED,
                        candidate_evidence=[],
                        requirement_evidence=req_evidence,
                        reason=f"No experience with {target_skill_name} found in candidate profile.",
                    )

        # Case 2: General Experience Requirement (e.g. "5+ years backend software engineering")
        all_intervals = []
        exp_evidence_lines = []
        for exp in candidate.experience:
            s_yr = parse_date_to_year_float(exp.start_date, self.current_year)
            e_yr = parse_date_to_year_float(
                exp.end_date if not exp.is_current else "Present", self.current_year
            )
            if s_yr is not None and e_yr is not None:
                all_intervals.append((s_yr, e_yr))
            role_desc = f"{exp.title or 'Role'} at {exp.company or 'Company'}"
            exp_evidence_lines.append(f"{role_desc} ({exp.start_date or ''} - {exp.end_date or 'Present'})")

        total_verified_years = calculate_non_overlapping_tenure(all_intervals)
        req_years = req.minimum_years or 0.0

        if not candidate.experience or (total_verified_years == 0 and not all_intervals):
            return SingleRequirementMatch(
                requirement=req_ref,
                status=MatchStatus.NOT_EVALUABLE,
                match_method=MatchMethod.NOT_EVALUABLE,
                candidate_evidence=[],
                requirement_evidence=req_evidence,
                reason="Candidate experience records lack explicit start/end dates to calculate duration.",
            )

        if total_verified_years >= req_years:
            return SingleRequirementMatch(
                requirement=req_ref,
                status=MatchStatus.MATCHED,
                match_method=MatchMethod.EXPERIENCE_VERIFIED,
                candidate_evidence=exp_evidence_lines,
                requirement_evidence=req_evidence,
                reason=f"Candidate has ~{round(total_verified_years, 1)} years of experience (>= {req_years} required).",
            )
        else:
            return SingleRequirementMatch(
                requirement=req_ref,
                status=MatchStatus.UNMATCHED,
                match_method=MatchMethod.EXPERIENCE_INSUFFICIENT,
                candidate_evidence=exp_evidence_lines,
                requirement_evidence=req_evidence,
                reason=f"Candidate has ~{round(total_verified_years, 1)} years of experience, below required {req_years} years.",
            )

    # -----------------------------------------------------------------------
    # Education Requirement Evaluation
    # -----------------------------------------------------------------------
    def _evaluate_education_requirement(
        self,
        req: JobEducationRequirement,
        candidate: CandidateProfile,
    ) -> SingleRequirementMatch:
        req_ref = RequirementReference(
            name=f"{req.degree or 'Degree'}" + (f" in {req.field}" if req.field else ""),
            type="education",
            priority=req.priority,
            context=req.evidence or f"{req.degree} in {req.field}",
        )
        req_evidence = [req.evidence] if req.evidence else [f"{req.degree} in {req.field}"]

        if not candidate.education:
            return SingleRequirementMatch(
                requirement=req_ref,
                status=MatchStatus.UNMATCHED,
                match_method=MatchMethod.UNMATCHED,
                candidate_evidence=[],
                requirement_evidence=req_evidence,
                reason="No education records found in candidate profile.",
            )

        req_level = parse_degree_level(req.degree)
        req_level_rank = DEGREE_LEVEL_HIERARCHY.get(req_level, 2) if req_level else 2

        best_match_status = MatchStatus.UNMATCHED
        best_method = MatchMethod.UNMATCHED
        best_evidence = []
        best_reason = "Candidate education does not satisfy degree requirements."

        for edu in candidate.education:
            cand_level = parse_degree_level(edu.degree)
            cand_level_rank = DEGREE_LEVEL_HIERARCHY.get(cand_level, 0)
            edu_ev = f"{edu.degree or 'Degree'} in {edu.field or 'unspecified'} from {edu.institution or 'unspecified'}"

            # Level comparison: Does candidate degree level meet or exceed requirement?
            if cand_level_rank >= req_level_rank:
                # Field of study comparison
                if is_field_of_study_compatible(edu.field, req.field):
                    return SingleRequirementMatch(
                        requirement=req_ref,
                        status=MatchStatus.MATCHED,
                        match_method=MatchMethod.EDUCATION_MATCH,
                        candidate_evidence=[edu_ev],
                        requirement_evidence=req_evidence,
                        reason=f"Candidate holds {edu.degree} in {edu.field or 'compatible field'}, satisfying {req_ref.name}.",
                    )
                else:
                    # Degree level matches, but field differs (Section 16 & Scenario 5)
                    best_match_status = MatchStatus.PARTIAL
                    best_method = MatchMethod.EDUCATION_PARTIAL
                    best_evidence = [edu_ev]
                    best_reason = f"Candidate degree level ({edu.degree}) satisfies requirement, but field ({edu.field}) does not match required {req.field}."
            else:
                if best_match_status == MatchStatus.UNMATCHED:
                    best_evidence = [edu_ev]
                    best_reason = f"Candidate degree ({edu.degree}) does not meet required degree level ({req.degree})."

        return SingleRequirementMatch(
            requirement=req_ref,
            status=best_match_status,
            match_method=best_method,
            candidate_evidence=best_evidence,
            requirement_evidence=req_evidence,
            reason=best_reason,
        )

    # -----------------------------------------------------------------------
    # Certification Requirement Evaluation
    # -----------------------------------------------------------------------
    def _evaluate_certification_requirement(
        self,
        req: JobCertificationRequirement,
        candidate: CandidateProfile,
    ) -> SingleRequirementMatch:
        req_ref = RequirementReference(
            name=req.name,
            type="certification",
            priority=req.priority,
            context=req.evidence or req.name,
        )
        req_evidence = [req.evidence] if req.evidence else [req.name]

        r_norm = re.sub(r"[-–—\s]+", " ", req.name.strip().lower())

        for cert in candidate.certifications:
            c_norm = re.sub(r"[-–—\s]+", " ", cert.name.strip().lower())
            if r_norm in c_norm or c_norm in r_norm:
                return SingleRequirementMatch(
                    requirement=req_ref,
                    status=MatchStatus.MATCHED,
                    match_method=MatchMethod.CERTIFICATION_MATCH,
                    candidate_evidence=[f"Certification: {cert.name} ({cert.issuing_organization or 'Verified'})"],
                    requirement_evidence=req_evidence,
                    reason=f"Candidate holds required certification: {cert.name}.",
                )

        return SingleRequirementMatch(
            requirement=req_ref,
            status=MatchStatus.UNMATCHED,
            match_method=MatchMethod.UNMATCHED,
            candidate_evidence=[],
            requirement_evidence=req_evidence,
            reason=f"Certification {req.name} not found in candidate certifications.",
        )

    # -----------------------------------------------------------------------
    # Other Requirement Evaluation (Section 18)
    # -----------------------------------------------------------------------
    def _evaluate_other_requirement(
        self,
        req: JobOtherRequirement,
        candidate: CandidateProfile,
    ) -> SingleRequirementMatch:
        req_ref = RequirementReference(
            name=req.text,
            type="other",
            priority=req.priority,
            context=req.evidence or req.text,
        )
        req_evidence = [req.evidence] if req.evidence else [req.text]

        req_type = req.type.lower() if req.type else "other"

        # Location requirement check
        if req_type == "location" or "location" in req.text.lower() or "remote" in req.text.lower():
            cand_loc = candidate.personal_info.location
            if not cand_loc:
                return SingleRequirementMatch(
                    requirement=req_ref,
                    status=MatchStatus.NOT_EVALUABLE,
                    match_method=MatchMethod.NOT_EVALUABLE,
                    candidate_evidence=[],
                    requirement_evidence=req_evidence,
                    reason="Candidate location is not provided in personal info.",
                )
            if cand_loc.lower() in req.text.lower() or req.text.lower() in cand_loc.lower():
                return SingleRequirementMatch(
                    requirement=req_ref,
                    status=MatchStatus.MATCHED,
                    match_method=MatchMethod.TEXT_EVIDENCE,
                    candidate_evidence=[f"Location: {cand_loc}"],
                    requirement_evidence=req_evidence,
                    reason=f"Candidate location ({cand_loc}) satisfies requirement.",
                )
            else:
                return SingleRequirementMatch(
                    requirement=req_ref,
                    status=MatchStatus.PARTIAL,
                    match_method=MatchMethod.TEXT_EVIDENCE,
                    candidate_evidence=[f"Location: {cand_loc}"],
                    requirement_evidence=req_evidence,
                    reason=f"Candidate location ({cand_loc}) differs from {req.text}.",
                )

        # Conservative default for undefined personal/administrative attributes
        return SingleRequirementMatch(
            requirement=req_ref,
            status=MatchStatus.NOT_EVALUABLE,
            match_method=MatchMethod.NOT_EVALUABLE,
            candidate_evidence=[],
            requirement_evidence=req_evidence,
            reason="Requirement cannot be evaluated from standard resume profile fields.",
        )

    # -----------------------------------------------------------------------
    # Summary Computation
    # -----------------------------------------------------------------------
    def _compute_summary(self, matches: List[SingleRequirementMatch]) -> MatchingSummary:
        summary = MatchingSummary(
            total_requirements=len(matches),
            matched=sum(1 for m in matches if m.status == MatchStatus.MATCHED),
            partial=sum(1 for m in matches if m.status == MatchStatus.PARTIAL),
            unmatched=sum(1 for m in matches if m.status == MatchStatus.UNMATCHED),
            not_evaluable=sum(1 for m in matches if m.status == MatchStatus.NOT_EVALUABLE),
            must_have_total=sum(1 for m in matches if m.requirement.priority == "must_have"),
            must_have_matched=sum(1 for m in matches if m.requirement.priority == "must_have" and m.status == MatchStatus.MATCHED),
            nice_to_have_total=sum(1 for m in matches if m.requirement.priority == "nice_to_have"),
            nice_to_have_matched=sum(1 for m in matches if m.requirement.priority == "nice_to_have" and m.status == MatchStatus.MATCHED),
        )
        return summary
