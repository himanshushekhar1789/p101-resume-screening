/**
 * P_101 Resume Screening System — Centralized API Client
 */

import {
  JobAnalysisResponse,
  DocumentParseResponse,
  ResumeExtractionResponse,
  MatchingAnalyzeRequest,
  CandidateJobMatchWithScoreResponse,
  LLMExplanationResponse,
} from '@/types/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    let data: unknown = null;
    try {
      data = await response.json();
      if (data && typeof data === 'object' && 'detail' in data) {
        errorDetail = String((data as { detail: unknown }).detail);
      }
    } catch {
      // response is not json
    }
    throw new ApiError(errorDetail, response.status, data);
  }
  return response.json() as Promise<T>;
}

export const api = {
  baseUrl: API_BASE_URL,

  async checkHealth(): Promise<{ status: string; app: string; version: string }> {
    const res = await fetch(`${API_BASE_URL}/api/v1/health`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    return handleResponse(res);
  },

  async analyzeJobText(job_description: string, job_title?: string): Promise<JobAnalysisResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/jobs/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        job_description,
        job_title: job_title || undefined,
      }),
    });
    return handleResponse<JobAnalysisResponse>(res);
  },

  async analyzeJobFile(file: File, job_title?: string): Promise<JobAnalysisResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (job_title) {
      formData.append('job_title', job_title);
    }

    const res = await fetch(`${API_BASE_URL}/api/v1/jobs/analyze/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<JobAnalysisResponse>(res);
  },

  async parseResume(file: File): Promise<DocumentParseResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE_URL}/api/v1/resumes/parse`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<DocumentParseResponse>(res);
  },

  async extractResume(file: File): Promise<ResumeExtractionResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE_URL}/api/v1/resumes/extract`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<ResumeExtractionResponse>(res);
  },

  async matchAndAnalyze(payload: MatchingAnalyzeRequest): Promise<CandidateJobMatchWithScoreResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/matching/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        ...payload,
        include_semantic: payload.include_semantic ?? true,
        include_score: payload.include_score ?? true,
        include_skill_gaps: payload.include_skill_gaps ?? true,
        include_explanation: payload.include_explanation ?? true,
      }),
    });
    return handleResponse<CandidateJobMatchWithScoreResponse>(res);
  },

  async matchFromFiles(options: {
    resumeFile: File;
    jobFile: File;
    includeSemantic?: boolean;
    includeScore?: boolean;
    includeSkillGaps?: boolean;
    includeExplanation?: boolean;
  }): Promise<CandidateJobMatchWithScoreResponse> {
    const formData = new FormData();
    formData.append('resume_file', options.resumeFile);
    formData.append('job_file', options.jobFile);

    const params = new URLSearchParams({
      include_semantic: String(options.includeSemantic ?? true),
      include_score: String(options.includeScore ?? true),
      include_skill_gaps: String(options.includeSkillGaps ?? true),
      include_explanation: String(options.includeExplanation ?? true),
    });

    const res = await fetch(`${API_BASE_URL}/api/v1/matching/from-files?${params.toString()}`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<CandidateJobMatchWithScoreResponse>(res);
  },

  async explanationFromFiles(
    resumeFile: File,
    jobFile: File,
    includeSemantic = true
  ): Promise<LLMExplanationResponse> {
    const formData = new FormData();
    formData.append('resume_file', resumeFile);
    formData.append('job_file', jobFile);

    const params = new URLSearchParams({
      include_semantic: String(includeSemantic),
    });

    const res = await fetch(`${API_BASE_URL}/api/v1/explanations/from-files?${params.toString()}`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<LLMExplanationResponse>(res);
  },
};
