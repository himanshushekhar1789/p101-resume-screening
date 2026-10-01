"""
Skill-Gap Analysis & Evidence Grounding Engine (Phase 9).

Identifies candidate skill gaps against job requirements, grounds those gaps in
verifiable candidate and job evidence, distinguishes missing vs insufficient vs
not_evaluable vs satisfied skills, and provides transparent, audit-compliant explanations.

STRICT SCOPE CONSTRAINTS:
- Deterministic-first: Phase 6 deterministic matching outcomes are authoritative.
- Supporting semantic evidence: Phase 7 semantic similarity provides contextual evidence
  annotations but CANNOT override deterministic missing status (Rule 6).
- General experience separation: General career tenure requirements are kept strictly
  separate in `experience_gaps` and never converted into skill gaps (e.g. "backend").
- Zero hallucinations: Every gap must cite explicit evidence or indicate that no evidence exists.
- ZERO candidate rankings, ZERO shortlists, ZERO hiring/rejection decisions, ZERO roadmaps.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple, Any, Set

from backend.app.schemas import (
    CandidateProfile,
    JobProfile,
    RequirementPriority,
    MatchStatus,
    MatchMethod,
    SingleRequirementMatch,
    CandidateJobMatchResponse,
    SemanticStatus,
    SemanticMatchResult,
    SkillGapStatus,
    SkillGapItem,
    ExperienceGapItem,
    SkillGapSummary,
    CandidateJobSkillGapResponse,
)
from backend.app.services.matching_engine import (
    MatchingEngine,
    parse_date_to_year_float,
    calculate_non_overlapping_tenure,
)
from backend.app.services.skill_taxonomy import lookup_canonical_skill

logger = logging.getLogger(__name__)


class SkillGapAnalyzer:
    """
    Evaluates candidate background against job requirements to identify,
    ground, and explain skill and experience gaps.
    """

    def __init__(self, current_year: float = 2026.0):
        self.current_year = current_year
        self.matching_engine = MatchingEngine(current_year=current_year)

    def analyze(
        self,
        candidate: CandidateProfile,
        job: JobProfile,
        match_response: Optional[CandidateJobMatchResponse] = None,
        include_semantic: bool = True,
    ) -> CandidateJobSkillGapResponse:
        """
        Executes skill gap analysis.
        If `match_response` is provided, reuses existing Phase 6 & 7 evaluations.
        Otherwise, executes matching pipeline deterministically.
        """
        if match_response is None:
            match_response = self.matching_engine.match_candidate_to_job(
                candidate=candidate,
                job=job,
                include_semantic=include_semantic,
            )

        # 1. Index Phase 7 semantic match results by requirement name and ID
        semantic_map: Dict[str, SemanticMatchResult] = {}
        if match_response.semantic_matches:
            for s in match_response.semantic_matches:
                semantic_map[s.requirement_id.lower()] = s
                semantic_map[s.requirement_text.lower()] = s
        for m in match_response.matches:
            if m.semantic_result:
                semantic_map[m.semantic_result.requirement_id.lower()] = m.semantic_result
                semantic_map[m.semantic_result.requirement_text.lower()] = m.semantic_result
                semantic_map[m.requirement.name.lower()] = m.semantic_result

        # 2. Separate skill matches vs experience matches
        skill_matches: List[SingleRequirementMatch] = []
        experience_matches: List[SingleRequirementMatch] = []

        for m in match_response.matches:
            if m.requirement.type == "skill":
                skill_matches.append(m)
            elif m.requirement.type == "experience":
                experience_matches.append(m)

        # 3. Process Skill Gaps (with deduplication by canonical skill name)
        skill_gaps = self._evaluate_skill_gaps(
            candidate=candidate,
            job=job,
            skill_matches=skill_matches,
            semantic_map=semantic_map,
        )

        # 4. Process General Career Experience Gaps (strictly separated from skill gaps)
        experience_gaps = self._evaluate_experience_gaps(
            candidate=candidate,
            job=job,
            experience_matches=experience_matches,
        )

        # 5. Compute aggregate summary
        summary = self._compute_summary(skill_gaps, experience_gaps)

        # 6. Build overall explanation
        explanation = self._build_explanation(summary, skill_gaps, experience_gaps)

        return CandidateJobSkillGapResponse(
            candidate_id=match_response.candidate_id,
            candidate_name=candidate.personal_info.name if candidate.personal_info else None,
            job_id=match_response.job_id,
            job_title=match_response.job_title or job.job_title,
            skill_gaps=skill_gaps,
            experience_gaps=experience_gaps,
            summary=summary,
            explanation=explanation,
        )

    def _calculate_skill_tenure(
        self,
        candidate: CandidateProfile,
        canonical_name: str,
        raw_name: str,
    ) -> float:
        """Calculates verified non-overlapping years for a specific skill from candidate work experience."""
        cand_intervals: List[Tuple[float, float]] = []
        names = {canonical_name.lower(), raw_name.lower()}
        lookup = lookup_canonical_skill(canonical_name)
        if lookup:
            names.add(lookup[0].lower())
            for a in lookup[2]:
                names.add(a.lower())

        for exp in candidate.experience:
            exp_text = f"{exp.title or ''} {exp.description or ''} {' '.join(exp.skills)}"
            if any(re.search(r"\b" + re.escape(n) + r"\b", exp_text, re.I) for n in names):
                s_yr = parse_date_to_year_float(exp.start_date, self.current_year)
                e_yr = parse_date_to_year_float(
                    exp.end_date if not exp.is_current else "Present", self.current_year
                )
                if s_yr is not None and e_yr is not None:
                    cand_intervals.append((s_yr, e_yr))

        return calculate_non_overlapping_tenure(cand_intervals)

    def _calculate_total_career_tenure(self, candidate: CandidateProfile) -> float:
        """Calculates total non-overlapping career experience across all dated roles."""
        cand_intervals: List[Tuple[float, float]] = []
        for exp in candidate.experience:
            s_yr = parse_date_to_year_float(exp.start_date, self.current_year)
            e_yr = parse_date_to_year_float(
                exp.end_date if not exp.is_current else "Present", self.current_year
            )
            if s_yr is not None and e_yr is not None:
                cand_intervals.append((s_yr, e_yr))
        return calculate_non_overlapping_tenure(cand_intervals)

    def _evaluate_skill_gaps(
        self,
        candidate: CandidateProfile,
        job: JobProfile,
        skill_matches: List[SingleRequirementMatch],
        semantic_map: Dict[str, SemanticMatchResult],
    ) -> List[SkillGapItem]:
        """
        Evaluates technical and structured skill requirements, deduplicating
        multiple mentions or aliases to the same canonical skill.
        """
        grouped_matches: Dict[str, List[SingleRequirementMatch]] = {}
        for m in skill_matches:
            req_name = m.requirement.name
            lookup = lookup_canonical_skill(req_name)
            canonical_name = lookup[0] if lookup else req_name
            key = canonical_name.lower()
            if key not in grouped_matches:
                grouped_matches[key] = []
            grouped_matches[key].append(m)

        skill_gaps: List[SkillGapItem] = []

        for key, matches_for_key in grouped_matches.items():
            rep_req = matches_for_key[0].requirement
            lookup = lookup_canonical_skill(rep_req.name)
            canonical_name = lookup[0] if lookup else rep_req.name
            skill_name = rep_req.name
            category = rep_req.category or (lookup[1] if lookup else "other")

            # Priority precedence: must_have takes precedence over nice_to_have
            is_must_have = any(m.requirement.priority == "must_have" for m in matches_for_key)
            priority: RequirementPriority = "must_have" if is_must_have else "nice_to_have"

            # Minimum years: maximum required tenure across occurrences
            min_years_list = [
                m.requirement.minimum_years
                for m in matches_for_key
                if m.requirement.minimum_years is not None
            ]
            max_min_years = max(min_years_list) if min_years_list else None

            # Evidence consolidation (grounded, non-fabricated, deduplicated)
            cand_evidence_set: List[str] = []
            for m in matches_for_key:
                for ev in m.candidate_evidence:
                    if ev and ev not in cand_evidence_set:
                        cand_evidence_set.append(ev)

            job_evidence_set: List[str] = []
            for m in matches_for_key:
                for ev in m.requirement_evidence:
                    if ev and ev not in job_evidence_set:
                        job_evidence_set.append(ev)
                if m.requirement.context and m.requirement.context not in job_evidence_set:
                    job_evidence_set.append(m.requirement.context)

            # Supporting semantic evidence lookup
            sem_res = (
                semantic_map.get(f"skill_{canonical_name}".lower())
                or semantic_map.get(f"skill_{skill_name}".lower())
                or semantic_map.get(canonical_name.lower())
                or semantic_map.get(skill_name.lower())
            )

            # Calculate candidate verified tenure for this skill
            cand_skill_years = self._calculate_skill_tenure(candidate, canonical_name, skill_name)

            # Determine authoritative deterministic status across matches for this skill
            all_statuses = [m.status for m in matches_for_key]
            if MatchStatus.MATCHED in all_statuses:
                if max_min_years and max_min_years > 0:
                    if cand_skill_years >= max_min_years:
                        det_status = MatchStatus.MATCHED
                        match_method = MatchMethod.EXPERIENCE_VERIFIED
                    elif cand_skill_years > 0:
                        det_status = MatchStatus.PARTIAL
                        match_method = MatchMethod.EXPERIENCE_INSUFFICIENT
                    else:
                        det_status = MatchStatus.NOT_EVALUABLE
                        match_method = MatchMethod.NOT_EVALUABLE
                else:
                    det_status = MatchStatus.MATCHED
                    match_method = next(m.match_method for m in matches_for_key if m.status == MatchStatus.MATCHED)
            elif MatchStatus.PARTIAL in all_statuses:
                det_status = MatchStatus.PARTIAL
                match_method = next(m.match_method for m in matches_for_key if m.status == MatchStatus.PARTIAL)
            elif MatchStatus.NOT_EVALUABLE in all_statuses:
                det_status = MatchStatus.NOT_EVALUABLE
                match_method = MatchMethod.NOT_EVALUABLE
            else:
                det_status = MatchStatus.UNMATCHED
                match_method = MatchMethod.UNMATCHED

            # Map to SkillGapStatus
            # RULE 6: High semantic similarity CANNOT override deterministic missing status!
            if det_status == MatchStatus.MATCHED:
                gap_status = SkillGapStatus.SATISFIED
                required_val = f"{max_min_years:.1f} years" if max_min_years else "Demonstrated skill"
                candidate_val = (
                    f"~{cand_skill_years:.1f} years verified"
                    if (max_min_years and cand_skill_years > 0)
                    else "Verified in candidate profile"
                )
                shortfall_val = None
                explanation = f"Candidate satisfies skill requirement '{canonical_name}' with verified evidence."
                if sem_res and sem_res.similarity is not None:
                    explanation += f" Semantic alignment: {sem_res.similarity:.2f}."
            elif det_status == MatchStatus.PARTIAL:
                gap_status = SkillGapStatus.INSUFFICIENT
                if max_min_years and max_min_years > 0:
                    shortfall_float = round(max(0.0, max_min_years - cand_skill_years), 1)
                    required_val = f"{max_min_years:.1f} years"
                    candidate_val = f"~{cand_skill_years:.1f} years"
                    shortfall_val = f"{shortfall_float:.1f} years"
                    explanation = (
                        f"Candidate possesses verified skill '{canonical_name}', but verified duration (~{cand_skill_years:.1f} years) "
                        f"falls short of the required {max_min_years:.1f} years by {shortfall_val}."
                    )
                else:
                    required_val = "Primary verified skill"
                    candidate_val = "Mentioned in projects/experience only"
                    shortfall_val = "Lacks primary skill listing"
                    explanation = (
                        f"Skill '{canonical_name}' is mentioned in projects or experience descriptions, "
                        f"but is not listed as a primary verified skill."
                    )
            elif det_status == MatchStatus.NOT_EVALUABLE:
                gap_status = SkillGapStatus.NOT_EVALUABLE
                required_val = f"{max_min_years:.1f}+ years" if max_min_years else "Verifiable tenure"
                candidate_val = "Skill listed without dated role tenure"
                shortfall_val = None
                explanation = (
                    f"Candidate possesses skill '{canonical_name}', but specific duration cannot be verified "
                    f"from dated roles without speculation."
                )
            else:  # UNMATCHED
                gap_status = SkillGapStatus.MISSING
                required_val = f"{max_min_years:.1f} years" if max_min_years else "Demonstrated skill"
                candidate_val = None
                shortfall_val = None
                priority_str = priority.value if hasattr(priority, "value") else str(priority)
                explanation = f"No verifiable candidate evidence found for required skill '{canonical_name}' ({priority_str})."
                if sem_res and sem_res.similarity is not None and sem_res.similarity >= 0.55:
                    matched_text = sem_res.candidate_evidence or sem_res.candidate_text or "related background"
                    explanation += (
                        f" Supporting semantic evidence: Conceptually related candidate evidence '{matched_text}' "
                        f"(cosine similarity: {sem_res.similarity:.2f}) was detected, but cannot substitute for required skill."
                    )

            item = SkillGapItem(
                requirement_id=f"skill_{canonical_name}",
                skill_name=skill_name,
                canonical_skill_name=canonical_name,
                category=category,
                priority=priority,
                status=gap_status,
                required_value=required_val,
                candidate_value=candidate_val,
                shortfall=shortfall_val,
                candidate_evidence=cand_evidence_set,
                job_evidence=job_evidence_set,
                explanation=explanation,
                deterministic_match_status=det_status,
                match_method=match_method,
                semantic_similarity=round(sem_res.similarity, 4) if (sem_res and sem_res.similarity is not None) else None,
                semantic_status=sem_res.semantic_status if sem_res else None,
                semantic_evidence=sem_res.candidate_evidence if sem_res else None,
            )
            skill_gaps.append(item)

        return skill_gaps

    def _evaluate_experience_gaps(
        self,
        candidate: CandidateProfile,
        job: JobProfile,
        experience_matches: List[SingleRequirementMatch],
    ) -> List[ExperienceGapItem]:
        """
        Evaluates general career experience requirements.
        General career tenure is kept strictly separate from skill gaps (Section 9).
        """
        experience_gaps: List[ExperienceGapItem] = []
        cand_total_years = self._calculate_total_career_tenure(candidate)

        for m in experience_matches:
            req_ref = m.requirement
            req_text = req_ref.context or req_ref.name
            priority = req_ref.priority
            req_years = req_ref.minimum_years

            cand_ev = list(m.candidate_evidence)
            job_ev = list(m.requirement_evidence)
            if req_ref.context and req_ref.context not in job_ev:
                job_ev.append(req_ref.context)

            if req_years is not None and req_years > 0:
                if cand_total_years >= req_years:
                    status = SkillGapStatus.SATISFIED
                    shortfall_years = 0.0
                    explanation = (
                        f"Candidate total career tenure (~{cand_total_years:.1f} years) meets or exceeds "
                        f"required {req_years:.1f} years."
                    )
                elif cand_total_years > 0:
                    status = SkillGapStatus.INSUFFICIENT
                    shortfall_years = round(req_years - cand_total_years, 1)
                    explanation = (
                        f"Candidate total career tenure (~{cand_total_years:.1f} years) falls short of "
                        f"required {req_years:.1f} years by {shortfall_years:.1f} years."
                    )
                else:
                    status = SkillGapStatus.MISSING
                    shortfall_years = req_years
                    explanation = (
                        f"No dated work experience records found to satisfy {req_years:.1f} years experience requirement."
                    )
            else:
                if m.status == MatchStatus.MATCHED:
                    status = SkillGapStatus.SATISFIED
                    shortfall_years = 0.0
                    explanation = "Candidate satisfies experience requirement."
                elif m.status == MatchStatus.PARTIAL:
                    status = SkillGapStatus.INSUFFICIENT
                    shortfall_years = None
                    explanation = m.reason or "Candidate partially satisfies experience requirement."
                elif m.status == MatchStatus.NOT_EVALUABLE:
                    status = SkillGapStatus.NOT_EVALUABLE
                    shortfall_years = None
                    explanation = m.reason or "Experience requirement cannot be reliably evaluated."
                else:
                    status = SkillGapStatus.MISSING
                    shortfall_years = None
                    explanation = m.reason or "No candidate evidence found for experience requirement."

            item = ExperienceGapItem(
                requirement_id=f"exp_{abs(hash(req_text)) % 1000000:06d}",
                requirement_text=req_text,
                priority=priority,
                status=status,
                required_years=req_years,
                candidate_years=round(cand_total_years, 1) if cand_total_years > 0 else 0.0,
                shortfall_years=shortfall_years,
                candidate_evidence=cand_ev,
                job_evidence=job_ev,
                explanation=explanation,
            )
            experience_gaps.append(item)

        return experience_gaps

    def _compute_summary(
        self,
        skill_gaps: List[SkillGapItem],
        experience_gaps: List[ExperienceGapItem],
    ) -> SkillGapSummary:
        """
        Computes aggregate summary of gaps across skills and experience.
        Guarantees that must_have_gaps strictly represents missing or insufficient
        must-have skills, excluding not_evaluable items (Section 11).
        """
        total_skills = len(skill_gaps)
        satisfied_skills = sum(1 for g in skill_gaps if g.status == SkillGapStatus.SATISFIED)
        missing_skills = sum(1 for g in skill_gaps if g.status == SkillGapStatus.MISSING)
        insufficient_skills = sum(1 for g in skill_gaps if g.status == SkillGapStatus.INSUFFICIENT)
        not_evaluable_skills = sum(1 for g in skill_gaps if g.status == SkillGapStatus.NOT_EVALUABLE)

        # CRITICAL INVARIANT: must_have_gaps = missing + insufficient (NOT not_evaluable)
        must_have_gaps = sum(
            1 for g in skill_gaps
            if g.priority == "must_have" and g.status in (SkillGapStatus.MISSING, SkillGapStatus.INSUFFICIENT)
        )
        nice_to_have_gaps = sum(
            1 for g in skill_gaps
            if g.priority == "nice_to_have" and g.status in (SkillGapStatus.MISSING, SkillGapStatus.INSUFFICIENT)
        )
        must_have_satisfied = sum(
            1 for g in skill_gaps
            if g.priority == "must_have" and g.status == SkillGapStatus.SATISFIED
        )
        nice_to_have_satisfied = sum(
            1 for g in skill_gaps
            if g.priority == "nice_to_have" and g.status == SkillGapStatus.SATISFIED
        )

        total_exp = len(experience_gaps)
        exp_gaps_count = sum(
            1 for e in experience_gaps
            if e.status in (SkillGapStatus.MISSING, SkillGapStatus.INSUFFICIENT)
        )

        return SkillGapSummary(
            total_skill_requirements=total_skills,
            satisfied_count=satisfied_skills,
            missing_count=missing_skills,
            insufficient_count=insufficient_skills,
            not_evaluable_count=not_evaluable_skills,
            must_have_gaps=must_have_gaps,
            nice_to_have_gaps=nice_to_have_gaps,
            must_have_satisfied=must_have_satisfied,
            nice_to_have_satisfied=nice_to_have_satisfied,
            total_experience_requirements=total_exp,
            experience_gaps_count=exp_gaps_count,
        )

    def _build_explanation(
        self,
        summary: SkillGapSummary,
        skill_gaps: List[SkillGapItem],
        experience_gaps: List[ExperienceGapItem],
    ) -> str:
        """Constructs an audit-compliant, deterministic overview of gap findings."""
        lines = [
            f"Skill Gap Analysis: {summary.total_skill_requirements} skill requirement(s) evaluated — "
            f"{summary.satisfied_count} satisfied, {summary.missing_count} missing, "
            f"{summary.insufficient_count} insufficient, {summary.not_evaluable_count} not evaluable."
        ]

        if summary.must_have_gaps > 0:
            missing_must = [
                g.canonical_skill_name or g.skill_name
                for g in skill_gaps
                if g.priority == "must_have" and g.status == SkillGapStatus.MISSING
            ]
            insufficient_must = [
                g.canonical_skill_name or g.skill_name
                for g in skill_gaps
                if g.priority == "must_have" and g.status == SkillGapStatus.INSUFFICIENT
            ]
            details = []
            if missing_must:
                details.append(f"missing: {', '.join(missing_must)}")
            if insufficient_must:
                details.append(f"insufficient: {', '.join(insufficient_must)}")
            lines.append(f"Critical Gaps: {summary.must_have_gaps} mandatory must-have gap(s) ({'; '.join(details)}).")
        else:
            lines.append("All mandatory must-have skill requirements are satisfied.")

        if summary.experience_gaps_count > 0:
            lines.append(f"Experience: {summary.experience_gaps_count} general career tenure requirement(s) not satisfied.")

        return " ".join(lines)


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------
_analyzer_instance: Optional[SkillGapAnalyzer] = None


def get_skill_gap_analyzer(current_year: float = 2026.0) -> SkillGapAnalyzer:
    global _analyzer_instance
    if _analyzer_instance is None or _analyzer_instance.current_year != current_year:
        _analyzer_instance = SkillGapAnalyzer(current_year=current_year)
    return _analyzer_instance


def analyze_skill_gaps(
    candidate: CandidateProfile,
    job: JobProfile,
    match_response: Optional[CandidateJobMatchResponse] = None,
    include_semantic: bool = True,
    current_year: float = 2026.0,
) -> CandidateJobSkillGapResponse:
    """Convenience function to analyze skill gaps between candidate and job."""
    analyzer = get_skill_gap_analyzer(current_year=current_year)
    return analyzer.analyze(
        candidate=candidate,
        job=job,
        match_response=match_response,
        include_semantic=include_semantic,
    )
