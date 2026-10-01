import React from 'react';
import { Info } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';

interface ScoreExplanationPanelProps {
  explanation?: string;
  className?: string;
}

export function ScoreExplanationPanel({
  explanation,
  className = '',
}: ScoreExplanationPanelProps) {
  return (
    <Card className={className} data-testid="score-explanation-panel">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-indigo-600" />
          <CardTitle>How This Score Was Calculated</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 text-xs text-slate-700 leading-relaxed">
        {explanation && (
          <div className="p-3.5 rounded-lg bg-indigo-50/50 border border-indigo-100 font-medium text-indigo-950">
            {explanation}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
          <div className="space-y-1">
            <h4 className="font-semibold text-slate-900">Rule Fit</h4>
            <p className="text-slate-500">
              Measures authoritative deterministic requirement coverage across skills, certifications, and education without hallucination.
            </p>
          </div>
          <div className="space-y-1">
            <h4 className="font-semibold text-slate-900">Semantic Fit</h4>
            <p className="text-slate-500">
              Measures conceptual and contextual similarity between resume project descriptions and required job technologies via embeddings.
            </p>
          </div>
          <div className="space-y-1">
            <h4 className="font-semibold text-slate-900">Experience Fit</h4>
            <p className="text-slate-500">
              Evaluates verified tenure against the job&apos;s minimum career experience requirement through ratio comparison.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
