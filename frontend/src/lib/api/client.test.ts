import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { api, ApiError } from './client';

describe('ApiClient', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('checks backend health successfully', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'ok', app: 'P_101 Backend', version: '1.0.0' }),
    } as Response);

    const res = await api.checkHealth();
    expect(res.status).toBe('ok');
    expect(res.app).toBe('P_101 Backend');
  });

  it('handles backend error with status and detail message', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({ detail: 'Scanned document cannot be parsed.' }),
    } as Response);

    await expect(api.checkHealth()).rejects.toThrow('Scanned document cannot be parsed.');
  });

  it('constructs correct payload for analyzeJobText', async () => {
    const mockResponse = {
      job_title: 'Senior Backend Engineer',
      profile: {
        job_title: 'Senior Backend Engineer',
        skills: [],
        experience: [],
        education: [],
        certifications: [],
        responsibilities: [],
      },
      metadata: {
        character_count: 100,
        word_count: 20,
        source_type: 'text',
        llm_provider: 'mock',
      },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    } as Response);

    const res = await api.analyzeJobText('We need Python and Docker.', 'Senior Engineer');
    expect(res.job_title).toBe('Senior Backend Engineer');
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/jobs/analyze'),
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({
          job_description: 'We need Python and Docker.',
          job_title: 'Senior Engineer',
        }),
      })
    );
  });
});
