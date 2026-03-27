'use client';

import { Fragment, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { format } from 'date-fns';
import { nl } from 'date-fns/locale';
import type { DecisionResponse } from '@/lib/api-types';

interface DecisionLogTableProps {
  decisions: DecisionResponse[];
}

const DECISION_TYPE_VARIANT: Record<string, 'primary' | 'warning' | 'success' | 'danger' | 'default'> = {
  mandaat: 'primary',
  scope: 'primary',
  governance: 'warning',
  beleid: 'warning',
  normenkader: 'success',
  risico: 'danger',
};

export function DecisionLogTable({ decisions }: DecisionLogTableProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  function toggleRow(id: string) {
    setExpandedId((prev) => (prev === id ? null : id));
  }

  function formatDate(dateStr: string): string {
    try {
      return format(new Date(dateStr), 'd MMM yyyy', { locale: nl });
    } catch {
      return dateStr;
    }
  }

  function truncate(text: string, max: number): string {
    if (text.length <= max) return text;
    return text.slice(0, max) + '...';
  }

  if (decisions.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-neutral-500">
        Nog geen besluiten vastgelegd.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-neutral-200 text-left">
            <th className="pb-3 pr-4 font-medium text-neutral-600">Nummer</th>
            <th className="pb-3 pr-4 font-medium text-neutral-600">Type</th>
            <th className="pb-3 pr-4 font-medium text-neutral-600">Inhoud</th>
            <th className="pb-3 pr-4 font-medium text-neutral-600">Gremium</th>
            <th className="pb-3 pr-4 font-medium text-neutral-600">Besloten door</th>
            <th className="pb-3 font-medium text-neutral-600">Datum</th>
          </tr>
        </thead>
        <tbody>
          {decisions.map((decision) => {
            const isExpanded = expandedId === decision.id;
            const isSuperseded = !!decision.supersedes_id;

            return (
              <Fragment key={decision.id}>
                <tr
                  className="border-b border-neutral-100 cursor-pointer hover:bg-neutral-50 transition-colors"
                  onClick={() => toggleRow(decision.id)}
                >
                  <td className={`py-3 pr-4 font-mono text-xs ${isSuperseded ? 'line-through text-neutral-400' : 'text-neutral-800'}`}>
                    {decision.number}
                  </td>
                  <td className="py-3 pr-4">
                    <Badge variant={DECISION_TYPE_VARIANT[decision.decision_type] || 'default'}>
                      {decision.decision_type}
                    </Badge>
                  </td>
                  <td className={`py-3 pr-4 ${isSuperseded ? 'line-through text-neutral-400' : 'text-neutral-800'}`}>
                    {truncate(decision.content, 100)}
                  </td>
                  <td className="py-3 pr-4 text-neutral-600">
                    {decision.gremium}
                  </td>
                  <td className="py-3 pr-4 text-neutral-600">
                    {decision.decided_by_name}
                  </td>
                  <td className="py-3 text-neutral-600 whitespace-nowrap">
                    {formatDate(decision.decided_at)}
                  </td>
                </tr>

                {isExpanded && (
                  <tr>
                    <td colSpan={6} className="px-4 py-4 bg-neutral-50">
                      <div className="space-y-3 text-sm">
                        <div>
                          <span className="font-medium text-neutral-600">Volledige inhoud: </span>
                          <span className="text-neutral-800">{decision.content}</span>
                        </div>
                        {decision.grondslag && (
                          <div>
                            <span className="font-medium text-neutral-600">Grondslag: </span>
                            <span className="text-neutral-800">{decision.grondslag}</span>
                          </div>
                        )}
                        {decision.motivation && (
                          <div>
                            <span className="font-medium text-neutral-600">Motivatie: </span>
                            <span className="text-neutral-800">{decision.motivation}</span>
                          </div>
                        )}
                        {decision.alternatives && (
                          <div>
                            <span className="font-medium text-neutral-600">Alternatieven overwogen: </span>
                            <span className="text-neutral-800">{decision.alternatives}</span>
                          </div>
                        )}
                        {decision.iso_clause && (
                          <div>
                            <span className="font-medium text-neutral-600">ISO-clausule: </span>
                            <span className="text-neutral-800">{decision.iso_clause}</span>
                          </div>
                        )}
                        {decision.valid_until && (
                          <div>
                            <span className="font-medium text-neutral-600">Geldig tot: </span>
                            <span className="text-neutral-800">{decision.valid_until}</span>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
