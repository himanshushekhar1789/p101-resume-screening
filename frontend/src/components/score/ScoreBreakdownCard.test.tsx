import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ScoreBreakdownCard } from './ScoreBreakdownCard';
import { HybridScoreBreakdown } from '@/types/api';

describe('ScoreBreakdownCard', () => {
  const mockComponents: HybridScoreBreakdown = {
    rule_fit: {
      score: 0.8,
      weight: 0.5,
      weighted_score: 0.4,
      available: true,
      status: 'evaluated',
    },
    semantic_fit: {
      score: 0.74,
      weight: 0.3,
      weighted_score: 0.222,
      available: true,
      status: 'evaluated',
    },
    experience_fit: {
      score: 0.6,
      weight: 0.2,
      weighted_score: 0.12,
      available: true,
      status: 'evaluated',
    },
    llm_fit: {
      score: null,
      weight: 0.0,
      weighted_score: null,
      available: false,
      status: 'unavailable',
    },
  };

  it('renders available component scores accurately without independent modification', () => {
    render(<ScoreBreakdownCard components={mockComponents} />);
    expect(screen.getByText('80%')).toBeDefined();
    expect(screen.getByText('74%')).toBeDefined();
    expect(screen.getByText('60%')).toBeDefined();
  });

  it('renders "Not available" for unavailable components rather than 0%', () => {
    render(<ScoreBreakdownCard components={mockComponents} />);
    expect(screen.getByText('Not available')).toBeDefined();
  });

  it('displays renormalization badge when weights are renormalized', () => {
    render(<ScoreBreakdownCard components={mockComponents} weightsRenormalized={true} />);
    expect(screen.getByText('Weights Renormalized')).toBeDefined();
  });
});
