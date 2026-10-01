'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Briefcase, PlusCircle, Trash2, ArrowRight, Layers, Clock, GraduationCap } from 'lucide-react';
import { JobProfile } from '@/types/api';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

export default function JobsPage() {
  const [activeJob, setActiveJob] = useState<JobProfile | null>(null);

  useEffect(() => {
    try {
      const stored = localStorage.getItem('p101_active_job');
      if (stored) {
        setActiveJob(JSON.parse(stored));
      }
    } catch {
      // ignore JSON parse error
    }
  }, []);

  const handleClearJob = () => {
    localStorage.removeItem('p101_active_job');
    setActiveJob(null);
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            Job Profiles
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Manage target roles and requirement specifications for resume screening.
          </p>
        </div>

        <Link href="/jobs/new">
          <Button variant="primary" size="md" leftIcon={<PlusCircle className="w-4 h-4" />}>
            Configure New Role
          </Button>
        </Link>
      </div>

      {!activeJob ? (
        <Card>
          <CardContent className="py-16 text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-400 mx-auto flex items-center justify-center">
              <Briefcase className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-900">No active job configured</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
                Upload or paste a job description to extract structured requirements and begin screening candidate resumes.
              </p>
            </div>
            <div className="pt-2">
              <Link href="/jobs/new">
                <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
                  Configure Role Now
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          <Card className="border-indigo-100 bg-indigo-50/20">
            <CardHeader>
              <div>
                <div className="flex items-center gap-2">
                  <Badge variant="must_have">Active Screening Role</Badge>
                  <CardTitle className="text-lg font-bold text-slate-900">
                    {activeJob.job_title}
                  </CardTitle>
                </div>
                {activeJob.department && (
                  <CardDescription>Department: {activeJob.department}</CardDescription>
                )}
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleClearJob}
                  leftIcon={<Trash2 className="w-4 h-4 text-rose-500" />}
                >
                  Remove Role
                </Button>
                <Link href="/analysis">
                  <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
                    Screen Candidates
                  </Button>
                </Link>
              </div>
            </CardHeader>

            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div className="p-3 rounded-lg bg-white border border-slate-200 flex items-center gap-3">
                  <Layers className="w-5 h-5 text-indigo-600 shrink-0" />
                  <div>
                    <span className="font-semibold text-slate-900">
                      {activeJob.skills.length} Evaluated Skills
                    </span>
                    <span className="block text-slate-500 text-[11px]">
                      {activeJob.skills.filter((s) => s.priority === 'must_have').length} Must-Have,{' '}
                      {activeJob.skills.filter((s) => s.priority === 'nice_to_have').length} Nice-To-Have
                    </span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-white border border-slate-200 flex items-center gap-3">
                  <Clock className="w-5 h-5 text-amber-600 shrink-0" />
                  <div>
                    <span className="font-semibold text-slate-900">
                      {activeJob.experience.length} Experience Criteria
                    </span>
                    <span className="block text-slate-500 text-[11px]">
                      Tenure requirement checks
                    </span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-white border border-slate-200 flex items-center gap-3">
                  <GraduationCap className="w-5 h-5 text-emerald-600 shrink-0" />
                  <div>
                    <span className="font-semibold text-slate-900">
                      {activeJob.education.length} Education Requirements
                    </span>
                    <span className="block text-slate-500 text-[11px]">
                      Degree and credentials
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
