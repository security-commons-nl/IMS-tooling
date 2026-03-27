'use client';

import { Cog6ToothIcon } from '@heroicons/react/24/outline';
import { PageWrapper } from '@/components/layout/page-wrapper';
import { Card } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';
import { CardSkeleton } from '@/components/ui/loading-skeleton';
import { ScoreBar } from '@/components/shared/score-bar';
import { StepProgressGrid } from '@/components/inrichten/step-progress-grid';
import { useSteps, useStepExecutions, useStepDependencies } from '@/lib/hooks/use-steps';
import { useSetupScores } from '@/lib/hooks/use-scores';

const DOMAIN_LABELS: Record<string, string> = {
  ISMS: 'Informatiebeveiliging (ISMS)',
  PIMS: 'Privacy (PIMS)',
  BCMS: 'Bedrijfscontinuiteit (BCMS)',
};

export default function InrichtenOverzichtPage() {
  const { data: steps, isLoading: stepsLoading } = useSteps();
  const { data: executions, isLoading: execLoading } = useStepExecutions();
  const { data: dependencies, isLoading: depsLoading } = useStepDependencies();
  const { data: scores } = useSetupScores();

  const isLoading = stepsLoading || execLoading || depsLoading;

  return (
    <PageWrapper
      title="Inrichting -- Overzicht"
      description="22-stappenplan voor het inrichten van uw managementsysteem."
    >
      {/* Score bars per domein */}
      {scores && scores.length > 0 && (
        <Card className="mb-6">
          <h2 className="text-sm font-semibold text-neutral-800 mb-4">
            Inrichtingsscore per domein
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {scores.map((score) => (
              <ScoreBar
                key={score.id}
                label={DOMAIN_LABELS[score.domain] || score.domain}
                value={score.score_pct}
              />
            ))}
          </div>
        </Card>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }, (_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && (!steps || steps.length === 0) && (
        <Card>
          <EmptyState
            icon={Cog6ToothIcon}
            title="Geen stappen gevonden"
            description="De inrichtingsstappen zijn nog niet geladen. Controleer de API-verbinding."
          />
        </Card>
      )}

      {/* Step progress grid */}
      {!isLoading && steps && steps.length > 0 && (
        <StepProgressGrid
          steps={steps}
          executions={executions || []}
          dependencies={dependencies || []}
        />
      )}
    </PageWrapper>
  );
}
