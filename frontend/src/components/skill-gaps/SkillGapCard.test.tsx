import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SkillGapCard } from './SkillGapCard';
import { SkillGapItem } from '@/types/api';

describe('SkillGapCard', () => {
  const mockGap: SkillGapItem = {
    requirement_id: 'skill_Kubernetes',
    skill_name: 'Kubernetes',
    canonical_skill_name: 'Kubernetes',
    category: 'devops',
    priority: 'must_have',
    status: 'missing',
    required_value: '2.0 years',
    candidate_value: 'None documented',
    shortfall: '2.0 years',
    candidate_evidence: [],
    job_evidence: ['Must have 2+ years of production Kubernetes experience'],
    explanation: 'Candidate resume does not document container orchestration with Kubernetes.',
    semantic_similarity: 0.68,
    semantic_evidence: 'Built and managed Docker containers for microservices architecture.',
  };

  it('renders skill name and priority', () => {
    render(<SkillGapCard gap={mockGap} />);
    expect(screen.getByText('Kubernetes')).toBeDefined();
    expect(screen.getByText('Must-have')).toBeDefined();
    expect(screen.getByText('missing')).toBeDefined();
  });

  it('renders shortfall values accurately', () => {
    render(<SkillGapCard gap={mockGap} />);
    expect(screen.getAllByText('2.0 years').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('None documented')).toBeDefined();
  });

  it('displays semantic supporting evidence with non-proficiency disclaimer', () => {
    render(<SkillGapCard gap={mockGap} />);
    expect(screen.getByText(/Related candidate context/)).toBeDefined();
    expect(screen.getByText(/Related semantic evidence does not establish direct Kubernetes proficiency/)).toBeDefined();
  });
});
