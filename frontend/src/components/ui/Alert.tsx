import React from 'react';
import { AlertCircle, CheckCircle2, Info, AlertTriangle } from 'lucide-react';

interface AlertProps {
  type?: 'error' | 'warning' | 'info' | 'success';
  title?: string;
  children: React.ReactNode;
  className?: string;
  onDismiss?: () => void;
}

export function Alert({
  type = 'info',
  title,
  children,
  className = '',
}: AlertProps) {
  let styles = 'bg-sky-50 border-sky-200 text-sky-900';
  let IconComponent = Info;

  switch (type) {
    case 'error':
      styles = 'bg-rose-50 border-rose-200 text-rose-900';
      IconComponent = AlertCircle;
      break;
    case 'warning':
      styles = 'bg-amber-50 border-amber-200 text-amber-900';
      IconComponent = AlertTriangle;
      break;
    case 'success':
      styles = 'bg-emerald-50 border-emerald-200 text-emerald-900';
      IconComponent = CheckCircle2;
      break;
    case 'info':
      styles = 'bg-sky-50 border-sky-200 text-sky-900';
      IconComponent = Info;
      break;
  }

  return (
    <div
      role="alert"
      className={`rounded-lg border p-4 flex gap-3 text-sm leading-relaxed ${styles} ${className}`}
    >
      <IconComponent className="w-5 h-5 shrink-0 mt-0.5" aria-hidden="true" />
      <div className="flex-1">
        {title && <h4 className="font-semibold text-sm mb-1">{title}</h4>}
        <div className="text-sm opacity-90">{children}</div>
      </div>
    </div>
  );
}
