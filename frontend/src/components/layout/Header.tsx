import React from 'react';
import Link from 'next/link';
import { ShieldCheck, Sparkles, Layers } from 'lucide-react';

export function Header() {
  return (
    <header className="h-16 border-b border-slate-200/80 bg-white/95 backdrop-blur-xs sticky top-0 z-30 px-4 sm:px-6 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-9 h-9 rounded-lg bg-slate-900 text-white flex items-center justify-center font-bold tracking-tight shadow-xs group-hover:bg-slate-800 transition-colors">
            <Layers className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-900 tracking-tight text-base">
                ResumeScreen<span className="text-indigo-600">AI</span>
              </span>
              <span className="text-[10px] font-semibold uppercase tracking-wider bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded border border-slate-200">
                P_101
              </span>
            </div>
            <p className="text-[11px] text-slate-500 hidden sm:block">
              Recruiter Decision Support &amp; Evidence Grounding
            </p>
          </div>
        </Link>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-50 border border-slate-200 text-xs text-slate-600">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          <span>Non-Authoritative AI Audit</span>
        </div>
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-50 border border-indigo-200 text-xs text-indigo-700 font-medium">
          <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
          <span>Deterministic-First Hybrid Engine</span>
        </div>
      </div>
    </header>
  );
}
