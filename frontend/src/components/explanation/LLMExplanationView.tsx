import React from 'react';
import {
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  ShieldAlert,
  ArrowRight,
  Layers,
  FileCheck,
} from 'lucide-react';
import { LLMExplanationResponse } from '@/types/api';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

interface LLMExplanationViewProps {
  explanation: LLMExplanationResponse;
  className?: string;
}

export function LLMExplanationView({
  explanation,
  className = '',
}: LLMExplanationViewProps) {
  return (
    <div className={`space-y-6 ${className}`} data-testid="llm-explanation-view">
      {/* Top Banner Visually Distinguishing AI-Generated Decision Support */}
      <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-50/80 to-purple-50/80 border border-indigo-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center shrink-0">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-indigo-950">
              AI Decision-Support Narrative &amp; Recommendations
            </h3>
            <p className="text-xs text-indigo-800">
              Generated from verified Phase 6–9 match facts • Non-authoritative advisory layer
            </p>
          </div>
        </div>

        <span className="text-[11px] font-semibold uppercase tracking-wider bg-white/80 text-indigo-900 border border-indigo-200 px-2.5 py-1 rounded-full self-start sm:self-auto">
          Decision Support
        </span>
      </div>

      {/* Mandatory Human Oversight Disclaimer (Prompt Rule: Never hidden in tooltip) */}
      <div
        className="p-4 rounded-xl bg-amber-50/90 border border-amber-300/80 text-amber-950 flex items-start gap-3 text-xs leading-relaxed"
        role="note"
        aria-label="Human Oversight Disclaimer"
        data-testid="oversight-disclaimer"
      >
        <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="font-bold text-amber-900 uppercase tracking-wider text-[11px]">
            Mandatory Recruiter Review Policy
          </span>
          <p className="text-amber-900 font-medium">
            {explanation.disclaimer ||
              'AI-generated explanation and decision-support summary. All hiring evaluations must be reviewed by authorized human recruiters.'}
          </p>
        </div>
      </div>

      {/* Executive Summary */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <FileCheck className="w-4 h-4 text-indigo-600" />
            <CardTitle>Executive Fit Summary</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-800 leading-relaxed font-normal">
            {explanation.summary}
          </p>
        </CardContent>
      </Card>

      {/* Strengths & Key Gaps (2 Column Grid) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Strengths */}
        <Card className="border-emerald-100 bg-emerald-50/20">
          <CardHeader>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <CardTitle className="text-emerald-950">Verified Strengths</CardTitle>
            </div>
            <Badge variant="satisfied">{explanation.strengths.length}</Badge>
          </CardHeader>
          <CardContent>
            {explanation.strengths.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No direct strong alignment points noted.</p>
            ) : (
              <ul className="space-y-2 text-xs text-slate-700">
                {explanation.strengths.map((str, idx) => (
                  <li key={idx} className="flex items-start gap-2 p-2 rounded-lg bg-white border border-emerald-200/60">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                    <span>{str}</span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        {/* Key Gaps */}
        <Card className="border-rose-100 bg-rose-50/20">
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600" />
              <CardTitle className="text-rose-950">Key Identified Gaps</CardTitle>
            </div>
            <Badge variant="missing">{explanation.key_gaps.length}</Badge>
          </CardHeader>
          <CardContent>
            {explanation.key_gaps.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No critical gaps identified.</p>
            ) : (
              <ul className="space-y-2 text-xs text-slate-700">
                {explanation.key_gaps.map((gap, idx) => (
                  <li key={idx} className="flex items-start gap-2 p-2 rounded-lg bg-white border border-rose-200/60">
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-500 mt-1.5 shrink-0" />
                    <span>{gap}</span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Explanations for Experience and Score */}
      {(explanation.experience_explanation || explanation.score_explanation) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {explanation.experience_explanation && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Experience Tenure Interpretation</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-slate-700 leading-relaxed">
                  {explanation.experience_explanation}
                </p>
              </CardContent>
            </Card>
          )}

          {explanation.score_explanation && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Score Composition Interpretation</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-slate-700 leading-relaxed">
                  {explanation.score_explanation}
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Personalized Skill-Gap Recommendations */}
      <Card className="border-indigo-100" data-testid="recommendations-container">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-amber-500" />
            <div>
              <CardTitle>Personalized Skill-Gap Recommendations</CardTitle>
              <CardDescription>
                Targeted actions strictly addressing identified Phase 9 gaps
              </CardDescription>
            </div>
          </div>
          <Badge variant="default">{explanation.recommendations.length} Recommendations</Badge>
        </CardHeader>

        <CardContent className="space-y-4">
          {explanation.recommendations.length === 0 ? (
            <p className="text-xs text-slate-500 italic py-4 text-center">
              Candidate satisfied all evaluable requirements; no gap remediation necessary.
            </p>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {explanation.recommendations.map((rec, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3"
                  data-testid="recommendation-item"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-slate-900">{rec.skill}</span>
                      <Badge variant={rec.priority}>{rec.priority}</Badge>
                    </div>
                    <Badge variant={rec.gap_status} label={rec.gap_status} />
                  </div>

                  {/* Why */}
                  <div className="text-xs text-slate-700">
                    <span className="font-semibold text-slate-900 block mb-0.5">Why:</span>
                    <p className="text-slate-600">{rec.reason}</p>
                  </div>

                  {/* Recommendation */}
                  <div className="text-xs text-slate-800 bg-white p-3 rounded-lg border border-slate-200">
                    <span className="font-semibold text-indigo-900 block mb-0.5 flex items-center gap-1">
                      <ArrowRight className="w-3.5 h-3.5 text-indigo-600" />
                      Actionable Recommendation:
                    </span>
                    <p className="text-slate-700 leading-relaxed">{rec.recommendation}</p>
                  </div>

                  {/* Evidence to Build */}
                  <div className="text-xs text-slate-700 bg-indigo-50/40 p-3 rounded-lg border border-indigo-100">
                    <span className="font-semibold text-slate-900 block mb-0.5">
                      Verifiable Evidence to Build:
                    </span>
                    {Array.isArray(rec.evidence_to_build) ? (
                      <ul className="list-disc list-inside space-y-1 text-slate-600">
                        {rec.evidence_to_build.map((ev, evIdx) => (
                          <li key={evIdx}>{ev}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-slate-600">{rec.evidence_to_build}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
