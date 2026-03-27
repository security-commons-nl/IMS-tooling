'use client';

import clsx from 'clsx';
import { LockClosedIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { StatusBadge } from '@/components/shared/status-badge';
import type { StepResponse, StepExecutionResponse } from '@/lib/api-types';

interface StepCardProps {
  step: StepResponse;
  execution?: StepExecutionResponse;
  isBlocked?: boolean;
  onClick?: () => void;
}

const DOMAIN_BADGE_VARIANT: Record<string, 'primary' | 'warning' | 'success' | 'default'> = {
  ISMS: 'primary',
  PIMS: 'warning',
  BCMS: 'success',
};

function getStatus(execution?: StepExecutionResponse): string {
  if (!execution) return 'niet_gestart';
  return execution.status;
}

function getBorderClass(status: string): string {
  switch (status) {
    case 'in_uitvoering':
      return 'border-l-4 border-l-primary-500';
    case 'concept':
      return 'border-l-4 border-l-yellow-500';
    case 'in_review':
      return 'border-l-4 border-l-orange-500';
    case 'vastgesteld':
      return 'border-l-4 border-l-green-500';
    default:
      return '';
  }
}

export function StepCard({ step, execution, isBlocked, onClick }: StepCardProps) {
  const status = getStatus(execution);
  const borderClass = getBorderClass(status);
  const isCompleted = status === 'vastgesteld';

  return (
    <Card
      padding="sm"
      className={clsx(
        'relative cursor-pointer transition-shadow hover:shadow-md',
        borderClass,
        isBlocked && 'opacity-40 cursor-not-allowed',
        status === 'niet_gestart' && 'bg-neutral-50',
      )}
      onClick={isBlocked ? undefined : onClick}
    >
      {isBlocked && (
        <div className="absolute inset-0 flex items-center justify-center z-10">
          <LockClosedIcon className="h-8 w-8 text-neutral-400" />
        </div>
      )}

      <div className="flex items-start gap-3">
        <div
          className={clsx(
            'flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg text-lg font-bold',
            isCompleted
              ? 'bg-green-100 text-green-700'
              : 'bg-primary-50 text-primary-700',
          )}
        >
          {isCompleted ? (
            <CheckCircleIcon className="h-6 w-6" />
          ) : (
            step.number
          )}
        </div>

        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold text-neutral-900 truncate">
            {step.name}
          </h3>

          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            <StatusBadge status={status} />
            <Badge variant="neutral">{step.required_gremium}</Badge>
            {step.domain && (
              <Badge variant={DOMAIN_BADGE_VARIANT[step.domain] || 'default'}>
                {step.domain}
              </Badge>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}
