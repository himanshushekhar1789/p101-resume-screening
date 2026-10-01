'use client';

import React from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, FileSearch } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';

export default function CandidateDetailPage() {
  const params = useParams();
  const id = params?.id as string;

  return (
    <div className="space-y-6 max-w-4xl mx-auto py-8">
      <div className="flex items-center gap-3">
        <Link href="/analysis">
          <Button variant="outline" size="sm" leftIcon={<ArrowLeft className="w-4 h-4" />}>
            Back to Workspace
          </Button>
        </Link>
        <h1 className="text-xl font-bold text-slate-900">
          Candidate Evaluation Record: {id}
        </h1>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <FileSearch className="w-5 h-5 text-indigo-600" />
            <CardTitle>Decision-Support Record</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-4 text-xs text-slate-600">
          <p>
            This candidate screening record is loaded in the Analysis Workspace.
            Each screening provides full deterministic coverage, SentenceTransformer semantic similarity,
            and grounded Phase 10 LLM recommendations.
          </p>
          <div className="pt-2">
            <Link href="/analysis">
              <Button variant="primary" size="sm">
                Open in Analysis Workspace
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
