import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { OverallScoreBadge } from './OverallScoreBadge';

describe('OverallScoreBadge', () => {
  it('renders score percentage correctly', () => {
    render(<OverallScoreBadge score={0.72} percentage={72} />);
    expect(screen.getByTestId('score-value').textContent).toBe('72');
    expect(screen.getByText('Moderate Fit')).toBeDefined();
  });

  it('renders high fit tier for score >= 80%', () => {
    render(<OverallScoreBadge score={0.88} percentage={88} allMustHavesSatisfied={true} />);
    expect(screen.getByText('High Fit')).toBeDefined();
    expect(screen.getByText('All Mandatory Criteria Met')).toBeDefined();
  });

  it('displays warning when mandatory requirements are unsatisfied', () => {
    render(<OverallScoreBadge score={0.65} percentage={65} allMustHavesSatisfied={false} />);
    expect(screen.getByText('Mandatory Shortfall Detected')).toBeDefined();
  });
});
