'use client';

import { cn } from '@/lib/utils';

interface ReadinessScoreGaugeProps {
  score: number;
  size?: number;
  showLabel?: boolean;
}

export function ReadinessScoreGauge({ score, size = 120, showLabel = true }: ReadinessScoreGaugeProps) {
  const circumference = 2 * Math.PI * 50;
  const offset = circumference - (score / 100) * circumference;
  
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };
  
  const getScoreBgColor = (score: number) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg className="transform -rotate-90" width={size} height={size}>
          <circle
            className="text-gray-200"
            strokeWidth="8"
            stroke="currentColor"
            fill="transparent"
            r="50"
            cx={size / 2}
            cy={size / 2}
          />
          <circle
            className={cn('transition-all duration-1000', getScoreColor(score).replace('text-', 'stroke-'))}
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            fill="transparent"
            r="50"
            cx={size / 2}
            cy={size / 2}
            style={{ filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))' }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={cn('text-2xl font-bold', getScoreColor(score))}>
            {score}
          </span>
        </div>
      </div>
      {showLabel && (
        <div className="mt-3 text-center">
          <p className={cn('text-sm font-medium', getScoreColor(score))}>
            Tax Readiness Score
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {score >= 80 ? 'Excellent' : score >= 60 ? 'Good' : 'Needs Attention'}
          </p>
        </div>
      )}
    </div>
  );
}