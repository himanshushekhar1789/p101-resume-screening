'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  FileSearch,
  Upload,
  FileText,
  Briefcase,
  AlertCircle,
  RotateCcw,
  CheckCircle2,
  Download,
  Loader2,
  Trash2,
} from 'lucide-react';
import { api, ApiError } from '@/lib/api/client';
import {
  CandidateJobMatchWithScoreResponse,
  JobProfile,
} from '@/types/api';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Alert } from '@/components/ui/Alert';
import { OverallScoreBadge } from '@/components/score/OverallScoreBadge';
import { ScoreBreakdownCard } from '@/components/score/ScoreBreakdownCard';
import { ScoreExplanationPanel } from '@/components/score/ScoreExplanationPanel';
import { RequirementCoverageTable } from '@/components/requirements/RequirementCoverageTable';
import { SkillGapSection } from '@/components/skill-gaps/SkillGapSection';
import { LLMExplanationView } from '@/components/explanation/LLMExplanationView';

export default function AnalysisPage() {
  // Session Job
  const [activeJob, setActiveJob] = useState<JobProfile | null>(null);

  // Job Mode: 'session' | 'file'
  const [jobMode, setJobMode] = useState<'session' | 'file'>('file');
  const [jobFile, setJobFile] = useState<File | null>(null);

  // Resume state
  const [resumeFile, setResumeFile] = useState<File | null>(null);

  // Loading & Step indicator
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [loadingStep, setLoadingStep] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  // Analysis Result
  const [result, setResult] = useState<CandidateJobMatchWithScoreResponse | null>(null);

  useEffect(() => {
    try {
      const storedJob = localStorage.getItem('p101_active_job');
      if (storedJob) {
        const parsed = JSON.parse(storedJob);
        setActiveJob(parsed);
        setJobMode('session');
      }
    } catch {
      // ignore
    }
  }, []);

  const handleResumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const validExtensions = ['.pdf', '.docx'];
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!validExtensions.includes(ext)) {
        setError('Unsupported resume file format. Please upload a .pdf or .docx document.');
        return;
      }
      setResumeFile(file);
      setError(null);
    }
  };

  const handleJobFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const validExtensions = ['.pdf', '.docx', '.txt'];
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!validExtensions.includes(ext)) {
        setError('Unsupported job file format. Please upload a .pdf, .docx, or .txt document.');
        return;
      }
      setJobFile(file);
      setError(null);
    }
  };

  const handleStartAnalysis = async () => {
    setError(null);

    if (!resumeFile) {
      setError('Please select a candidate resume file (.pdf or .docx) to analyze.');
      return;
    }

    if (jobMode === 'file' && !jobFile) {
      setError('Please select a job description document or switch to use an active job role.');
      return;
    }

    if (jobMode === 'session' && !activeJob) {
      setError('No active job profile found in session. Please upload a job file or configure a job in Job Setup.');
      return;
    }

    setIsAnalyzing(true);
    setLoadingStep('Uploading documents and parsing candidate profile...');

    try {
      let analysisResponse: CandidateJobMatchWithScoreResponse;

      if (jobMode === 'file' && jobFile) {
        setLoadingStep('Running end-to-end extraction, matching, and scoring pipeline...');
        analysisResponse = await api.matchFromFiles({
          resumeFile,
          jobFile,
          includeSemantic: true,
          includeScore: true,
          includeSkillGaps: true,
          includeExplanation: true,
        });
      } else if (activeJob) {
        setLoadingStep('Extracting structured candidate profile from resume...');
        const resumeExtraction = await api.extractResume(resumeFile);

        setLoadingStep('Evaluating requirements, hybrid scoring, and AI explanation...');
        analysisResponse = await api.matchAndAnalyze({
          candidate: resumeExtraction.profile,
          job: activeJob,
          candidate_id: resumeFile.name,
          job_id: activeJob.job_title,
          include_semantic: true,
          include_score: true,
          include_skill_gaps: true,
          include_explanation: true,
        });
      } else {
        throw new Error('Missing job configuration.');
      }

      setResult(analysisResponse);

      // Save to recent analyses in localStorage
      try {
        const existing = JSON.parse(localStorage.getItem('p101_recent_analyses') || '[]');
        const candidateName =
          analysisResponse.score?.candidate_name ||
          analysisResponse.candidate_id ||
          resumeFile.name;
        const jobTitle =
          analysisResponse.job_title ||
          (activeJob ? activeJob.job_title : jobFile?.name) ||
          'Target Role';
        const score = analysisResponse.score?.candidate_fit_score ?? 0;

        const newEntry = {
          id: `eval_${Date.now()}`,
          candidate: candidateName,
          job: jobTitle,
          score,
          date: new Date().toLocaleDateString(),
        };

        const updated = [newEntry, ...existing].slice(0, 10);
        localStorage.setItem('p101_recent_analyses', JSON.stringify(updated));
      } catch {
        // storage save error ignored
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(`Analysis Error (${err.status}): ${err.message}`);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred during candidate analysis.');
      }
    } finally {
      setIsAnalyzing(false);
      setLoadingStep('');
    }
  };

  const handleReset = () => {
    setResult(null);
    setResumeFile(null);
    setError(null);
  };

  const handleDownloadJSON = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analysis_${result.candidate_id || 'candidate'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            Candidate Analysis Workspace
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Multi-layer hybrid scoring, requirement-by-requirement audit, and evidence-grounded AI recommendations.
          </p>
        </div>

        {result && (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownloadJSON}
              leftIcon={<Download className="w-4 h-4" />}
            >
              Export JSON Audit
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleReset}
              leftIcon={<RotateCcw className="w-4 h-4" />}
            >
              Screen Another Resume
            </Button>
          </div>
        )}
      </div>

      {error && (
        <Alert type="error" title="Analysis Workflow Failed">
          {error}
        </Alert>
      )}

      {/* Screen Form (shown when no result is active) */}
      {!result && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Step 1: Target Role Setup */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Briefcase className="w-5 h-5 text-indigo-600" />
                  <CardTitle>1. Target Job Description</CardTitle>
                </div>

                {activeJob && (
                  <div className="flex items-center bg-slate-100 p-0.5 rounded-lg text-xs">
                    <button
                      type="button"
                      onClick={() => setJobMode('session')}
                      className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                        jobMode === 'session'
                          ? 'bg-white text-slate-900 shadow-xs'
                          : 'text-slate-600'
                      }`}
                    >
                      Active Role
                    </button>
                    <button
                      type="button"
                      onClick={() => setJobMode('file')}
                      className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                        jobMode === 'file'
                          ? 'bg-white text-slate-900 shadow-xs'
                          : 'text-slate-600'
                      }`}
                    >
                      Upload File
                    </button>
                  </div>
                )}
              </CardHeader>

              <CardContent className="space-y-4">
                {jobMode === 'session' && activeJob ? (
                  <div className="p-4 rounded-xl bg-indigo-50/50 border border-indigo-200/80 space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sm text-indigo-950">
                        {activeJob.job_title}
                      </span>
                      <span className="bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded font-medium text-[11px]">
                        Pre-configured
                      </span>
                    </div>
                    <p className="text-slate-600">
                      {activeJob.skills.length} skills ({activeJob.skills.filter(s => s.priority === 'must_have').length} must-have) •{' '}
                      {activeJob.experience.length} experience criteria
                    </p>
                    <div className="pt-1">
                      <Link
                        href="/jobs/new"
                        className="text-indigo-600 hover:text-indigo-800 font-medium inline-flex items-center gap-1"
                      >
                        Change role configuration →
                      </Link>
                    </div>
                  </div>
                ) : (
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                      Upload Job Description (PDF, DOCX, TXT)
                    </label>
                    <div className="border-2 border-dashed border-slate-300 hover:border-slate-400 rounded-xl p-6 text-center transition-colors">
                      <input
                        id="job-upload-input"
                        type="file"
                        accept=".pdf,.docx,.txt"
                        onChange={handleJobFileChange}
                        className="hidden"
                      />
                      <label
                        htmlFor="job-upload-input"
                        className="cursor-pointer flex flex-col items-center space-y-2"
                      >
                        <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-600">
                          <Upload className="w-5 h-5" />
                        </div>
                        <span className="text-sm font-medium text-slate-900">
                          {jobFile ? jobFile.name : 'Choose Job Description Document'}
                        </span>
                        <span className="text-xs text-slate-400">PDF, DOCX, or plain text</span>
                      </label>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Step 2: Candidate Resume Upload */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-indigo-600" />
                  <CardTitle>2. Candidate Resume</CardTitle>
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    Upload Resume Document (PDF or DOCX) <span className="text-rose-500">*</span>
                  </label>
                  <div className="border-2 border-dashed border-slate-300 hover:border-slate-400 rounded-xl p-6 text-center transition-colors">
                    <input
                      id="resume-upload-input"
                      type="file"
                      accept=".pdf,.docx"
                      onChange={handleResumeChange}
                      className="hidden"
                    />
                    <label
                      htmlFor="resume-upload-input"
                      className="cursor-pointer flex flex-col items-center space-y-2"
                    >
                      <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-600">
                        <Upload className="w-5 h-5" />
                      </div>
                      <span className="text-sm font-medium text-slate-900">
                        {resumeFile ? resumeFile.name : 'Choose Candidate Resume'}
                      </span>
                      <span className="text-xs text-slate-400">Standard PDF or DOCX up to 10MB</span>
                    </label>
                  </div>
                </div>

                {resumeFile && (
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2 truncate">
                      <FileText className="w-4 h-4 text-slate-500 shrink-0" />
                      <span className="font-medium text-slate-800 truncate">{resumeFile.name}</span>
                      <span className="text-slate-400 shrink-0">
                        ({(resumeFile.size / 1024).toFixed(1)} KB)
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setResumeFile(null)}
                      className="text-slate-400 hover:text-rose-600 ml-2"
                      aria-label="Remove resume file"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Action Button & Loading Status */}
          <div className="flex flex-col items-center justify-center pt-4 space-y-3">
            <Button
              variant="primary"
              size="lg"
              isLoading={isAnalyzing}
              onClick={handleStartAnalysis}
              leftIcon={<FileSearch className="w-5 h-5" />}
              className="w-full sm:w-auto px-8"
            >
              {isAnalyzing ? 'Executing Screening Engine...' : 'Run Full Candidate Analysis'}
            </Button>

            {isAnalyzing && (
              <div className="flex items-center gap-2 text-xs text-slate-600 animate-pulse">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-600" />
                <span>{loadingStep || 'Processing match pipeline...'}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Render Analysis Results when Available */}
      {result && (
        <div className="space-y-8 animate-fadeIn" data-testid="analysis-results">
          {/* Candidate Overview Header */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200/90 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Evaluation Report
              </div>
              <h2 className="text-2xl font-extrabold tracking-tight text-slate-900 mt-1">
                {result.score?.candidate_name || result.candidate_id || 'Candidate Profile'}
              </h2>
              <div className="flex flex-wrap items-center gap-2 mt-1 text-xs text-slate-500">
                <span className="font-medium text-slate-700">Role: {result.job_title || 'Target Job'}</span>
                <span>•</span>
                <span>Evaluated: {result.matches.length} criteria</span>
                <span>•</span>
                <span>
                  Satisfied: {result.summary.matched} / {result.summary.total_requirements}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 bg-slate-100 px-3 py-1 rounded-full border border-slate-200">
                Recruiter Decision Support
              </span>
            </div>
          </div>

          {/* Top Row: Overall Score Badge + Score Component Breakdown */}
          {result.score && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-1">
                <OverallScoreBadge
                  score={result.score.candidate_fit_score}
                  percentage={Math.round(result.score.percentage_score)}
                  allMustHavesSatisfied={result.score.all_must_haves_satisfied}
                />
              </div>

              <div className="lg:col-span-2">
                <ScoreBreakdownCard
                  components={result.score.components}
                  weightsRenormalized={result.score.weights_renormalized}
                />
              </div>
            </div>
          )}

          {/* Score Explanation Panel */}
          {result.score && (
            <ScoreExplanationPanel explanation={result.score.explanation} />
          )}

          {/* Requirement Coverage Table */}
          <RequirementCoverageTable matches={result.matches} />

          {/* Skill-Gap Analysis & Evidence Grounding (Phase 9) */}
          {result.gaps && <SkillGapSection gaps={result.gaps} />}

          {/* AI Decision-Support Explanation & Personalized Recommendations (Phase 10) */}
          {result.explanation && <LLMExplanationView explanation={result.explanation} />}
        </div>
      )}
    </div>
  );
}
