'use client';

import { useState, useMemo } from 'react';
import { ClipboardDocumentListIcon } from '@heroicons/react/24/outline';
import { PageWrapper } from '@/components/layout/page-wrapper';
import { Card } from '@/components/ui/card';
import { Select } from '@/components/ui/select';
import { EmptyState } from '@/components/ui/empty-state';
import { CardSkeleton } from '@/components/ui/loading-skeleton';
import { DecisionLogTable } from '@/components/inrichten/decision-log-table';
import { useApi } from '@/lib/hooks/use-api';
import type { DecisionResponse } from '@/lib/api-types';

const DECISION_TYPE_OPTIONS = [
  { value: '', label: 'Alle types' },
  { value: 'mandaat', label: 'Mandaat' },
  { value: 'scope', label: 'Scope' },
  { value: 'governance', label: 'Governance' },
  { value: 'beleid', label: 'Beleid' },
  { value: 'normenkader', label: 'Normenkader' },
  { value: 'risico', label: 'Risico' },
];

const GREMIUM_OPTIONS = [
  { value: '', label: 'Alle gremia' },
  { value: 'SIMS', label: 'SIMS' },
  { value: 'TIMS', label: 'TIMS' },
  { value: 'Lijnmanagement', label: 'Lijnmanagement' },
];

export default function BesluitenPage() {
  const { data: decisions, isLoading } = useApi<DecisionResponse[]>(
    '/decisions/',
    '/decisions/',
  );

  const [typeFilter, setTypeFilter] = useState('');
  const [gremiumFilter, setGremiumFilter] = useState('');

  const filtered = useMemo(() => {
    if (!decisions) return [];
    return decisions.filter((d) => {
      if (typeFilter && d.decision_type !== typeFilter) return false;
      if (gremiumFilter && d.gremium !== gremiumFilter) return false;
      return true;
    });
  }, [decisions, typeFilter, gremiumFilter]);

  return (
    <PageWrapper
      title="Besluitlog"
      description="Alle vastgelegde besluiten. Besluiten zijn onwijzigbaar — alleen superseding is mogelijk."
    >
      {/* Filters */}
      <div className="mb-4 flex flex-wrap items-end gap-3">
        <div className="w-48">
          <Select
            label="Type"
            options={DECISION_TYPE_OPTIONS}
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          />
        </div>
        <div className="w-48">
          <Select
            label="Gremium"
            options={GREMIUM_OPTIONS}
            value={gremiumFilter}
            onChange={(e) => setGremiumFilter(e.target.value)}
          />
        </div>
      </div>

      {/* Content */}
      {isLoading && <CardSkeleton />}

      {!isLoading && (!decisions || decisions.length === 0) && (
        <Card>
          <EmptyState
            icon={ClipboardDocumentListIcon}
            title="Nog geen besluiten"
            description="Besluiten worden automatisch vastgelegd wanneer stappen worden afgerond."
          />
        </Card>
      )}

      {!isLoading && decisions && decisions.length > 0 && (
        <Card>
          <DecisionLogTable decisions={filtered} />
        </Card>
      )}
    </PageWrapper>
  );
}
