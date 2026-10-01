'use client';

import React, { useState } from 'react';
import { CandidateJobSkillGapResponse, SkillGapStatus } from '@/types/api';
import { SkillGapCard } from './SkillGapCard';
import { ExperienceGapCard } from './ExperienceGapCard';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

interface SkillGapSectionProps {
  gaps: CandidateJobSkillGapResponse;
  className?: string;
}

export function SkillGapSection({ gaps, className = '' }: SkillGapSectionProps) {
  const [filter, setFilter] = useState<'all' | SkillGapStatus>('all');

  const filteredSkills =
    filter === 'all'
      ? gaps.skill_gaps
      : gaps.skill_gaps.filter((s) => s.status === filter);

  return (
    <div className={`space-y-6 ${className}`} data-testid="skill-gap-section">
      <Card>
        <CardHeader>
          <div>
            <CardTitle>Skill-Gap Analysis &amp; Evidence Grounding</CardTitle>
            <CardDescription>
              Clear distinction between satisfied, missing, insufficient, and unverified skills
            </CardDescription>
          </div>

          {/* Filter Tabs */}
          <div className="flex flex-wrap items-center gap-1.5 bg-slate-100 p-1 rounded-lg text-xs">
            <button
              type="button"
              onClick={() => setFilter('all')}
              className={`px-3 py-1 rounded-md font-medium transition-colors ${
                filter === 'all' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              All ({gaps.skill_gaps.length})
            </button>
            <button
              type="button"
              onClick={() => setFilter('missing')}
              className={`px-3 py-1 rounded-md font-medium transition-colors ${
                filter === 'missing' ? 'bg-white text-rose-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Missing ({gaps.summary.missing_count})
            </button>
            <button
              type="button"
              onClick={() => setFilter('insufficient')}
              className={`px-3 py-1 rounded-md font-medium transition-colors ${
                filter === 'insufficient' ? 'bg-white text-amber-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Insufficient ({gaps.summary.insufficient_count})
            </button>
            <button
              type="button"
              onClick={() => setFilter('satisfied')}
              className={`px-3 py-1 rounded-md font-medium transition-colors ${
                filter === 'satisfied' ? 'bg-white text-emerald-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Satisfied ({gaps.summary.satisfied_count})
            </button>
            <button
              type="button"
              onClick={() => setFilter('not_evaluable')}
              className={`px-3 py-1 rounded-md font-medium transition-colors ${
                filter === 'not_evaluable' ? 'bg-white text-slate-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Not Evaluable ({gaps.summary.not_evaluable_count})
            </button>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {gaps.explanation && (
            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 leading-relaxed">
              <span className="font-semibold text-slate-900">Gap Summary Audit:</span> {gaps.explanation}
            </div>
          )}

          {filteredSkills.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-400 italic">
              No skills match the selected filter ({filter}).
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {filteredSkills.map((gap, idx) => (
                <SkillGapCard key={`${gap.requirement_id}_${idx}`} gap={gap} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* General Career Experience Gaps (Separately Sectioned) */}
      <ExperienceGapCard experienceGaps={gaps.experience_gaps} />
    </div>
  );
}
