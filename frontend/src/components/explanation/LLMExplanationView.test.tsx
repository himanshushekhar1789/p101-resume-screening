import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LLMExplanationView } from './LLMExplanationView';
import { LLMExplanationResponse } from '@/types/api';

describe('LLMExplanationView', () => {
  const mockExplanation: LLMExplanationResponse = {
    candidate_id: 'cand_sarah_01',
    job_id: 'job_backend_01',
    summary: 'Candidate demonstrates strong Python foundation but has gap in Kubernetes.',
    strengths: ['Strong 4 years of Python experience', 'REST API design with FastAPI'],
    key_gaps: ['Missing mandatory Kubernetes experience'],
    requirement_explanations: [],
    experience_explanation: 'Meets 4.0 years vs 3.0 years required.',
    score_explanation: 'Candidate fit score is 72% based on balanced rule and semantic fit.',
    recommendations: [
      {
        skill: 'Kubernetes',
        gap_status: 'missing',
        priority: 'must_have',
        reason: 'Job requires container orchestration which is absent from resume.',
        recommendation: 'Deploy microservices on minikube or managed EKS/GKE cluster.',
        evidence_to_build: ['GitHub repository with Helm charts and deployment manifests'],
      },
    ],
    disclaimer: 'AI-generated explanation and decision-support summary. All hiring evaluations must be reviewed by authorized human recruiters.',
  };

  it('renders executive summary, strengths, and key gaps', () => {
    render(<LLMExplanationView explanation={mockExplanation} />);
    expect(screen.getByText(/Candidate demonstrates strong Python foundation/)).toBeDefined();
    expect(screen.getByText('Strong 4 years of Python experience')).toBeDefined();
    expect(screen.getByText('Missing mandatory Kubernetes experience')).toBeDefined();
  });

  it('renders mandatory human oversight disclaimer prominently', () => {
    render(<LLMExplanationView explanation={mockExplanation} />);
    const disclaimer = screen.getByTestId('oversight-disclaimer');
    expect(disclaimer.textContent).toContain('All hiring evaluations must be reviewed by authorized human recruiters');
  });

  it('renders actionable recommendations grounded in Phase 9 gaps', () => {
    render(<LLMExplanationView explanation={mockExplanation} />);
    expect(screen.getByText('Deploy microservices on minikube or managed EKS/GKE cluster.')).toBeDefined();
    expect(screen.getByText('GitHub repository with Helm charts and deployment manifests')).toBeDefined();
  });
});
