import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from backend.app.schemas import (
    CandidateProfile,
    JobProfile,
    CandidateJobMatchResponse,
    CandidateJobScoreResponse,
    CandidateJobSkillGapResponse,
    LLMExplanationResponse,
    RequirementExplanationItem,
    SkillGapRecommendationItem,
    ScoringWeights,
)
from backend.app.ai.llm_client import BaseLLMClient, get_llm_client, LLMError, LLMUnavailableError
from backend.app.ai.validators import validate_llm_json, LLMValidationError

logger = logging.getLogger(__name__)

# Path to the versioned prompt template
PROMPT_PATH = Path(__file__).resolve().parent.parent / "ai" / "prompts" / "llm_explanation.txt"


class LLMExplanationService:
    """
    Service responsible for generating evidence-grounded human explanations and
    personalized skill-gap recommendations from structured Phase 6-9 evaluation results.
    
    CRITICAL PRINCIPLE:
    The LLM is strictly an explanation and recommendation layer. It consumes facts
    produced by earlier deterministic, semantic, scoring, and gap engines, and NEVER
    modifies or recalculates underlying statuses, scores, or requirements.
    """

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        self.llm_client = llm_client or get_llm_client()
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Loads prompt template from disk with fallback."""
        if PROMPT_PATH.exists():
            return PROMPT_PATH.read_text(encoding="utf-8")
        logger.warning(f"Prompt template file not found at {PROMPT_PATH}; using default.")
        return (
            "You are an evidence-grounded resume analysis assistant.\n"
            "Use only the provided structured evidence. Do not invent facts.\n"
            "Explain requirement statuses and generate recommendations only for identified gaps."
        )

    def build_structured_context(
        self,
        candidate: CandidateProfile,
        job: JobProfile,
        matching_result: CandidateJobMatchResponse,
        scoring_result: Optional[CandidateJobScoreResponse],
        skill_gap_result: CandidateJobSkillGapResponse,
        candidate_id: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Constructs an explicit, sanitized dictionary containing ONLY the evidence
        and metrics necessary for the LLM to generate an explanation and recommendations.
        """
        cand_name = "Candidate"
        if candidate.personal_info and candidate.personal_info.name:
            cand_name = candidate.personal_info.name

        context = {
            "candidate": {
                "candidate_id": candidate_id or matching_result.candidate_id,
                "name": cand_name,
                "summary": candidate.summary,
            },
            "job": {
                "job_id": job_id or matching_result.job_id,
                "job_title": job.job_title or matching_result.job_title or "Target Position",
            },
            "matching": {
                "matches": [
                    {
                        "requirement_id": getattr(m.requirement, "requirement_id", None) or f"{m.requirement.type}_{m.requirement.name}".replace(" ", "_"),
                        "type": m.requirement.type,
                        "name": m.requirement.name,
                        "priority": m.requirement.priority,
                        "required_value": (
                            f"{m.requirement.minimum_years} years"
                            if getattr(m.requirement, "minimum_years", None)
                            else getattr(m.requirement, "context", None)
                        ),
                        "status": m.status.value if hasattr(m.status, "value") else str(m.status),
                        "match_method": m.match_method.value if hasattr(m.match_method, "value") else str(m.match_method),
                        "candidate_evidence": m.candidate_evidence,
                        "candidate_value": getattr(m, "candidate_value", None),
                        "explanation": getattr(m, "reason", None) or getattr(m, "explanation", ""),
                        "semantic_similarity": (
                            round(m.semantic_result.similarity, 4)
                            if m.semantic_result and m.semantic_result.similarity is not None
                            else None
                        ),
                        "semantic_evidence": (
                            m.semantic_result.candidate_evidence
                            if m.semantic_result
                            else None
                        ),
                    }
                    for m in matching_result.matches
                ],

                "summary": matching_result.summary.model_dump(),
            },
            "score": (
                {
                    "candidate_fit_score": scoring_result.candidate_fit_score,
                    "percentage_score": scoring_result.percentage_score,
                    "rule_fit_score": scoring_result.rule_fit_score,
                    "semantic_fit_score": scoring_result.semantic_fit_score,
                    "experience_fit_score": scoring_result.experience_fit_score,
                    "llm_fit_score": scoring_result.llm_fit_score,
                    "all_must_haves_satisfied": scoring_result.all_must_haves_satisfied,
                }
                if scoring_result
                else None
            ),
            "gaps": {
                "skill_gaps": [
                    {
                        "requirement_id": sg.requirement_id,
                        "skill_name": sg.skill_name,
                        "canonical_skill_name": sg.canonical_skill_name,
                        "category": sg.category,
                        "priority": sg.priority,
                        "status": sg.status.value if hasattr(sg.status, "value") else str(sg.status),
                        "required_value": sg.required_value,
                        "candidate_value": sg.candidate_value,
                        "shortfall": sg.shortfall,
                        "candidate_evidence": sg.candidate_evidence,
                        "job_evidence": sg.job_evidence,
                        "semantic_similarity": sg.semantic_similarity,
                        "semantic_evidence": sg.semantic_evidence,
                    }
                    for sg in skill_gap_result.skill_gaps
                ],
                "experience_gaps": [
                    {
                        "requirement_id": eg.requirement_id,
                        "requirement_text": eg.requirement_text,
                        "priority": eg.priority,
                        "status": eg.status.value if hasattr(eg.status, "value") else str(eg.status),
                        "required_years": eg.required_years,
                        "candidate_years": eg.candidate_years,
                        "shortfall_years": eg.shortfall_years,
                        "candidate_evidence": eg.candidate_evidence,
                        "job_evidence": eg.job_evidence,
                    }
                    for eg in skill_gap_result.experience_gaps
                ],
                "summary": skill_gap_result.summary.model_dump(),
            },
        }

        return context

    async def generate_explanation(
        self,
        candidate: CandidateProfile,
        job: JobProfile,
        matching_result: Optional[CandidateJobMatchResponse] = None,
        scoring_result: Optional[CandidateJobScoreResponse] = None,
        skill_gap_result: Optional[CandidateJobSkillGapResponse] = None,
        candidate_id: Optional[str] = None,
        job_id: Optional[str] = None,
        scoring_weights: Optional[ScoringWeights] = None,
        llm_fit_score: Optional[float] = None,
        include_semantic: bool = True,
    ) -> LLMExplanationResponse:
        """
        Executes end-to-end evidence-grounded LLM explanation and recommendation generation.
        Leverages previous phases if matching, scoring, or gap results are omitted.
        """
        # 1. Ensure Phase 6 deterministic matching result exists
        if matching_result is None:
            from backend.app.services.matching_engine import MatchingEngine
            engine = MatchingEngine()
            matching_result = engine.match_candidate_to_job(
                candidate=candidate,
                job=job,
                candidate_id=candidate_id,
                job_id=job_id,
                include_semantic=include_semantic,
            )

        # 2. Ensure Phase 9 skill-gap analysis result exists
        if skill_gap_result is None:
            from backend.app.services.skill_gap_analyzer import analyze_skill_gaps
            skill_gap_result = analyze_skill_gaps(
                candidate=candidate,
                job=job,
                match_response=matching_result,
                include_semantic=include_semantic,
            )

        # 3. Ensure Phase 8 hybrid scoring result exists
        if scoring_result is None:
            from backend.app.services.scoring_engine import get_scoring_engine
            scoring_engine = get_scoring_engine()
            scoring_result = scoring_engine.compute_score(
                match_response=matching_result,
                weights=scoring_weights,
                llm_fit_score=llm_fit_score,
            )

        # 4. Construct sanitized structured context
        context = self.build_structured_context(
            candidate=candidate,
            job=job,
            matching_result=matching_result,
            scoring_result=scoring_result,
            skill_gap_result=skill_gap_result,
            candidate_id=candidate_id,
            job_id=job_id,
        )

        # 5. Assemble prompt
        prompt = (
            f"{self.prompt_template}\n\n"
            f"STRUCTURED MATCHING AND GAP CONTEXT:\n"
            f"{json.dumps(context, indent=2)}\n"
        )

        # 6. Call LLM provider
        try:
            raw_response = await self.llm_client.generate(prompt=prompt, temperature=0.2)
        except Exception as e:
            logger.error(f"Error calling LLM provider for explanation: {str(e)}")
            raise

        # 7. Validate and parse structured output
        validated_response = validate_llm_json(raw_response, LLMExplanationResponse)

        # 8. Enrich identifiers if omitted by LLM
        if not validated_response.candidate_id:
            validated_response.candidate_id = candidate_id or matching_result.candidate_id
        if not validated_response.candidate_name:
            validated_response.candidate_name = (
                candidate.personal_info.name if candidate.personal_info else "Candidate"
            )
        if not validated_response.job_id:
            validated_response.job_id = job_id or matching_result.job_id
        if not validated_response.job_title:
            validated_response.job_title = job.job_title or matching_result.job_title

        return validated_response


async def generate_candidate_explanation(
    candidate: CandidateProfile,
    job: JobProfile,
    matching_result: Optional[CandidateJobMatchResponse] = None,
    scoring_result: Optional[CandidateJobScoreResponse] = None,
    skill_gap_result: Optional[CandidateJobSkillGapResponse] = None,
    candidate_id: Optional[str] = None,
    job_id: Optional[str] = None,
    scoring_weights: Optional[ScoringWeights] = None,
    llm_fit_score: Optional[float] = None,
    include_semantic: bool = True,
    llm_client: Optional[BaseLLMClient] = None,
) -> LLMExplanationResponse:
    """Convenience module function to generate candidate explanation."""
    service = LLMExplanationService(llm_client=llm_client)
    return await service.generate_explanation(
        candidate=candidate,
        job=job,
        matching_result=matching_result,
        scoring_result=scoring_result,
        skill_gap_result=skill_gap_result,
        candidate_id=candidate_id,
        job_id=job_id,
        scoring_weights=scoring_weights,
        llm_fit_score=llm_fit_score,
        include_semantic=include_semantic,
    )
