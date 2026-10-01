import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, HelpCircle, Info } from 'lucide-react';
import { MatchStatus, SkillGapStatus } from '@/types/api';

export type BadgeVariant =
  | 'satisfied'
  | 'insufficient'
  | 'partially_satisfied'
  | 'missing'
  | 'unmatched'
  | 'not_evaluable'
  | 'info'
  | 'must_have'
  | 'nice_to_have'
  | 'default';

interface BadgeProps {
  variant?: BadgeVariant | MatchStatus | SkillGapStatus | string;
  label?: string;
  children?: React.ReactNode;
  showIcon?: boolean;
  className?: string;
}

export function Badge({
  variant = 'default',
  label,
  children,
  showIcon = true,
  className = '',
}: BadgeProps) {
  const content = children || label;

  let bgClasses = 'bg-slate-100 text-slate-700 border-slate-200';
  let IconComponent = HelpCircle;

  switch (variant) {
    case 'satisfied':
      bgClasses = 'bg-emerald-50 text-emerald-800 border-emerald-300';
      IconComponent = CheckCircle2;
      break;
    case 'insufficient':
    case 'partially_satisfied':
      bgClasses = 'bg-amber-50 text-amber-800 border-amber-300';
      IconComponent = AlertTriangle;
      break;
    case 'missing':
    case 'unmatched':
      bgClasses = 'bg-rose-50 text-rose-800 border-rose-300';
      IconComponent = XCircle;
      break;
    case 'not_evaluable':
      bgClasses = 'bg-slate-100 text-slate-700 border-slate-300';
      IconComponent = HelpCircle;
      break;
    case 'must_have':
      bgClasses = 'bg-purple-50 text-purple-800 border-purple-300 font-semibold';
      IconComponent = Info;
      break;
    case 'nice_to_have':
      bgClasses = 'bg-blue-50 text-blue-700 border-blue-200';
      IconComponent = Info;
      break;
    case 'info':
      bgClasses = 'bg-sky-50 text-sky-800 border-sky-300';
      IconComponent = Info;
      break;
    default:
      bgClasses = 'bg-slate-100 text-slate-800 border-slate-300';
      IconComponent = Info;
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${bgClasses} ${className}`}
      role="status"
    >
      {showIcon && <IconComponent className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />}
      <span>{content}</span>
    </span>
  );
}
