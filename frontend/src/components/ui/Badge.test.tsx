import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Badge } from './Badge';

describe('Badge', () => {
  it('renders satisfied badge with appropriate role and label', () => {
    render(<Badge variant="satisfied" label="Satisfied" />);
    const badge = screen.getByRole('status');
    expect(badge.textContent).toContain('Satisfied');
  });

  it('renders missing badge with appropriate label', () => {
    render(<Badge variant="missing" label="Missing" />);
    const badge = screen.getByRole('status');
    expect(badge.textContent).toContain('Missing');
  });

  it('renders insufficient badge with appropriate label', () => {
    render(<Badge variant="insufficient" label="Insufficient" />);
    const badge = screen.getByRole('status');
    expect(badge.textContent).toContain('Insufficient');
  });

  it('renders not_evaluable badge with appropriate label', () => {
    render(<Badge variant="not_evaluable" label="Not Evaluable" />);
    const badge = screen.getByRole('status');
    expect(badge.textContent).toContain('Not Evaluable');
  });
});
