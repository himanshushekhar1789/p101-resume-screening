import React from 'react';
import { ShieldCheck, ShieldAlert } from 'lucide-react';

interface OverallScoreBadgeProps {
  score: number; // 0.0 - 1.0
  percentage?: number; // 0 - 100
  allMustHavesSatisfied?: boolean;
  className?: string;
}

export function OverallScoreBadge({
  score,
  percentage,
  allMustHavesSatisfied,
  className = '',
}: OverallScoreBadgeProps) {
  const percentValue = percentage ?? Math.round(score * 100);

  let tier = 'Limited Fit';
  let tierColor = 'text-slate-600 bg-slate-100 border-slate-200';
  let circleColor = 'text-slate-500';

  if (percentValue >= 80) {
    tier = 'High Fit';
    tierColor = 'text-emerald-700 bg-emerald-50 border-emerald-200';
    circleColor = 'text-emerald-600';
  } else if (percentValue >= 65) {
    tier = 'Moderate Fit';
    tierColor = 'text-indigo-700 bg-indigo-50 border-indigo-200';
    circleColor = 'text-indigo-600';
  } else if (percentValue >= 50) {
    tier = 'Partial Fit';
    tierColor = 'text-amber-700 bg-amber-50 border-amber-200';
    circleColor = 'text-amber-500';
  } else {
    tier = 'Limited Fit';
    tierColor = 'text-rose-700 bg-rose-50 border-rose-200';
    circleColor = 'text-rose-500';
  }

  return (
    <div
      className={`p-6 rounded-2xl bg-white border border-slate-200/90 shadow-xs flex flex-col items-center justify-center text-center ${className}`}
      data-testid="overall-score-badge"
    >
      <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
        Overall Candidate Fit
      </span>

      <div className="flex items-baseline justify-center my-1">
        <span className={`text-5xl font-extrabold tracking-tight ${circleColor}`} data-testid="score-value">
          {percentValue}
        </span>
        <span className="text-2xl font-bold text-slate-400 ml-1">%</span>
      </div>

      <div className={`mt-2 px-3 py-1 rounded-full text-xs font-semibold border ${tierColor}`}>
        {tier}
      </div>

      {allMustHavesSatisfied !== undefined && (
        <div className="mt-4 pt-3 border-t border-slate-100 w-full flex items-center justify-center gap-1.5 text-xs">
          {allMustHavesSatisfied ? (
            <span className="inline-flex items-center gap-1 text-emerald-700 font-medium">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              All Mandatory Criteria Met
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-amber-700 font-medium">
              <ShieldAlert className="w-4 h-4 text-amber-600" />
              Mandatory Shortfall Detected
            </span>
          )}
        </div>
      )}
    </div>
  );
}
