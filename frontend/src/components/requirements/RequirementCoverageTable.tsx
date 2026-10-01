'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Quote, Layers, CheckCircle2, XCircle, AlertTriangle, HelpCircle } from 'lucide-react';
import { SingleRequirementMatch, MatchStatus } from '@/types/api';
import { Badge } from '@/components/ui/Badge';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';

interface RequirementCoverageTableProps {
  matches: SingleRequirementMatch[];
  className?: string;
}

export function RequirementCoverageTable({
  matches,
  className = '',
}: RequirementCoverageTableProps) {
  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});

  const toggleRow = (id: string) => {
    setExpandedRows((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const getStatusIcon = (status: MatchStatus) => {
    switch (status) {
      case 'satisfied':
        return <CheckCircle2 className="w-4 h-4 text-emerald-600 inline mr-1" />;
      case 'partially_satisfied':
        return <AlertTriangle className="w-4 h-4 text-amber-500 inline mr-1" />;
      case 'unmatched':
        return <XCircle className="w-4 h-4 text-rose-500 inline mr-1" />;
      case 'not_evaluable':
        return <HelpCircle className="w-4 h-4 text-slate-400 inline mr-1" />;
    }
  };

  return (
    <Card className={className} data-testid="requirement-coverage-table">
      <CardHeader>
        <div>
          <CardTitle>Requirement-by-Requirement Coverage</CardTitle>
          <CardDescription>
            Authoritative deterministic evaluation across all mandatory and preferred criteria
          </CardDescription>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700 divide-y divide-slate-200">
            <thead className="bg-slate-50 text-[11px] font-semibold text-slate-500 uppercase tracking-wider sticky top-0 z-10">
              <tr>
                <th scope="col" className="py-3.5 pl-6 pr-3">
                  Requirement
                </th>
                <th scope="col" className="px-3 py-3.5">
                  Type
                </th>
                <th scope="col" className="px-3 py-3.5">
                  Priority
                </th>
                <th scope="col" className="px-3 py-3.5">
                  Status
                </th>
                <th scope="col" className="px-3 py-3.5">
                  Match Method
                </th>
                <th scope="col" className="px-3 py-3.5">
                  Semantic Sim.
                </th>
                <th scope="col" className="relative py-3.5 pl-3 pr-6 text-right">
                  Evidence
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {matches.map((item, idx) => {
                const reqKey = `${item.requirement.type}_${item.requirement.name}_${idx}`;
                const isExpanded = !!expandedRows[reqKey];
                const hasEvidence =
                  (item.candidate_evidence && item.candidate_evidence.length > 0) ||
                  (item.requirement_evidence && item.requirement_evidence.length > 0) ||
                  item.reason;

                return (
                  <React.Fragment key={reqKey}>
                    <tr
                      className="hover:bg-slate-50/70 transition-colors cursor-pointer"
                      onClick={() => toggleRow(reqKey)}
                    >
                      <td className="py-3.5 pl-6 pr-3 font-semibold text-slate-900 flex items-center gap-2">
                        {getStatusIcon(item.status)}
                        <span>{item.requirement.name}</span>
                      </td>

                      <td className="px-3 py-3.5 capitalize text-slate-600">
                        {item.requirement.type}
                      </td>

                      <td className="px-3 py-3.5">
                        <Badge variant={item.requirement.priority}>
                          {item.requirement.priority === 'must_have' ? 'Must-have' : 'Nice-to-have'}
                        </Badge>
                      </td>

                      <td className="px-3 py-3.5">
                        <Badge variant={item.status} label={item.status.replace('_', ' ')} />
                      </td>

                      <td className="px-3 py-3.5 text-slate-500 font-mono text-[11px]">
                        {item.match_method}
                      </td>

                      <td className="px-3 py-3.5 text-slate-600">
                        {item.semantic_result?.similarity_score !== undefined
                          ? `${Math.round(item.semantic_result.similarity_score * 100)}%`
                          : '—'}
                      </td>

                      <td className="py-3.5 pl-3 pr-6 text-right">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleRow(reqKey);
                          }}
                          className="inline-flex items-center gap-1 text-[11px] text-indigo-600 hover:text-indigo-900 font-medium"
                          aria-label={`Toggle evidence for ${item.requirement.name}`}
                        >
                          <span>{isExpanded ? 'Hide' : 'Inspect'}</span>
                          {isExpanded ? (
                            <ChevronUp className="w-3.5 h-3.5" />
                          ) : (
                            <ChevronDown className="w-3.5 h-3.5" />
                          )}
                        </button>
                      </td>
                    </tr>

                    {/* Expandable Evidence Row */}
                    {isExpanded && (
                      <tr className="bg-slate-50/90">
                        <td colSpan={7} className="py-4 pl-8 pr-6 space-y-3">
                          {item.reason && (
                            <div className="text-xs text-slate-700 bg-white p-3 rounded-lg border border-slate-200">
                              <span className="font-semibold text-slate-900">Deterministic Match Audit:</span>{' '}
                              {item.reason}
                            </div>
                          )}

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Candidate Evidence */}
                            <div className="p-3 bg-white rounded-lg border border-slate-200 space-y-1.5">
                              <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800">
                                <Quote className="w-3.5 h-3.5 text-indigo-500" />
                                <span>Verified Candidate Evidence</span>
                              </div>
                              {item.candidate_evidence && item.candidate_evidence.length > 0 ? (
                                <ul className="space-y-1">
                                  {item.candidate_evidence.map((ev, evIdx) => (
                                    <li
                                      key={evIdx}
                                      className="text-xs text-slate-600 bg-slate-50 p-2 rounded border border-slate-100 italic"
                                    >
                                      &ldquo;{ev}&rdquo;
                                    </li>
                                  ))}
                                </ul>
                              ) : (
                                <p className="text-xs text-slate-400 italic">
                                  No direct text evidence documented in candidate resume.
                                </p>
                              )}
                            </div>

                            {/* Job Requirement Evidence */}
                            <div className="p-3 bg-white rounded-lg border border-slate-200 space-y-1.5">
                              <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800">
                                <Layers className="w-3.5 h-3.5 text-purple-500" />
                                <span>Target Job Requirement Context</span>
                              </div>
                              {item.requirement_evidence && item.requirement_evidence.length > 0 ? (
                                <ul className="space-y-1">
                                  {item.requirement_evidence.map((jev, jevIdx) => (
                                    <li
                                      key={jevIdx}
                                      className="text-xs text-slate-600 bg-slate-50 p-2 rounded border border-slate-100 italic"
                                    >
                                      &ldquo;{jev}&rdquo;
                                    </li>
                                  ))}
                                </ul>
                              ) : item.requirement.context ? (
                                <p className="text-xs text-slate-600 bg-slate-50 p-2 rounded border border-slate-100 italic">
                                  &ldquo;{item.requirement.context}&rdquo;
                                </p>
                              ) : (
                                <p className="text-xs text-slate-400 italic">
                                  Extracted from job specification.
                                </p>
                              )}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
