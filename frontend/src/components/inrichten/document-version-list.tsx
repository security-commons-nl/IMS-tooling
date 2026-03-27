'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { StatusBadge } from '@/components/shared/status-badge';
import { api } from '@/lib/api-client';
import { format } from 'date-fns';
import { nl } from 'date-fns/locale';
import type { DocumentResponse, DocumentVersionResponse } from '@/lib/api-types';

interface DocumentVersionListProps {
  documents: DocumentResponse[];
}

const DOC_TYPE_VARIANT: Record<string, 'primary' | 'warning' | 'success' | 'default'> = {
  beleid: 'primary',
  governance: 'warning',
  register: 'success',
  rapport: 'default',
  procedure: 'default',
};

const VISIBILITY_VARIANT: Record<string, 'default' | 'warning' | 'danger'> = {
  intern: 'default',
  vertrouwelijk: 'warning',
  geheim: 'danger',
};

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '-';
  try {
    return format(new Date(dateStr), 'd MMM yyyy', { locale: nl });
  } catch {
    return dateStr;
  }
}

function DocumentCard({ document }: { document: DocumentResponse }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const { data: versions } = useSWR<DocumentVersionResponse[]>(
    isExpanded ? `/documents/${document.id}/versions/` : null,
    () => api.documents.listVersions(document.id),
  );

  return (
    <Card padding="sm" className="transition-shadow hover:shadow-md">
      <button
        type="button"
        className="flex w-full items-start justify-between text-left"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold text-neutral-900">
            {document.title}
          </h3>
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            <Badge variant={DOC_TYPE_VARIANT[document.document_type] || 'default'}>
              {document.document_type}
            </Badge>
            {document.domain && (
              <Badge variant="primary">{document.domain}</Badge>
            )}
            <Badge variant={VISIBILITY_VARIANT[document.visibility] || 'default'}>
              {document.visibility}
            </Badge>
            {document.withdrawn_at && (
              <Badge variant="danger">Ingetrokken</Badge>
            )}
          </div>
        </div>
        <div className="ml-3 flex-shrink-0">
          {isExpanded ? (
            <ChevronDownIcon className="h-5 w-5 text-neutral-400" />
          ) : (
            <ChevronRightIcon className="h-5 w-5 text-neutral-400" />
          )}
        </div>
      </button>

      {isExpanded && (
        <div className="mt-4 border-t border-neutral-100 pt-4">
          <h4 className="text-xs font-medium uppercase tracking-wide text-neutral-500 mb-3">
            Versiegeschiedenis
          </h4>
          {!versions ? (
            <p className="text-sm text-neutral-400">Laden...</p>
          ) : versions.length === 0 ? (
            <p className="text-sm text-neutral-400">Geen versies beschikbaar.</p>
          ) : (
            <div className="space-y-2">
              {versions.map((version) => (
                <div
                  key={version.id}
                  className="flex items-center justify-between rounded-md bg-neutral-50 px-3 py-2 text-sm"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs text-neutral-600">
                      v{version.version_number}
                    </span>
                    <StatusBadge status={version.status} />
                    {version.generated_by_agent && (
                      <span className="inline-flex items-center rounded bg-primary-50 px-1.5 py-0.5 text-xs text-primary-700">
                        AI Concept
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-4 text-xs text-neutral-500">
                    {version.vastgesteld_at && (
                      <span>Vastgesteld: {formatDate(version.vastgesteld_at)}</span>
                    )}
                    <span>{formatDate(version.created_at)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

export function DocumentVersionList({ documents }: DocumentVersionListProps) {
  if (documents.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-neutral-500">
        Nog geen documenten beschikbaar.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {documents.map((doc) => (
        <DocumentCard key={doc.id} document={doc} />
      ))}
    </div>
  );
}
