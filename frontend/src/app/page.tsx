'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  FileSearch,
  PlusCircle,
  Briefcase,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  Cpu,
  ArrowRight,
} from 'lucide-react';
import { api } from '@/lib/api/client';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';

interface HealthStatus {
  online: boolean;
  app?: string;
  version?: string;
  error?: string;
}

export default function DashboardPage() {
  const [health, setHealth] = useState<HealthStatus>({ online: false });
  const [loadingHealth, setLoadingHealth] = useState(true);
  const [recentAnalyses, setRecentAnalyses] = useState<Array<{ id: string; candidate: string; job: string; score: number; date: string }>>([]);

  useEffect(() => {
    async function fetchHealth() {
      try {
        const res = await api.checkHealth();
        setHealth({ online: res.status === 'ok', app: res.app, version: res.version });
      } catch (err: unknown) {
        setHealth({
          online: false,
          error: err instanceof Error ? err.message : 'Backend connection unavailable',
        });
      } finally {
        setLoadingHealth(false);
      }
    }

    fetchHealth();

    // Load recent analyses from local session storage if available
    try {
      const stored = localStorage.getItem('p101_recent_analyses');
      if (stored) {
        setRecentAnalyses(JSON.parse(stored));
      }
    } catch {
      // ignore storage error
    }
  }, []);

  return (
    <div className="space-y-8">
      {/* Top Banner / Hero */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            Recruiter Screening Dashboard
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Deterministic matching, semantic similarity, and grounded LLM explanations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/jobs/new">
            <Button variant="outline" size="md" leftIcon={<PlusCircle className="w-4 h-4" />}>
              Configure Job
            </Button>
          </Link>
          <Link href="/analysis">
            <Button variant="primary" size="md" leftIcon={<FileSearch className="w-4 h-4" />}>
              Start Screening
            </Button>
          </Link>
        </div>
      </div>

      {/* Backend System Telemetry Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-white border border-slate-200 shadow-xs">
        <div className="flex items-center gap-3">
          <div
            className={`w-3 h-3 rounded-full ${
              loadingHealth
                ? 'bg-amber-400 animate-pulse'
                : health.online
                ? 'bg-emerald-500'
                : 'bg-rose-500'
            }`}
          />
          <div>
            <div className="text-xs font-semibold text-slate-900">
              Backend Service Status:{' '}
              {loadingHealth
                ? 'Checking connection...'
                : health.online
                ? 'Operational'
                : 'Offline / Disconnected'}
            </div>
            <div className="text-[11px] text-slate-500">
              {health.online
                ? `${health.app || 'P_101 Backend'} v${health.version || '1.0.0'} (${api.baseUrl})`
                : health.error || 'Ensure FastAPI backend is running on http://localhost:8000'}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs text-slate-600">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Deterministic Grounding Active</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Cpu className="w-4 h-4 text-indigo-600" />
            <span>Local Embeddings Active</span>
          </div>
        </div>
      </div>

      {/* Quick Summary Cards (Derived from real activity or clean empty states) */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <Card>
          <CardContent className="p-5 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
              <Briefcase className="w-6 h-6" />
            </div>
            <div>
              <div className="text-xs font-medium uppercase tracking-wider text-slate-500">
                Jobs Configured
              </div>
              <div className="text-2xl font-bold text-slate-900 mt-0.5">
                {/* Real metric: derived from session storage or state */}
                {typeof window !== 'undefined' && localStorage.getItem('p101_active_job') ? '1 Active' : '0'}
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">
                Available in current session
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
              <FileSearch className="w-6 h-6" />
            </div>
            <div>
              <div className="text-xs font-medium uppercase tracking-wider text-slate-500">
                Screenings Completed
              </div>
              <div className="text-2xl font-bold text-slate-900 mt-0.5">
                {recentAnalyses.length}
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">
                Session match reports
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-700">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <div className="text-xs font-medium uppercase tracking-wider text-slate-500">
                Decision Support
              </div>
              <div className="text-2xl font-bold text-slate-900 mt-0.5">
                Audited
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">
                Zero automated hiring cuts
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Recent Screenings or Empty State */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Recent Screening Analyses</CardTitle>
                <CardDescription>
                  Evaluations conducted in this session with full audit trails
                </CardDescription>
              </div>
              {recentAnalyses.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    localStorage.removeItem('p101_recent_analyses');
                    setRecentAnalyses([]);
                  }}
                >
                  Clear History
                </Button>
              )}
            </CardHeader>
            <CardContent>
              {recentAnalyses.length === 0 ? (
                <div className="py-12 px-4 text-center space-y-3">
                  <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-400 mx-auto flex items-center justify-center">
                    <FileSearch className="w-6 h-6" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900">No screenings completed yet</h4>
                    <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
                      Upload a job description and candidate resume in the Analysis Workspace to generate an evidence-grounded screening report.
                    </p>
                  </div>
                  <div className="pt-2">
                    <Link href="/analysis">
                      <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
                        Launch Analysis Workspace
                      </Button>
                    </Link>
                  </div>
                </div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {recentAnalyses.map((item) => (
                    <div
                      key={item.id}
                      className="py-3.5 flex items-center justify-between gap-4 hover:bg-slate-50/50 px-2 rounded-lg transition-colors"
                    >
                      <div className="min-w-0">
                        <div className="text-sm font-semibold text-slate-900 truncate">
                          {item.candidate}
                        </div>
                        <div className="text-xs text-slate-500 flex items-center gap-2 mt-0.5">
                          <span>{item.job}</span>
                          <span>•</span>
                          <span>{item.date}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 shrink-0">
                        <div className="text-right">
                          <span className="text-sm font-bold text-slate-900">
                            {Math.round(item.score * 100)}%
                          </span>
                          <span className="text-[10px] text-slate-500 block">Fit Score</span>
                        </div>
                        <Link href={`/analysis?id=${item.id}`}>
                          <Button variant="outline" size="sm">
                            View Audit
                          </Button>
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Screening Methodology Architecture Note */}
          <Card className="bg-slate-900 text-white border-slate-800">
            <CardContent className="p-6 space-y-4">
              <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs tracking-wider uppercase">
                <Cpu className="w-4 h-4" />
                <span>Deterministic-First Hybrid Architecture</span>
              </div>
              <h3 className="text-lg font-bold text-white">
                How ResumeScreen AI Evaluates Candidates
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Unlike opaque black-box AI screeners, our system strictly separates deterministic facts from AI explanations.
                Phase 6 performs requirement-by-requirement canonical validation. Phase 7 measures semantic similarity for supporting evidence.
                Phase 8 combines these into a transparent multi-layer score. Phase 9 maps missing vs insufficient skill gaps, and Phase 10 provides human-readable explanations grounded directly in resume citations.
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-center text-xs">
                <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700">
                  <div className="font-semibold text-slate-200">Rule Fit</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Deterministic 0-1</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700">
                  <div className="font-semibold text-slate-200">Semantic Fit</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Cosine Similarity</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700">
                  <div className="font-semibold text-slate-200">Experience Fit</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Tenure Ratio</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700">
                  <div className="font-semibold text-slate-200">Skill Gaps</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Evidence Grounded</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Workflow Steps & Oversight Notice */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Screening Workflow</CardTitle>
              <CardDescription>Step-by-step decision support</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-3">
                <div className="w-7 h-7 rounded-full bg-slate-900 text-white font-bold text-xs flex items-center justify-center shrink-0">
                  1
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-slate-900">Define Job Requirements</h4>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Upload or paste a job description. The parser extracts mandatory skills, experience, and education.
                  </p>
                </div>
              </div>

              <div className="flex gap-3">
                <div className="w-7 h-7 rounded-full bg-slate-900 text-white font-bold text-xs flex items-center justify-center shrink-0">
                  2
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-slate-900">Upload Candidate Resume</h4>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Upload candidate PDF/DOCX. Text and work history are extracted and normalized to standard canonical taxonomy.
                  </p>
                </div>
              </div>

              <div className="flex gap-3">
                <div className="w-7 h-7 rounded-full bg-slate-900 text-white font-bold text-xs flex items-center justify-center shrink-0">
                  3
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-slate-900">Inspect Evidence &amp; Explanations</h4>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Review score breakdown, requirement coverage table, verified evidence citations, and AI-generated gap recommendations.
                  </p>
                </div>
              </div>

              <div className="pt-2">
                <Link href="/jobs/new" className="block">
                  <Button variant="secondary" size="sm" className="w-full">
                    Start by Configuring a Job
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>

          {/* Recruiter Ethics & Oversight Guarantee */}
          <Card className="border-amber-200 bg-amber-50/40">
            <CardContent className="p-4 space-y-2">
              <div className="flex items-center gap-2 text-amber-800 font-semibold text-xs">
                <AlertCircle className="w-4 h-4 shrink-0 text-amber-600" />
                <span>Ethical AI &amp; Recruiter Authority</span>
              </div>
              <p className="text-xs text-amber-900/90 leading-relaxed">
                This system does NOT rank candidates, auto-reject applications, or produce automated hiring verdicts.
                All outputs serve solely to assist human recruiters with transparent, auditable evidence.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
