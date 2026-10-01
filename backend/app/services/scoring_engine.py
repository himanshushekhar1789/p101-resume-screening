"""
Phase 8: Multi-Layer Hybrid Fusion Scoring Engine for P_101 Resume Screening System.

Computes an explainable, configurable candidate-fit score combining:
1. Rule-based requirement fit (Phase 6 deterministic matching, priority-weighted)
2. Semantic skill fit (Phase 7 dense vector cosine similarity, priority-weighted)
3. Experience fit (Phase 6 verifiable non-overlapping tenure & proportional duration)
4. LLM-supported fit (Provider abstraction / placeholder with dynamic weight renormalization)

Guarantees:
- Canonical range [0.0, 1.0]
- Independent hard must-have safety signal (does not override scores or auto-reject)
- Dynamic weight renormalization when components are unavailable
- Zero candidate ranking, zero shortlisting, zero hiring decisions
"""

import re
import logging
from typing import Optional, List, Dict, Any, Tuple

from backend.app.config import get_settings
from backend.app.schemas import (
    CandidateProfile,
    JobProfile,
    CandidateJobMatchResponse,
    SingleRequirementMatch,
    MatchStatus,
    MatchMethod,
    RequirementPriority,
    SemanticStatus,
    SemanticMatchResult,
    ScoringWeights,
    ScoreComponent,
    RequirementScoreContribution,
    HybridScoreBreakdown,
    CandidateJobScoreResponse,
)
from backend.app.services.matching_engine import MatchingEngine

logger = logging.getLogger(__name__)


def extract_duration_years(text: str) -> Optional[float]:
    """Extract decimal years float from reasoning or evidence text (e.g. '~5.0 years' -> 5.0)."""
    if not text:
        return None
    m = re.search(r"~?\s*(\d+(?:\.\d+)?)\s*(?:verified\s*)?years?", text, re.I)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return None
    return None


class ScoringEngine:
    """
    Core service responsible for combining deterministic matching (Phase 6),
    semantic similarity (Phase 7), experience verification, and optional LLM fit
    into a calibrated, explainable CandidateJobScoreResponse.
    """

    def __init__(
        self,
        default_weights: Optional[ScoringWeights] = None,
        not_evaluable_policy: Optional[str] = None,
    ):
        settings = get_settings()
        self.default_weights = default_weights or ScoringWeights(
            rule_weight=settings.weight_rule_fit,
            semantic_weight=settings.weight_semantic_fit,
            experience_weight=settings.weight_experience_fit,
            llm_weight=settings.weight_llm_fit,
        )
        self.not_evaluable_policy = not_evaluable_policy or settings.not_evaluable_policy

    def resolve_weights(self, custom_weights: Optional[ScoringWeights] = None) -> ScoringWeights:
        """Validate and return active scoring weights."""
        if custom_weights is not None:
            return custom_weights
        return self.default_weights

    # -----------------------------------------------------------------------
    # Component 1: Rule Fit
    # -----------------------------------------------------------------------
    def calculate_rule_fit(
        self,
        matches: List[SingleRequirementMatch],
        rule_weight: float,
    ) -> Tuple[ScoreComponent, List[RequirementScoreContribution]]:
        """
        Calculates priority-weighted deterministic requirement satisfaction from Phase 6.
        - Evaluates applicable non-experience deterministic requirements:
          skills, education, certifications, and other deterministic requirements.
        - Experience requirements (type == "experience") are strictly excluded
          because career tenure / required years is represented exclusively by Experience Fit.
        - must_have weight: 1.0
        - nice_to_have weight: 0.5
        - matched: 1.0
        - partial: 0.5
        - unmatched: 0.0
        - not_evaluable: excluded from denominator (under default 'exclude' policy)
        """
        contributions: List[RequirementScoreContribution] = []
        evaluable_weighted_values: List[float] = []
        evaluable_priority_weights: List[float] = []

        matched_count = 0
        partial_count = 0
        unmatched_count = 0
        not_evaluable_count = 0
        must_have_count = 0
        nice_to_have_count = 0

        for m in matches:
            req = m.requirement
            priority = req.priority or "must_have"
            priority_weight = 1.0 if priority == "must_have" else 0.5
            status = m.status

            # Check semantic similarity if attached
            sem_sim: Optional[float] = None
            if m.semantic_result and m.semantic_result.similarity is not None:
                sem_sim = round(m.semantic_result.similarity, 4)

            # ARCHITECTURAL RULE (Phase 8.1):
            # Rule Fit evaluates evaluable non-experience deterministic requirements.
            # Experience requirements (type == "experience") are strictly excluded from Rule Fit
            # because career tenure / required years is represented independently by Experience Fit.
            if req.type == "experience":
                is_evaluable = (status != MatchStatus.NOT_EVALUABLE)
                contributions.append(
                    RequirementScoreContribution(
                        requirement_id=f"{req.type}_{req.name}".replace(" ", "_"),
                        name=req.name,
                        type=req.type,
                        priority=priority,
                        status=status,
                        status_value=None,
                        priority_weight=priority_weight,
                        weighted_value=None,
                        evaluable=is_evaluable,
                        semantic_similarity=sem_sim,
                        reason=f"Excluded from rule_fit (handled independently by experience_fit): {m.reason or ''}".strip(),
                    )
                )
                continue

            if priority == "must_have":
                must_have_count += 1
            else:
                nice_to_have_count += 1

            evaluable = True
            status_value: Optional[float] = None
            weighted_value: Optional[float] = None

            if status == MatchStatus.MATCHED:
                matched_count += 1
                status_value = 1.0
            elif status == MatchStatus.PARTIAL:
                partial_count += 1
                status_value = 0.5
            elif status == MatchStatus.UNMATCHED:
                unmatched_count += 1
                status_value = 0.0
            elif status == MatchStatus.NOT_EVALUABLE:
                not_evaluable_count += 1
                if self.not_evaluable_policy == "zero":
                    status_value = 0.0
                else:
                    evaluable = False
                    status_value = None

            if evaluable and status_value is not None:
                weighted_val = status_value * priority_weight
                weighted_value = round(weighted_val, 4)
                evaluable_weighted_values.append(weighted_val)
                evaluable_priority_weights.append(priority_weight)

            contributions.append(
                RequirementScoreContribution(
                    requirement_id=f"{req.type}_{req.name}".replace(" ", "_"),
                    name=req.name,
                    type=req.type,
                    priority=priority,
                    status=status,
                    status_value=status_value,
                    priority_weight=priority_weight,
                    weighted_value=weighted_value,
                    evaluable=evaluable,
                    semantic_similarity=sem_sim,
                    reason=m.reason,
                )
            )

        sum_priority_weights = sum(evaluable_priority_weights)
        evaluable_count = len(evaluable_weighted_values)

        if sum_priority_weights > 0:
            raw_score = sum(evaluable_weighted_values) / sum_priority_weights
            score = round(min(1.0, max(0.0, raw_score)), 4)
            available = True
            explanation = (
                f"Rule fit evaluated {evaluable_count} non-experience requirement(s) ({must_have_count} must-have, "
                f"{nice_to_have_count} nice-to-have). Satisfied {matched_count} fully, {partial_count} partially, "
                f"{unmatched_count} unmatched ({not_evaluable_count} not evaluable)."
            )
        else:
            score = None
            available = False
            explanation = "No evaluable non-experience requirements found to compute rule fit."

        component = ScoreComponent(
            name="rule_fit",
            score=score,
            configured_weight=rule_weight,
            effective_weight=rule_weight if available else 0.0,
            weighted_contribution=round(score * rule_weight, 4) if (available and score is not None) else 0.0,
            available=available,
            explanation=explanation,
            evaluable_count=evaluable_count,
            not_evaluable_count=not_evaluable_count,
        )

        return component, contributions

    # -----------------------------------------------------------------------
    # Component 2: Semantic Fit
    # -----------------------------------------------------------------------
    def calculate_semantic_fit(
        self,
        matches: List[SingleRequirementMatch],
        semantic_matches: Optional[List[SemanticMatchResult]],
        semantic_weight: float,
    ) -> ScoreComponent:
        """
        Calculates priority-weighted average of raw cosine similarity scores from Phase 7.
        - Evaluates applicable non-experience semantic requirements (skills, education,
          certifications, other).
        - Experience requirements (category == 'experience' or id starting with 'exp_')
          are strictly excluded from numerical Semantic Fit to prevent double-counting
          with Experience Fit.
        - must_have weight: 1.0
        - nice_to_have weight: 0.5
        - Uses raw similarity (clipped to [0.0, 1.0]).
        - If no semantic results exist or all are not_evaluable/experience, marked available=False.
        """
        # Pool all available semantic results from matches or direct list
        results_map: Dict[str, SemanticMatchResult] = {}

        if semantic_matches:
            for sm in semantic_matches:
                results_map[sm.requirement_id] = sm

        for m in matches:
            if m.semantic_result:
                results_map[m.semantic_result.requirement_id] = m.semantic_result

        if not results_map:
            return ScoreComponent(
                name="semantic_fit",
                score=None,
                configured_weight=semantic_weight,
                effective_weight=0.0,
                weighted_contribution=0.0,
                available=False,
                explanation="Semantic matching results are unavailable or disabled by configuration.",
                evaluable_count=0,
                not_evaluable_count=len(matches),
            )

        evaluable_sims: List[float] = []
        evaluable_weights: List[float] = []
        not_evaluable_count = 0

        for r in results_map.values():
            # ARCHITECTURAL RULE (Phase 8.2):
            # Exclude experience requirements from the numerical Semantic Fit calculation.
            # Career tenure and skill duration are evaluated exclusively by Experience Fit.
            if r.category == "experience" or r.requirement_id.startswith("exp_"):
                continue

            if r.semantic_status == SemanticStatus.SEMANTIC_NOT_EVALUABLE:
                not_evaluable_count += 1
                continue

            priority = r.priority or "must_have"
            p_weight = 1.0 if priority == "must_have" else 0.5
            # Cosine similarity clipped to [0.0, 1.0] (negative similarity treated as zero correlation)
            sim = min(1.0, max(0.0, float(r.similarity)))

            evaluable_sims.append(sim * p_weight)
            evaluable_weights.append(p_weight)

        evaluable_count = len(evaluable_sims)
        sum_weights = sum(evaluable_weights)

        if sum_weights > 0:
            raw_score = sum(evaluable_sims) / sum_weights
            score = round(min(1.0, max(0.0, raw_score)), 4)
            available = True
            explanation = (
                f"Semantic fit evaluated {evaluable_count} non-experience requirement(s) using dense vector similarity "
                f"yielding an average weighted similarity of {score:.2f} ({not_evaluable_count} not evaluable)."
            )
        else:
            score = None
            available = False
            explanation = "No semantically evaluable non-experience requirements available."

        return ScoreComponent(
            name="semantic_fit",
            score=score,
            configured_weight=semantic_weight,
            effective_weight=semantic_weight if available else 0.0,
            weighted_contribution=round((score or 0.0) * semantic_weight, 4) if available else 0.0,
            available=available,
            explanation=explanation,
            evaluable_count=evaluable_count,
            not_evaluable_count=not_evaluable_count,
        )

    # -----------------------------------------------------------------------
    # Component 3: Experience Fit
    # -----------------------------------------------------------------------
    def calculate_experience_fit(
        self,
        matches: List[SingleRequirementMatch],
        experience_weight: float,
        contributions_map: Optional[Dict[str, RequirementScoreContribution]] = None,
    ) -> ScoreComponent:
        """
        Calculates experience fit strictly from Phase 6 deterministic tenure evidence.
        - For explicit years requirements: candidate_years / required_years (capped at 1.0).
        - Excess experience above requirement is NOT rewarded beyond 1.0.
        - unmatched: 0.0
        - not_evaluable: excluded from denominator.
        - Multiple experience requirements are priority-weighted.
        """
        # Find matches with type == "experience" or explicit tenure verification methods
        exp_matches: List[SingleRequirementMatch] = []
        for m in matches:
            is_exp_type = m.requirement.type == "experience"
            has_exp_method = m.match_method in [
                MatchMethod.EXPERIENCE_VERIFIED,
                MatchMethod.EXPERIENCE_INSUFFICIENT,
            ]
            has_min_years = (
                m.requirement.minimum_years is not None and m.requirement.minimum_years > 0
            )

            if is_exp_type or has_exp_method or has_min_years:
                exp_matches.append(m)

        if not exp_matches:
            return ScoreComponent(
                name="experience_fit",
                score=None,
                configured_weight=experience_weight,
                effective_weight=0.0,
                weighted_contribution=0.0,
                available=False,
                explanation="No explicit experience or tenure duration requirements specified in the job profile.",
                evaluable_count=0,
                not_evaluable_count=0,
            )

        evaluable_scores: List[float] = []
        evaluable_weights: List[float] = []
        not_evaluable_count = 0

        for m in exp_matches:
            req = m.requirement
            priority = req.priority or "must_have"
            p_weight = 1.0 if priority == "must_have" else 0.5

            if m.status == MatchStatus.NOT_EVALUABLE:
                not_evaluable_count += 1
                continue

            indiv_score: float = 0.0
            ratio: Optional[float] = None

            # Attempt to extract candidate years and required years
            required_years = req.minimum_years
            if required_years is None and req.context:
                required_years = extract_duration_years(req.context)

            candidate_years: Optional[float] = None
            if m.reason:
                candidate_years = extract_duration_years(m.reason)
            if candidate_years is None and m.candidate_evidence:
                candidate_years = extract_duration_years(" ".join(m.candidate_evidence))

            if required_years is not None and required_years > 0:
                if candidate_years is not None:
                    ratio = candidate_years / required_years
                    indiv_score = min(1.0, max(0.0, ratio))
                elif m.status == MatchStatus.MATCHED:
                    indiv_score = 1.0
                    ratio = 1.0
                elif m.status == MatchStatus.PARTIAL:
                    indiv_score = 0.5
                    ratio = 0.5
                else:
                    indiv_score = 0.0
                    ratio = 0.0
            else:
                # Qualitative experience requirement without numeric years
                if m.status == MatchStatus.MATCHED:
                    indiv_score = 1.0
                elif m.status == MatchStatus.PARTIAL:
                    indiv_score = 0.5
                else:
                    indiv_score = 0.0

            # Attach experience ratio to contribution trace if available
            req_key = f"{req.type}_{req.name}".replace(" ", "_")
            if contributions_map and req_key in contributions_map:
                contributions_map[req_key].experience_ratio = (
                    round(ratio, 2) if ratio is not None else None
                )

            evaluable_scores.append(indiv_score * p_weight)
            evaluable_weights.append(p_weight)

        evaluable_count = len(evaluable_scores)
        sum_weights = sum(evaluable_weights)

        if sum_weights > 0:
            raw_score = sum(evaluable_scores) / sum_weights
            score = round(min(1.0, max(0.0, raw_score)), 4)
            available = True
            explanation = (
                f"Experience fit evaluated {evaluable_count} experience requirement(s) yielding "
                f"{score:.2f} proportional satisfaction ({not_evaluable_count} not evaluable)."
            )
        else:
            score = None
            available = False
            explanation = (
                f"All {len(exp_matches)} experience requirement(s) lacked verifiable duration (not evaluable)."
            )

        return ScoreComponent(
            name="experience_fit",
            score=score,
            configured_weight=experience_weight,
            effective_weight=experience_weight if available else 0.0,
            weighted_contribution=round((score or 0.0) * experience_weight, 4) if available else 0.0,
            available=available,
            explanation=explanation,
            evaluable_count=evaluable_count,
            not_evaluable_count=not_evaluable_count,
        )

    # -----------------------------------------------------------------------
    # Component 4: LLM Fit
    # -----------------------------------------------------------------------
    def calculate_llm_fit(
        self,
        llm_weight: float,
        explicit_score: Optional[float] = None,
    ) -> ScoreComponent:
        """
        Manages the LLM-supported fit component.
        By default, Phase 8 is deterministic; unless an explicit valid score is provided,
        this component is marked available=False and its weight is dynamically renormalized.
        """
        if explicit_score is not None:
            clamped = min(1.0, max(0.0, float(explicit_score)))
            score = round(clamped, 4)
            available = True
            explanation = f"LLM-supported fit score evaluated externally with score {score:.2f}."
        else:
            score = None
            available = False
            explanation = (
                "LLM-supported fit evaluation is disabled or unavailable by default in Phase 8 "
                "(deterministic execution mode)."
            )

        return ScoreComponent(
            name="llm_fit",
            score=score,
            configured_weight=llm_weight,
            effective_weight=llm_weight if available else 0.0,
            weighted_contribution=round((score or 0.0) * llm_weight, 4) if available else 0.0,
            available=available,
            explanation=explanation,
            evaluable_count=1 if available else 0,
            not_evaluable_count=0 if available else 1,
        )

    # -----------------------------------------------------------------------
    # Dynamic Weight Renormalization & Fusion
    # -----------------------------------------------------------------------
    def renormalize_and_fuse(
        self,
        components: Dict[str, ScoreComponent],
    ) -> Tuple[float, bool]:
        """
        Dynamically renormalizes configured weights across all available components:
            w'_k = w_k / sum_{j in available} w_j
        Computes the final candidate_fit_score:
            candidate_fit_score = sum_{k in available} (score_k * w'_k)
        """
        available_comps = [c for c in components.values() if c.available and c.score is not None]
        total_available_weight = sum(c.configured_weight for c in available_comps)

        weights_renormalized = False
        if abs(total_available_weight - 1.0) > 1e-4 and total_available_weight > 0:
            weights_renormalized = True

        overall_fit = 0.0
        if total_available_weight > 0:
            for c in components.values():
                if c.available and c.score is not None:
                    renormalized_w = c.configured_weight / total_available_weight
                    c.effective_weight = round(renormalized_w, 4)
                    c.weighted_contribution = round(c.score * renormalized_w, 4)
                    overall_fit += c.score * renormalized_w
                else:
                    c.effective_weight = 0.0
                    c.weighted_contribution = 0.0
        else:
            for c in components.values():
                c.effective_weight = 0.0
                c.weighted_contribution = 0.0

        clamped_overall = min(1.0, max(0.0, overall_fit))
        return round(clamped_overall, 4), weights_renormalized

    # -----------------------------------------------------------------------
    # Main Computation Pipeline
    # -----------------------------------------------------------------------
    def compute_score(
        self,
        match_response: CandidateJobMatchResponse,
        weights: Optional[ScoringWeights] = None,
        llm_fit_score: Optional[float] = None,
    ) -> CandidateJobScoreResponse:
        """
        Computes hybrid candidate-fit score given an existing CandidateJobMatchResponse.
        """
        resolved_weights = self.resolve_weights(weights)

        # 1. Calculate Rule Fit
        rule_comp, contributions = self.calculate_rule_fit(
            matches=match_response.matches,
            rule_weight=resolved_weights.rule_weight,
        )
        contribs_map = {c.requirement_id: c for c in contributions}

        # 2. Calculate Semantic Fit
        semantic_comp = self.calculate_semantic_fit(
            matches=match_response.matches,
            semantic_matches=match_response.semantic_matches,
            semantic_weight=resolved_weights.semantic_weight,
        )

        # 3. Calculate Experience Fit
        experience_comp = self.calculate_experience_fit(
            matches=match_response.matches,
            experience_weight=resolved_weights.experience_weight,
            contributions_map=contribs_map,
        )

        # 4. Calculate LLM Fit
        llm_comp = self.calculate_llm_fit(
            llm_weight=resolved_weights.llm_weight,
            explicit_score=llm_fit_score,
        )

        # 5. Dynamic Weight Renormalization & Fusion
        components_dict = {
            "rule_fit": rule_comp,
            "semantic_fit": semantic_comp,
            "experience_fit": experience_comp,
            "llm_fit": llm_comp,
        }

        candidate_fit_score, weights_renormalized = self.renormalize_and_fuse(components_dict)
        percentage_score = round(candidate_fit_score * 100, 2)

        # 6. Safety Signal: all_must_haves_satisfied
        # Evaluate must-have satisfaction directly from Phase 6 matches
        must_haves = [
            m for m in match_response.matches
            if (m.requirement.priority or "must_have") == "must_have"
        ]
        all_must_haves_satisfied = (
            len(must_haves) > 0 and all(m.status == MatchStatus.MATCHED for m in must_haves)
        )

        # Counts
        evaluated_reqs = sum(1 for c in contributions if c.evaluable)
        not_eval_reqs = sum(1 for c in contributions if not c.evaluable)

        # Explanation Summary
        summary_parts = [
            f"Overall Candidate Fit Score: {candidate_fit_score:.2f} ({percentage_score:.1f}%).",
            f"Rule Fit: {rule_comp.score if rule_comp.score is not None else 'N/A'} (effective weight: {rule_comp.effective_weight:.1%}).",
            f"Semantic Fit: {semantic_comp.score if semantic_comp.score is not None else 'N/A'} (effective weight: {semantic_comp.effective_weight:.1%}).",
            f"Experience Fit: {experience_comp.score if experience_comp.score is not None else 'N/A'} (effective weight: {experience_comp.effective_weight:.1%}).",
        ]
        if llm_comp.available:
            summary_parts.append(f"LLM Fit: {llm_comp.score:.2f} (effective weight: {llm_comp.effective_weight:.1%}).")
        else:
            summary_parts.append("LLM Fit: Unavailable (weights dynamically renormalized).")

        if all_must_haves_satisfied:
            summary_parts.append("All must-have requirements are satisfied.")
        else:
            summary_parts.append("One or more must-have requirements remain unsatisfied.")

        overall_explanation = " ".join(summary_parts)

        breakdown = HybridScoreBreakdown(
            rule_fit=rule_comp,
            semantic_fit=semantic_comp,
            experience_fit=experience_comp,
            llm_fit=llm_comp,
        )

        return CandidateJobScoreResponse(
            candidate_id=match_response.candidate_id,
            job_id=match_response.job_id,
            job_title=match_response.job_title,
            candidate_fit_score=candidate_fit_score,
            percentage_score=percentage_score,
            rule_fit_score=rule_comp.score,
            semantic_fit_score=semantic_comp.score,
            experience_fit_score=experience_comp.score,
            llm_fit_score=llm_comp.score,
            components=breakdown,
            requirement_contributions=contributions,
            all_must_haves_satisfied=all_must_haves_satisfied,
            evaluated_requirements=evaluated_reqs,
            not_evaluable_requirements=not_eval_reqs,
            weights_renormalized=weights_renormalized,
            explanation=overall_explanation,
        )

    def score_candidate_for_job(
        self,
        candidate: CandidateProfile,
        job: JobProfile,
        candidate_id: Optional[str] = None,
        job_id: Optional[str] = None,
        include_semantic: bool = True,
        weights: Optional[ScoringWeights] = None,
        llm_fit_score: Optional[float] = None,
    ) -> CandidateJobScoreResponse:
        """
        Executes end-to-end matching (Phase 6 + optional Phase 7) and computes the hybrid score.
        """
        matching_engine = MatchingEngine()
        match_response = matching_engine.match_candidate_to_job(
            candidate=candidate,
            job=job,
            candidate_id=candidate_id,
            job_id=job_id,
            include_semantic=include_semantic,
        )
        return self.compute_score(
            match_response=match_response,
            weights=weights,
            llm_fit_score=llm_fit_score,
        )


_global_scoring_engine: Optional[ScoringEngine] = None


def get_scoring_engine() -> ScoringEngine:
    """Singleton getter for global ScoringEngine instance."""
    global _global_scoring_engine
    if _global_scoring_engine is None:
        _global_scoring_engine = ScoringEngine()
    return _global_scoring_engine
