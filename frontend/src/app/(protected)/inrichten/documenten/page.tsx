'use client';

import { useState, useMemo } from 'react';
import { DocumentTextIcon } from '@heroicons/react/24/outline';
import { PageWrapper } from '@/components/layout/page-wrapper';
import { Card } from '@/components/ui/card';
import { Select } from '@/components/ui/select';
import { EmptyState } from '@/components/ui/empty-state';
import { CardSkeleton } from '@/components/ui/loading-skeleton';
import { DocumentVersionList } from '@/components/inrichten/document-version-list';
import { useApi } from '@/lib/hooks/use-api';
import type { DocumentResponse } from '@/lib/api-types';

const DOC_TYPE_OPTIONS = [
  { value: '', label: 'Alle types' },
  { value: 'beleid', label: 'Beleid' },
  { value: 'governance', label: 'Governance' },
  { value: 'register', label: 'Register' },
  { value: 'rapport', label: 'Rapport' },
  { value: 'procedure', label: 'Procedure' },
];

const DOMAIN_OPTIONS = [
  { value: '', label: 'Alle domeinen' },
  { value: 'ISMS', label: 'ISMS' },
  { value: 'PIMS', label: 'PIMS' },
  { value: 'BCMS', label: 'BCMS' },
];

export default function DocumentenPage() {
  const { data: documents, isLoading } = useApi<DocumentResponse[]>(
    '/documents/',
    '/documents/',
  );

  const [typeFilter, setTypeFilter] = useState('');
  const [domainFilter, setDomainFilter] = useState('');

  const filtered = useMemo(() => {
    if (!documents) return [];
    return documents.filter((d) => {
      if (typeFilter && d.document_type !== typeFilter) return false;
      if (domainFilter && d.domain !== domainFilter) return false;
      return true;
    });
  }, [documents, typeFilter, domainFilter]);

  return (
    <PageWrapper
      title="Documenten"
      description="Alle IMS-documenten met versiegeschiedenis."
    >
      {/* Filters */}
      <div className="mb-4 flex flex-wrap items-end gap-3">
        <div className="w-48">
          <Select
            label="Type"
            options={DOC_TYPE_OPTIONS}
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          />
        </div>
        <div className="w-48">
          <Select
            label="Domein"
            options={DOMAIN_OPTIONS}
            value={domainFilter}
            onChange={(e) => setDomainFilter(e.target.value)}
          />
        </div>
      </div>

      {/* Content */}
      {isLoading && <CardSkeleton />}

      {!isLoading && (!documents || documents.length === 0) && (
        <Card>
          <EmptyState
            icon={DocumentTextIcon}
            title="Nog geen documenten"
            description="Documenten worden aangemaakt wanneer stappen worden uitgevoerd."
          />
        </Card>
      )}

      {!isLoading && documents && documents.length > 0 && (
        <DocumentVersionList documents={filtered} />
      )}
    </PageWrapper>
  );
}
