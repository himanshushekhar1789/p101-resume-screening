/**
 * P_101 Resume Screening System — API TypeScript Definitions
 * Directly aligned with FastAPI Pydantic schemas in backend/app/schemas.py
 */

export type RequirementPriority = 'must_have' | 'nice_to_have';
export type RequirementType = 'skill' | 'experience' | 'education' | 'certification' | 'other';

export type MatchStatus =
  | 'satisfied'
  | 'partially_satisfied'
  | 'unmatched'
  | 'not_evaluable';

export type MatchMethod =
  | 'canonical_exact'
  | 'alias_normalized'
  | 'version_compatible'
  | 'experience_verified'
  | 'experience_insufficient'
  | 'education_match'
  | 'education_partial'
  | 'certification_match'
  | 'text_evidence'
  | 'unmatched'
  | 'not_evaluable';

export type SkillGapStatus =
  | 'satisfied'
  | 'missing'
  | 'insufficient'
  | 'not_evaluable';

export type SemanticStatus =
  | 'high_similarity'
  | 'moderate_similarity'
  | 'low_similarity'
  | 'no_match';

// --- Candidate Profile ---
export interface CandidateSkill {
  name: string;
  category?: string | null;
  years_of_experience?: number | null;
  evidence?: string | null;
}

export interface WorkExperience {
  title?: string | null;
  company?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  duration_years?: number | null;
  description?: string | null;
  responsibilities?: string[] | null;
  technologies?: string[] | null;
}

export interface Education {
  degree?: string | null;
  field?: string | null;
  institution?: string | null;
  year?: number | null;
}

export interface Certification {
  name: string;
  issuer?: string | null;
  year?: number | null;
}

export interface CandidateProfile {
  name?: string | null;
  email?: string | null;
  phone?: string | null;
  total_experience_years?: number | null;
  skills: CandidateSkill[];
  experience: WorkExperience[];
  education: Education[];
  certifications: Certification[];
  summary?: string | null;
}

// --- Job Profile ---
export interface JobSkillRequirement {
  name: string;
  priority: RequirementPriority;
  category?: string | null;
  minimum_years?: number | null;
  evidence?: string | null;
}

export interface JobExperienceRequirement {
  description: string;
  priority: RequirementPriority;
  minimum_years?: number | null;
  evidence?: string | null;
}

export interface JobEducationRequirement {
  degree?: string | null;
  field?: string | null;
  priority: RequirementPriority;
  evidence?: string | null;
}

export interface JobCertificationRequirement {
  name: string;
  priority: RequirementPriority;
  evidence?: string | null;
}

export interface JobProfile {
  job_title: string;
  department?: string | null;
  skills: JobSkillRequirement[];
  experience: JobExperienceRequirement[];
  education: JobEducationRequirement[];
  certifications: JobCertificationRequirement[];
  responsibilities: string[];
  summary?: string | null;
}

export interface JobAnalysisMetadata {
  character_count: number;
  word_count: number;
  source_type: string;
  llm_provider: string;
}

export interface JobAnalysisResponse {
  job_title: string;
  profile: JobProfile;
  metadata: JobAnalysisMetadata;
}

// --- Document Parsing ---
export interface DocumentParseResponse {
  filename: string;
  file_type: string;
  page_count: number;
  character_count: number;
  word_count: number;
  text: string;
}

export interface ResumeExtractionResponse {
  filename: string;
  file_type: string;
  profile: CandidateProfile;
  extraction_metadata: Record<string, unknown>;
}

// --- Deterministic & Semantic Matching ---
export interface RequirementReference {
  name: string;
  type: RequirementType;
  priority: RequirementPriority;
  minimum_years?: number | null;
  category?: string | null;
  context?: string | null;
}

export interface SemanticMatchResult {
  requirement_name: string;
  requirement_category?: string | null;
  priority: RequirementPriority;
  candidate_evidence_text?: string | null;
  similarity_score: number;
  status: SemanticStatus;
  interpretation?: string | null;
}

export interface SingleRequirementMatch {
  requirement: RequirementReference;
  status: MatchStatus;
  match_method: MatchMethod;
  candidate_evidence: string[];
  requirement_evidence: string[];
  reason?: string | null;
  semantic_result?: SemanticMatchResult | null;
}

export interface MatchingSummary {
  total_requirements: number;
  matched: number;
  partial: number;
  unmatched: number;
  not_evaluable: number;
  must_have_total: number;
  must_have_matched: number;
  nice_to_have_total: number;
  nice_to_have_matched: number;
}

// --- Scoring ---
export interface ScoreComponent {
  score?: number | null;
  weight: number;
  weighted_score?: number | null;
  available: boolean;
  status: string;
  reason?: string | null;
}

export interface RequirementScoreContribution {
  requirement_id: string;
  name: string;
  type: string;
  priority: RequirementPriority;
  status: MatchStatus;
  status_value?: number | null;
  priority_weight: number;
  weighted_value?: number | null;
  evaluable: boolean;
  semantic_similarity?: number | null;
  experience_ratio?: number | null;
  reason?: string | null;
}

export interface HybridScoreBreakdown {
  rule_fit: ScoreComponent;
  semantic_fit: ScoreComponent;
  experience_fit: ScoreComponent;
  llm_fit: ScoreComponent;
}

export interface CandidateJobScoreResponse {
  candidate_id?: string | null;
  candidate_name?: string | null;
  job_id?: string | null;
  job_title?: string | null;
  candidate_fit_score: number; // 0.0 - 1.0
  percentage_score: number;    // 0.0 - 100.0
  rule_fit_score?: number | null;
  semantic_fit_score?: number | null;
  experience_fit_score?: number | null;
  llm_fit_score?: number | null;
  components: HybridScoreBreakdown;
  requirement_contributions: RequirementScoreContribution[];
  all_must_haves_satisfied: boolean;
  evaluated_requirements: number;
  not_evaluable_requirements: number;
  weights_renormalized: boolean;
  explanation: string;
}

export interface ScoringWeights {
  rule_fit: number;
  semantic_fit: number;
  experience_fit: number;
  llm_fit: number;
}

// --- Skill Gaps ---
export interface SkillGapItem {
  requirement_id: string;
  skill_name: string;
  canonical_skill_name?: string | null;
  category?: string | null;
  priority: RequirementPriority;
  status: SkillGapStatus;
  required_value?: string | null;
  candidate_value?: string | null;
  shortfall?: string | null;
  candidate_evidence: string[];
  job_evidence: string[];
  explanation: string;
  deterministic_match_status?: MatchStatus | null;
  match_method?: MatchMethod | null;
  semantic_similarity?: number | null;
  semantic_status?: SemanticStatus | null;
  semantic_evidence?: string | null;
}

export interface ExperienceGapItem {
  requirement_id: string;
  requirement_text: string;
  priority: RequirementPriority;
  status: SkillGapStatus;
  required_years?: number | null;
  candidate_years?: number | null;
  shortfall_years?: number | null;
  candidate_evidence: string[];
  job_evidence: string[];
  explanation: string;
}

export interface SkillGapSummary {
  total_skill_requirements: number;
  satisfied_count: number;
  missing_count: number;
  insufficient_count: number;
  not_evaluable_count: number;
  must_have_gaps: number;
  nice_to_have_gaps: number;
  must_have_satisfied: number;
  nice_to_have_satisfied: number;
  total_experience_requirements: number;
  experience_gaps_count: number;
}

export interface CandidateJobSkillGapResponse {
  candidate_id?: string | null;
  candidate_name?: string | null;
  job_id?: string | null;
  job_title?: string | null;
  skill_gaps: SkillGapItem[];
  experience_gaps: ExperienceGapItem[];
  summary: SkillGapSummary;
  explanation: string;
}

// --- LLM Explanations ---
export interface RequirementExplanationItem {
  requirement_id: string;
  requirement_name: string;
  category?: string | null;
  priority: RequirementPriority;
  status: string;
  explanation: string;
  evidence_used: string[];
}

export interface SkillGapRecommendationItem {
  skill: string;
  gap_status: SkillGapStatus;
  priority: RequirementPriority;
  reason: string;
  recommendation: string;
  evidence_to_build: string[] | string;
}

export interface LLMExplanationResponse {
  candidate_id?: string | null;
  candidate_name?: string | null;
  job_id?: string | null;
  job_title?: string | null;
  summary: string;
  strengths: string[];
  key_gaps: string[];
  requirement_explanations: RequirementExplanationItem[];
  experience_explanation?: string | null;
  score_explanation?: string | null;
  recommendations: SkillGapRecommendationItem[];
  disclaimer: string;
}

// --- Unified Match Responses ---
export interface CandidateJobMatchResponse {
  candidate_id?: string | null;
  job_id?: string | null;
  job_title?: string | null;
  matches: SingleRequirementMatch[];
  summary: MatchingSummary;
  semantic_matches?: SemanticMatchResult[] | null;
  gaps?: CandidateJobSkillGapResponse | null;
  explanation?: LLMExplanationResponse | null;
}

export interface CandidateJobMatchWithScoreResponse extends CandidateJobMatchResponse {
  score?: CandidateJobScoreResponse | null;
}

// --- Request Payloads ---
export interface MatchingAnalyzeRequest {
  candidate: CandidateProfile;
  job: JobProfile;
  candidate_id?: string | null;
  job_id?: string | null;
  include_semantic?: boolean;
  include_score?: boolean;
  include_skill_gaps?: boolean;
  include_explanation?: boolean;
  scoring_weights?: ScoringWeights | null;
  llm_fit_score?: number | null;
}
