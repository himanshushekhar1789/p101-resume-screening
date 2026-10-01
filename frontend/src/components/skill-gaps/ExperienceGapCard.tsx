import React from 'react';
import { Clock, Quote, AlertTriangle } from 'lucide-react';
import { ExperienceGapItem } from '@/types/api';
import { Badge } from '@/components/ui/Badge';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';

interface ExperienceGapCardProps {
  experienceGaps: ExperienceGapItem[];
  className?: string;
}

export function ExperienceGapCard({
  experienceGaps,
  className = '',
}: ExperienceGapCardProps) {
  if (!experienceGaps || experienceGaps.length === 0) {
    return null;
  }

  return (
    <Card className={className} data-testid="experience-gaps-container">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Clock className="w-5 h-5 text-amber-600" />
          <CardTitle>General Career Tenure Gaps</CardTitle>
        </div>
        <span className="text-xs text-slate-500 font-medium">
          Strictly separated from technical skill requirements
        </span>
      </CardHeader>

      <CardContent className="space-y-4">
        {experienceGaps.map((gap, idx) => (
          <div
            key={idx}
            className="p-4 rounded-xl border border-slate-200 bg-slate-50/60 space-y-3"
            data-testid="experience-gap-item"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm text-slate-900">
                  {gap.requirement_text}
                </span>
                <Badge variant={gap.priority}>
                  {gap.priority === 'must_have' ? 'Must-have' : 'Nice-to-have'}
                </Badge>
              </div>
              <Badge variant={gap.status} label={gap.status} />
            </div>

            {/* Metrics Breakdown */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3 rounded-lg bg-white border border-slate-200 text-xs">
              <div>
                <span className="text-slate-500 block">Required Tenure</span>
                <span className="font-bold text-slate-900">
                  {gap.required_years !== null && gap.required_years !== undefined
                    ? `${gap.required_years} years`
                    : 'Unspecified'}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block">Candidate Verified Tenure</span>
                <span className="font-bold text-slate-900">
                  {gap.candidate_years !== null && gap.candidate_years !== undefined
                    ? `${gap.candidate_years} years`
                    : '0 years'}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block">Shortfall Deficit</span>
                <span className="font-bold text-rose-600">
                  {gap.shortfall_years !== null && gap.shortfall_years !== undefined
                    ? `${gap.shortfall_years} years`
                    : gap.status === 'satisfied'
                    ? '0 years (Satisfied)'
                    : 'Tenure gap'}
                </span>
              </div>
            </div>

            <p className="text-xs text-slate-700 leading-relaxed">
              <span className="font-semibold text-slate-900">Audit Explanation:</span>{' '}
              {gap.explanation}
            </p>

            {/* Evidence snippets */}
            {gap.candidate_evidence && gap.candidate_evidence.length > 0 && (
              <div className="p-3 bg-white rounded-lg border border-slate-200 text-xs space-y-1">
                <span className="text-slate-500 font-medium flex items-center gap-1">
                  <Quote className="w-3.5 h-3.5 text-indigo-500" />
                  Candidate Career Timeline Evidence:
                </span>
                {gap.candidate_evidence.map((ev, evIdx) => (
                  <div key={evIdx} className="text-slate-600 italic">
                    &ldquo;{ev}&rdquo;
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
