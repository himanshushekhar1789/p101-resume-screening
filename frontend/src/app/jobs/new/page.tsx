'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Briefcase,
  Upload,
  FileText,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  GraduationCap,
  Award,
  Clock,
  Layers,
} from 'lucide-react';
import { api, ApiError } from '@/lib/api/client';
import { JobAnalysisResponse, RequirementPriority } from '@/types/api';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';

export default function NewJobPage() {
  const router = useRouter();

  // Mode: 'paste' | 'upload'
  const [mode, setMode] = useState<'paste' | 'upload'>('paste');

  // Input states
  const [jobTitle, setJobTitle] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Execution states
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<JobAnalysisResponse | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const validExtensions = ['.pdf', '.docx', '.txt'];
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!validExtensions.includes(ext)) {
        setError('Unsupported file type. Please upload a .pdf, .docx, or .txt file.');
        return;
      }
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleAnalyze = async () => {
    setError(null);
    setIsLoading(true);

    try {
      let result: JobAnalysisResponse;

      if (mode === 'upload') {
        if (!selectedFile) {
          setError('Please select a file to upload.');
          setIsLoading(false);
          return;
        }
        result = await api.analyzeJobFile(selectedFile, jobTitle || undefined);
      } else {
        if (!jobDescription.trim()) {
          setError('Please paste or enter the job description text.');
          setIsLoading(false);
          return;
        }
        result = await api.analyzeJobText(jobDescription, jobTitle || undefined);
      }

      setAnalysisResult(result);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(`Analysis Error (${err.status}): ${err.message}`);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred while analyzing the job description.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleProceedToScreening = () => {
    if (analysisResult) {
      localStorage.setItem('p101_active_job', JSON.stringify(analysisResult.profile));
      router.push('/analysis');
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
          Configure Job Description
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Extract structured requirements, mandatory skills, experience thresholds, and education criteria.
        </p>
      </div>

      {error && (
        <Alert type="error" title="Analysis Request Failed">
          {error}
        </Alert>
      )}

      {/* Input Options Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-indigo-600" />
            <CardTitle>Job Specification Source</CardTitle>
          </div>
          {/* Tab Selector */}
          <div className="flex items-center bg-slate-100 p-1 rounded-lg">
            <button
              type="button"
              onClick={() => {
                setMode('paste');
                setError(null);
              }}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                mode === 'paste'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Option B: Paste Text
            </button>
            <button
              type="button"
              onClick={() => {
                setMode('upload');
                setError(null);
              }}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                mode === 'upload'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Option A: Upload Document
            </button>
          </div>
        </CardHeader>

        <CardContent className="space-y-5">
          {/* Job Title Optional Input */}
          <div>
            <label htmlFor="jobTitle" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Job Title <span className="text-slate-400 font-normal lowercase">(optional override)</span>
            </label>
            <input
              id="jobTitle"
              type="text"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              placeholder="e.g. Senior Backend Engineer"
              className="w-full px-3.5 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900 transition-colors"
            />
          </div>

          {mode === 'paste' ? (
            <div>
              <label htmlFor="jobDescription" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Job Description Text <span className="text-rose-500">*</span>
              </label>
              <textarea
                id="jobDescription"
                rows={10}
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste the full job description here, including responsibilities, required skills, preferred qualifications, and experience expectations..."
                className="w-full px-3.5 py-2.5 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900 font-mono text-xs transition-colors"
              />
            </div>
          ) : (
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Upload Job File (PDF, DOCX, TXT) <span className="text-rose-500">*</span>
              </label>
              <div className="border-2 border-dashed border-slate-300 hover:border-slate-400 rounded-xl p-8 text-center transition-colors">
                <input
                  id="job-file-upload"
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <label
                  htmlFor="job-file-upload"
                  className="cursor-pointer flex flex-col items-center justify-center space-y-2"
                >
                  <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-600">
                    <Upload className="w-6 h-6" />
                  </div>
                  <div className="text-sm font-medium text-slate-900">
                    {selectedFile ? selectedFile.name : 'Click or drag file to upload'}
                  </div>
                  <div className="text-xs text-slate-500">
                    Supports PDF, DOCX, or plain text up to 10MB
                  </div>
                </label>
              </div>
            </div>
          )}

          <div className="flex justify-end pt-2">
            <Button
              variant="primary"
              size="md"
              isLoading={isLoading}
              onClick={handleAnalyze}
              leftIcon={<FileText className="w-4 h-4" />}
            >
              {isLoading ? 'Analyzing Job Requirements...' : 'Analyze Job Description'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Structured Requirements Results Panel */}
      {analysisResult && (
        <div className="space-y-6 animate-fadeIn">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-emerald-50 border border-emerald-200">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
              <div>
                <h3 className="text-sm font-bold text-emerald-950">
                  Requirements Extracted: {analysisResult.job_title}
                </h3>
                <p className="text-xs text-emerald-800">
                  {analysisResult.profile.skills.length} skills,{' '}
                  {analysisResult.profile.experience.length} experience requirements,{' '}
                  {analysisResult.profile.education.length} education criteria.
                </p>
              </div>
            </div>

            <Button
              variant="primary"
              size="sm"
              onClick={handleProceedToScreening}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Use for Screening in Workspace
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Required Skills (Must-Have) */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-purple-600" />
                  <CardTitle>Required Skills (Must-Have)</CardTitle>
                </div>
                <Badge variant="must_have">
                  {analysisResult.profile.skills.filter((s) => s.priority === 'must_have').length}
                </Badge>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {analysisResult.profile.skills.filter((s) => s.priority === 'must_have').length === 0 ? (
                    <p className="text-xs text-slate-500 italic">No explicit must-have skills identified.</p>
                  ) : (
                    analysisResult.profile.skills
                      .filter((s) => s.priority === 'must_have')
                      .map((skill, idx) => (
                        <div
                          key={idx}
                          className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between text-xs"
                        >
                          <div>
                            <span className="font-semibold text-slate-900">{skill.name}</span>
                            {skill.category && (
                              <span className="text-slate-500 ml-2">({skill.category})</span>
                            )}
                          </div>
                          {skill.minimum_years && (
                            <span className="text-slate-600 font-medium">
                              {skill.minimum_years}+ yrs
                            </span>
                          )}
                        </div>
                      ))
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Preferred Skills (Nice-To-Have) */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-blue-600" />
                  <CardTitle>Preferred Skills (Nice-To-Have)</CardTitle>
                </div>
                <Badge variant="nice_to_have">
                  {analysisResult.profile.skills.filter((s) => s.priority === 'nice_to_have').length}
                </Badge>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {analysisResult.profile.skills.filter((s) => s.priority === 'nice_to_have').length === 0 ? (
                    <p className="text-xs text-slate-500 italic">No nice-to-have skills specified.</p>
                  ) : (
                    analysisResult.profile.skills
                      .filter((s) => s.priority === 'nice_to_have')
                      .map((skill, idx) => (
                        <div
                          key={idx}
                          className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between text-xs"
                        >
                          <div>
                            <span className="font-semibold text-slate-900">{skill.name}</span>
                            {skill.category && (
                              <span className="text-slate-500 ml-2">({skill.category})</span>
                            )}
                          </div>
                          {skill.minimum_years && (
                            <span className="text-slate-600 font-medium">
                              {skill.minimum_years}+ yrs
                            </span>
                          )}
                        </div>
                      ))
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Experience Requirements */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-amber-600" />
                  <CardTitle>Experience Requirements</CardTitle>
                </div>
                <Badge variant="default">
                  {analysisResult.profile.experience.length}
                </Badge>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {analysisResult.profile.experience.length === 0 ? (
                    <p className="text-xs text-slate-500 italic">No specific experience requirement identified.</p>
                  ) : (
                    analysisResult.profile.experience.map((exp, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1 text-xs"
                      >
                        <div className="flex items-center justify-between font-medium text-slate-900">
                          <span>{exp.description}</span>
                          <Badge variant={exp.priority}>{exp.priority}</Badge>
                        </div>
                        {exp.minimum_years && (
                          <div className="text-slate-500">
                            Required Tenure: <span className="font-semibold text-slate-700">{exp.minimum_years} years</span>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Education & Certifications */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <GraduationCap className="w-4 h-4 text-emerald-600" />
                  <CardTitle>Education &amp; Certifications</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    Education Criteria
                  </h4>
                  {analysisResult.profile.education.length === 0 ? (
                    <p className="text-xs text-slate-500 italic">No formal education criteria specified.</p>
                  ) : (
                    analysisResult.profile.education.map((edu, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs flex justify-between items-center"
                      >
                        <span className="font-semibold text-slate-900">
                          {edu.degree || 'Degree'} {edu.field ? `in ${edu.field}` : ''}
                        </span>
                        <Badge variant={edu.priority}>{edu.priority}</Badge>
                      </div>
                    ))
                  )}
                </div>

                <div>
                  <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    Certifications
                  </h4>
                  {analysisResult.profile.certifications.length === 0 ? (
                    <p className="text-xs text-slate-500 italic">No specific certifications requested.</p>
                  ) : (
                    analysisResult.profile.certifications.map((cert, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs flex justify-between items-center"
                      >
                        <span className="font-semibold text-slate-900">{cert.name}</span>
                        <Badge variant={cert.priority}>{cert.priority}</Badge>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Key Responsibilities */}
          {analysisResult.profile.responsibilities.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Key Responsibilities</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="list-disc list-inside space-y-1.5 text-xs text-slate-700">
                  {analysisResult.profile.responsibilities.map((resp, idx) => (
                    <li key={idx} className="leading-relaxed">
                      {resp}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
