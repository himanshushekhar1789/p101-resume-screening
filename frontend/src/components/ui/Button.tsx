import React from 'react';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  disabled,
  className = '',
  ...props
}: ButtonProps) {
  const baseClasses =
    'inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';

  let variantClasses = '';
  switch (variant) {
    case 'primary':
      variantClasses =
        'bg-slate-900 text-white hover:bg-slate-800 focus:ring-slate-950 border border-transparent shadow-xs';
      break;
    case 'secondary':
      variantClasses =
        'bg-slate-100 text-slate-900 hover:bg-slate-200 focus:ring-slate-300 border border-slate-200';
      break;
    case 'outline':
      variantClasses =
        'bg-white text-slate-700 hover:bg-slate-50 focus:ring-slate-400 border border-slate-300 shadow-xs';
      break;
    case 'danger':
      variantClasses =
        'bg-rose-600 text-white hover:bg-rose-700 focus:ring-rose-500 border border-transparent shadow-xs';
      break;
    case 'ghost':
      variantClasses =
        'bg-transparent text-slate-600 hover:bg-slate-100 hover:text-slate-900 focus:ring-slate-300';
      break;
  }

  let sizeClasses = '';
  switch (size) {
    case 'sm':
      sizeClasses = 'px-3 py-1.5 text-xs gap-1.5';
      break;
    case 'md':
      sizeClasses = 'px-4 py-2 text-sm gap-2';
      break;
    case 'lg':
      sizeClasses = 'px-5 py-2.5 text-base gap-2.5';
      break;
  }

  return (
    <button
      disabled={disabled || isLoading}
      className={`${baseClasses} ${variantClasses} ${sizeClasses} ${className}`}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin shrink-0" aria-hidden="true" />
      ) : (
        leftIcon && <span className="shrink-0">{leftIcon}</span>
      )}
      <span>{children}</span>
      {!isLoading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
    </button>
  );
}
