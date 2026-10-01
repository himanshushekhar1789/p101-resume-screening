import React from 'react';
import { HybridScoreBreakdown } from '@/types/api';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';

interface ScoreBreakdownCardProps {
  components: HybridScoreBreakdown;
  weightsRenormalized?: boolean;
  className?: string;
}

export function ScoreBreakdownCard({
  components,
  weightsRenormalized,
  className = '',
}: ScoreBreakdownCardProps) {
  const items = [
    {
      key: 'rule_fit',
      label: 'Rule Fit',
      description: 'Deterministic requirement coverage (Skills, Certs, Education)',
      component: components.rule_fit,
    },
    {
      key: 'semantic_fit',
      label: 'Semantic Fit',
      description: 'SentenceTransformer cosine similarity on resume evidence',
      component: components.semantic_fit,
    },
    {
      key: 'experience_fit',
      label: 'Experience Fit',
      description: 'Verified career tenure ratio against required years',
      component: components.experience_fit,
    },
    {
      key: 'llm_fit',
      label: 'LLM Fit',
      description: 'External LLM evaluator fit (advisory only)',
      component: components.llm_fit,
      showOnlyIfAvailable: true,
    },
  ];

  return (
    <Card className={className} data-testid="score-breakdown-card">
      <CardHeader>
        <div>
          <CardTitle>Score Component Breakdown</CardTitle>
          <CardDescription>
            Multi-layer hybrid scoring combining rule, semantic, and tenure metrics
          </CardDescription>
        </div>
        {weightsRenormalized && (
          <span className="text-[11px] font-medium bg-amber-50 text-amber-800 border border-amber-200 px-2.5 py-0.5 rounded-full">
            Weights Renormalized
          </span>
        )}
      </CardHeader>

      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {items.map((item) => {
            const comp = item.component;
            if (!comp) return null;

            // If it's LLM fit and not available, we can display "Not available" or omit if instructed
            const isAvailable = comp.available && comp.score !== null && comp.score !== undefined;
            const percentage = isAvailable ? Math.round((comp.score as number) * 100) : null;

            return (
              <div
                key={item.key}
                className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between"
                data-testid={`score-component-${item.key}`}
              >
                <div>
                  <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
                    <span>{item.label}</span>
                    <span className="text-slate-400 font-normal">
                      Weight: {Math.round(comp.weight * 100)}%
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1 leading-snug">
                    {item.description}
                  </p>
                </div>

                <div className="mt-4 pt-2 border-t border-slate-200/60 flex items-baseline justify-between">
                  <span className="text-xs text-slate-500">Component Score</span>
                  {isAvailable ? (
                    <span className="text-xl font-bold text-slate-900">
                      {percentage}%
                    </span>
                  ) : (
                    <span className="text-xs font-medium text-slate-400 italic">
                      Not available
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
