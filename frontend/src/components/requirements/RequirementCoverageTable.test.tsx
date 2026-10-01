import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { RequirementCoverageTable } from './RequirementCoverageTable';
import { SingleRequirementMatch } from '@/types/api';

describe('RequirementCoverageTable', () => {
  const mockMatches: SingleRequirementMatch[] = [
    {
      requirement: {
        name: 'Python',
        type: 'skill',
        priority: 'must_have',
      },
      status: 'satisfied',
      match_method: 'canonical_exact',
      candidate_evidence: ['Developed microservices in Python 3.10 and FastAPI.'],
      requirement_evidence: ['Strong Python proficiency required.'],
      reason: 'Verified canonical exact match in work history.',
      semantic_result: {
        requirement_name: 'Python',
        priority: 'must_have',
        similarity_score: 0.95,
        status: 'high_similarity',
      },
    },
    {
      requirement: {
        name: 'Kubernetes',
        type: 'skill',
        priority: 'must_have',
      },
      status: 'unmatched',
      match_method: 'unmatched',
      candidate_evidence: [],
      requirement_evidence: ['Production Kubernetes deployment experience required.'],
      reason: 'No evidence found in candidate profile.',
    },
  ];

  it('renders requirements with status and priority badges', () => {
    render(<RequirementCoverageTable matches={mockMatches} />);
    expect(screen.getByText('Python')).toBeDefined();
    expect(screen.getByText('Kubernetes')).toBeDefined();
    expect(screen.getByText('canonical_exact')).toBeDefined();
  });

  it('expands evidence panel upon clicking Inspect button', () => {
    render(<RequirementCoverageTable matches={mockMatches} />);
    const inspectButtons = screen.getAllByText('Inspect');
    expect(inspectButtons.length).toBeGreaterThan(0);

    fireEvent.click(inspectButtons[0]);
    expect(screen.getByText(/Developed microservices in Python 3.10 and FastAPI/)).toBeDefined();
    expect(screen.getByText(/Strong Python proficiency required/)).toBeDefined();
  });
});
