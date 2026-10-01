'use client';

import React from 'react';
import Link from 'next/link';
import { Users, FileSearch, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';

export default function CandidatesPage() {
  return (
    <div className="space-y-6 max-w-4xl mx-auto py-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Candidate Screenings
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Single-candidate deep-dive evaluations with deterministic-first audit trails.
        </p>
      </div>

      <Card>
        <CardContent className="py-16 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-indigo-50 text-indigo-600 mx-auto flex items-center justify-center">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-900">
              Launch Candidate Screening Workspace
            </h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
              Select or upload a target job description and evaluate candidate resumes individually with full requirement breakdown and evidence verification.
            </p>
          </div>
          <div className="pt-2">
            <Link href="/analysis">
              <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
                Go to Analysis Workspace
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
