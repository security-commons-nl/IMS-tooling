'use client';

import type { RiskResponse } from '@/lib/api-types';

const CELL_COLORS: Record<string, string> = {
  low: 'bg-green-100 hover:bg-green-200',
  medium: 'bg-yellow-100 hover:bg-yellow-200',
  high: 'bg-orange-100 hover:bg-orange-200',
  critical: 'bg-red-100 hover:bg-red-200',
};

const CELL_COLORS_STATIC: Record<string, string> = {
  low: 'bg-green-100',
  medium: 'bg-yellow-100',
  high: 'bg-orange-100',
  critical: 'bg-red-100',
};

function getLevel(score: number): string {
  if (score <= 4) return 'low';
  if (score <= 9) return 'medium';
  if (score <= 14) return 'high';
  return 'critical';
}

const AXIS_LABELS: Record<number, string> = {
  1: 'Zeer laag',
  2: 'Laag',
  3: 'Midden',
  4: 'Hoog',
  5: 'Zeer hoog',
};

// --- Select mode ---

interface RiskMatrixSelectProps {
  mode: 'select';
  value: { likelihood: number | ''; impact: number | '' };
  onChange: (likelihood: number, impact: number) => void;
}

// --- View mode ---

interface RiskMatrixViewProps {
  mode: 'view';
  risks: RiskResponse[];
}

type RiskMatrixProps = RiskMatrixSelectProps | RiskMatrixViewProps;

export function RiskMatrix(props: RiskMatrixProps) {
  const isSelect = props.mode === 'select';

  // Build lookup: cel (likelihood, impact) → aantal/titels
  const riskMap: Record<string, RiskResponse[]> = {};
  if (!isSelect) {
    for (const risk of (props as RiskMatrixViewProps).risks) {
      const key = `${risk.likelihood}-${risk.impact}`;
      if (!riskMap[key]) riskMap[key] = [];
      riskMap[key].push(risk);
    }
  }

  return (
    <div className="inline-block">
      <div className="flex items-end gap-1">
        {/* Y-as label */}
        <div className="flex flex-col items-center justify-center" style={{ width: 20, height: 5 * 36 + 4 * 4 }}>
          <span
            className="text-xs text-neutral-500 font-medium whitespace-nowrap"
            style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}
          >
            Kans →
          </span>
        </div>

        <div className="flex flex-col gap-1">
          {/* Grid rijen: kans 5 (boven) → 1 (onder) */}
          {[5, 4, 3, 2, 1].map((likelihood) => (
            <div key={likelihood} className="flex items-center gap-1">
              {/* Y-as label */}
              <div className="w-12 text-right">
                <span className="text-xs text-neutral-400">{likelihood}</span>
              </div>

              {/* Cellen: impact 1 → 5 */}
              {[1, 2, 3, 4, 5].map((impact) => {
                const score = likelihood * impact;
                const level = getLevel(score);
                const key = `${likelihood}-${impact}`;

                if (isSelect) {
                  const { value, onChange } = props as RiskMatrixSelectProps;
                  const isSelected = value.likelihood === likelihood && value.impact === impact;
                  return (
                    <button
                      key={key}
                      type="button"
                      title={`Kans: ${AXIS_LABELS[likelihood]}, Impact: ${AXIS_LABELS[impact]} — Score: ${score}`}
                      onClick={() => onChange(likelihood, impact)}
                      className={`
                        w-9 h-9 rounded flex items-center justify-center text-xs font-medium transition-all
                        ${CELL_COLORS[level]}
                        ${isSelected
                          ? 'ring-2 ring-offset-1 ring-neutral-700 text-neutral-800'
                          : 'text-neutral-400'}
                      `}
                    >
                      {isSelected ? (
                        <svg className="w-4 h-4 text-neutral-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <span>{score}</span>
                      )}
                    </button>
                  );
                } else {
                  const risksInCell = riskMap[key] || [];
                  const count = risksInCell.length;
                  const tooltipText = count > 0
                    ? risksInCell.map((r) => r.title).join('\n')
                    : `Kans: ${AXIS_LABELS[likelihood]}, Impact: ${AXIS_LABELS[impact]}`;
                  return (
                    <div
                      key={key}
                      title={tooltipText}
                      className={`w-9 h-9 rounded flex items-center justify-center text-xs font-medium ${CELL_COLORS_STATIC[level]}`}
                    >
                      {count > 0 ? (
                        <span className="text-neutral-700 font-semibold">{count}</span>
                      ) : (
                        <span className="text-neutral-300">{score}</span>
                      )}
                    </div>
                  );
                }
              })}
            </div>
          ))}

          {/* X-as labels */}
          <div className="flex items-center gap-1 mt-1">
            <div className="w-12" />
            {[1, 2, 3, 4, 5].map((impact) => (
              <div key={impact} className="w-9 text-center">
                <span className="text-xs text-neutral-400">{impact}</span>
              </div>
            ))}
          </div>
          <div className="flex justify-center mt-0.5" style={{ paddingLeft: 52 }}>
            <span className="text-xs text-neutral-500 font-medium">Impact →</span>
          </div>
        </div>
      </div>

      {/* Legenda */}
      <div className="mt-3 flex flex-wrap gap-3">
        {[
          { label: 'Groen (≤4)', color: 'bg-green-100' },
          { label: 'Geel (5–9)', color: 'bg-yellow-100' },
          { label: 'Oranje (10–14)', color: 'bg-orange-100' },
          { label: 'Rood (≥15)', color: 'bg-red-100' },
        ].map(({ label, color }) => (
          <div key={label} className="flex items-center gap-1.5">
            <div className={`w-3 h-3 rounded ${color}`} />
            <span className="text-xs text-neutral-500">{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
