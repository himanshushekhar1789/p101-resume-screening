import React from 'react';
import { Quote, Layers, Cpu, AlertCircle, Info } from 'lucide-react';
import { SkillGapItem } from '@/types/api';
import { Badge } from '@/components/ui/Badge';

interface SkillGapCardProps {
  gap: SkillGapItem;
}

export function SkillGapCard({ gap }: SkillGapCardProps) {
  const isProblematic = gap.status === 'missing' || gap.status === 'insufficient';

  return (
    <div
      className="p-4 rounded-xl border border-slate-200/90 bg-white shadow-xs space-y-3"
      data-testid={`skill-gap-card-${gap.skill_name}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="font-bold text-sm text-slate-900">{gap.skill_name}</span>
          {gap.canonical_skill_name && gap.canonical_skill_name !== gap.skill_name && (
            <span className="text-[11px] text-slate-500 font-mono">
              (canonical: {gap.canonical_skill_name})
            </span>
          )}
          {gap.category && (
            <span className="text-xs text-slate-500">[{gap.category}]</span>
          )}
          <Badge variant={gap.priority}>
            {gap.priority === 'must_have' ? 'Must-have' : 'Nice-to-have'}
          </Badge>
        </div>

        <Badge variant={gap.status} label={gap.status} />
      </div>

      {/* Numerical/Tenure Values if applicable */}
      {(gap.required_value || gap.candidate_value || gap.shortfall) && (
        <div className="grid grid-cols-3 gap-2 p-2.5 rounded-lg bg-slate-50 border border-slate-200/80 text-xs">
          <div>
            <span className="text-slate-500 block">Required</span>
            <span className="font-semibold text-slate-800">
              {gap.required_value || 'Present'}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block">Candidate</span>
            <span className="font-semibold text-slate-800">
              {gap.candidate_value || 'None documented'}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block">Shortfall</span>
            <span className={`font-semibold ${isProblematic ? 'text-rose-600' : 'text-emerald-600'}`}>
              {gap.shortfall || 'None'}
            </span>
          </div>
        </div>
      )}

      {/* Deterministic Explanation */}
      <p className="text-xs text-slate-700 leading-relaxed">
        <span className="font-semibold text-slate-900">Audit Explanation:</span>{' '}
        {gap.explanation}
      </p>

      {/* Evidence Citations */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
        {/* Candidate Evidence */}
        <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
          <span className="font-semibold text-slate-800 flex items-center gap-1 text-[11px]">
            <Quote className="w-3.5 h-3.5 text-indigo-500" />
            Resume Citation:
          </span>
          {gap.candidate_evidence && gap.candidate_evidence.length > 0 ? (
            <ul className="space-y-1">
              {gap.candidate_evidence.map((ev, i) => (
                <li key={i} className="text-slate-600 italic">
                  &ldquo;{ev}&rdquo;
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-slate-400 italic">No direct resume evidence found.</p>
          )}
        </div>

        {/* Job Evidence */}
        <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
          <span className="font-semibold text-slate-800 flex items-center gap-1 text-[11px]">
            <Layers className="w-3.5 h-3.5 text-purple-500" />
            Target Requirement Citation:
          </span>
          {gap.job_evidence && gap.job_evidence.length > 0 ? (
            <ul className="space-y-1">
              {gap.job_evidence.map((jev, i) => (
                <li key={i} className="text-slate-600 italic">
                  &ldquo;{jev}&rdquo;
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-slate-400 italic">Extracted from job specification.</p>
          )}
        </div>
      </div>

      {/* Supporting Semantic Evidence (Phase 7) */}
      {(gap.semantic_evidence || gap.semantic_similarity !== undefined) && (
        <div className="p-3 rounded-lg bg-sky-50/60 border border-sky-200/80 text-xs space-y-1.5">
          <div className="flex items-center justify-between text-sky-900 font-semibold text-[11px]">
            <div className="flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-sky-700" />
              <span>Supporting Semantic Similarity Context</span>
            </div>
            {gap.semantic_similarity !== null && gap.semantic_similarity !== undefined && (
              <span className="font-mono text-sky-800">
                Score: {(gap.semantic_similarity * 100).toFixed(0)}%
              </span>
            )}
          </div>

          {gap.semantic_evidence && (
            <p className="text-sky-800 italic">
              Related candidate context: &ldquo;{gap.semantic_evidence}&rdquo;
            </p>
          )}

          {isProblematic && (
            <div className="flex items-start gap-1 text-[11px] text-amber-800 font-medium pt-1">
              <AlertCircle className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
              <span>
                Important: Related semantic evidence does not establish direct {gap.skill_name} proficiency.
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
