'use client';

import { useState, use } from 'react';
import { useRouter } from 'next/navigation';
import useSWR from 'swr';
import {
  ArrowLeftIcon,
  CheckCircleIcon,
  LockClosedIcon,
  ArrowUpTrayIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';
import { PageWrapper } from '@/components/layout/page-wrapper';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { StatusBadge } from '@/components/shared/status-badge';
import { WaaromTooltip } from '@/components/shared/waarom-tooltip';
import { CardSkeleton } from '@/components/ui/loading-skeleton';
import { api, apiFetch, ApiError } from '@/lib/api-client';
import { STEP_CONFIGS } from '@/lib/step-config';
import type {
  StepResponse,
  StepExecutionResponse,
  StepDependencyResponse,
  DecisionResponse,
  DocumentResponse,
} from '@/lib/api-types';

// --- Status transition labels (direct buttons, no dropdown) ---
const STATUS_ACTIONS: Record<
  string,
  { target: string; label: string; variant: 'primary' | 'secondary' | 'danger' }[]
> = {
  niet_gestart: [
    { target: 'in_uitvoering', label: 'Start deze stap', variant: 'primary' },
  ],
  in_uitvoering: [
    { target: 'concept', label: 'Markeer als concept', variant: 'primary' },
  ],
  concept: [
    { target: 'in_review', label: 'Indienen voor review', variant: 'primary' },
  ],
  in_review: [
    { target: 'vastgesteld', label: 'Goedkeuren', variant: 'primary' },
    { target: 'concept', label: 'Terugsturen', variant: 'secondary' },
  ],
  vastgesteld: [],
};

// --- What's needed before transitioning (stok achter de deur) ---
interface GateCheck {
  passed: boolean;
  message: string;
}

function checkGates(
  currentStatus: string,
  targetStatus: string,
  decisions: DecisionResponse[],
  documents: DocumentResponse[],
  stepId: string,
): GateCheck {
  // Starting a step is always allowed
  if (currentStatus === 'niet_gestart' && targetStatus === 'in_uitvoering') {
    return { passed: true, message: '' };
  }

  // in_uitvoering → concept: must have at least 1 decision or document linked to this step
  if (currentStatus === 'in_uitvoering' && targetStatus === 'concept') {
    const hasOutput =
      decisions.some((d) => d.step_execution_id === stepId) ||
      documents.some((d) => d.step_execution_id === stepId);
    if (!hasOutput) {
      return {
        passed: false,
        message:
          'Voeg eerst een besluit of document toe voordat je deze stap als concept markeert.',
      };
    }
  }

  // concept → in_review: same check (at least 1 output)
  if (currentStatus === 'concept' && targetStatus === 'in_review') {
    const hasOutput =
      decisions.some((d) => d.step_execution_id === stepId) ||
      documents.some((d) => d.step_execution_id === stepId);
    if (!hasOutput) {
      return {
        passed: false,
        message:
          'Er moet minimaal een besluit of document aan deze stap gekoppeld zijn.',
      };
    }
  }

  // in_review → vastgesteld: must have a decision in the besluitlog for this step
  if (currentStatus === 'in_review' && targetStatus === 'vastgesteld') {
    const hasDecision = decisions.some((d) => d.step_execution_id === stepId);
    if (!hasDecision) {
      return {
        passed: false,
        message:
          'Er moet een besluit in de besluitlog staan voordat deze stap vastgesteld kan worden.',
      };
    }
  }

  return { passed: true, message: '' };
}

export default function StepDetailPage({
  params,
}: {
  params: Promise<{ stepId: string }>;
}) {
  const { stepId } = use(params);
  const router = useRouter();
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [uploadFile, setUploadFile] = useState('');
  const [uploadType, setUploadType] = useState('pdf');

  const { data: step, isLoading: stepLoading } = useSWR<StepResponse>(
    `/steps/${stepId}`,
    () => api.steps.get(stepId),
  );

  const {
    data: allExecutions,
    isLoading: execLoading,
    mutate: mutateExecutions,
  } = useSWR<StepExecutionResponse[]>('/steps/executions/', () =>
    api.steps.listExecutions(),
  );

  const { data: dependencies } = useSWR<StepDependencyResponse[]>(
    '/steps/dependencies/',
    () => api.steps.listDependencies(),
  );

  // Fetch decisions and documents linked to this step (for gate checks)
  const { data: decisions = [] } = useSWR<DecisionResponse[]>(
    '/decisions/',
    () => api.decisions.list(),
  );

  const { data: documents = [] } = useSWR<DocumentResponse[]>(
    '/documents/',
    () => api.documents.list(),
  );

  const execution = allExecutions?.find((e) => e.step_id === stepId);
  const currentStatus = execution?.status || 'niet_gestart';
  const isCompleted = currentStatus === 'vastgesteld';
  const executionId = execution?.id;

  const stepConfig = step ? STEP_CONFIGS[step.number] || null : null;

  // Check if dependencies are met
  const stepDeps = dependencies?.filter((d) => d.step_id === stepId) || [];
  const blockingDeps = stepDeps.filter((dep) => {
    if (dep.dependency_type !== 'B') return false;
    const depExec = allExecutions?.find(
      (e) => e.step_id === dep.depends_on_step_id,
    );
    return !depExec || depExec.status !== 'vastgesteld';
  });
  const isBlocked = blockingDeps.length > 0;

  const actions = STATUS_ACTIONS[currentStatus] || [];

  // Count linked outputs
  const linkedDecisions = decisions.filter(
    (d) => d.step_execution_id === executionId,
  );
  const linkedDocuments = documents.filter(
    (d) => d.step_execution_id === executionId,
  );
  const outputCount = linkedDecisions.length + linkedDocuments.length;

  async function handleTransition(targetStatus: string) {
    // Gate check
    const gate = checkGates(
      currentStatus,
      targetStatus,
      decisions,
      documents,
      executionId || '',
    );
    if (!gate.passed) {
      setError(gate.message);
      return;
    }

    setIsUpdating(true);
    setError(null);

    try {
      if (!execution) {
        const created = await api.steps.createExecution({
          step_id: stepId,
          status: 'niet_gestart',
        });
        if (targetStatus !== 'niet_gestart') {
          await api.steps.updateExecution(created.id, {
            status: targetStatus,
          });
        }
      } else {
        await api.steps.updateExecution(execution.id, {
          status: targetStatus,
        });
      }
      await mutateExecutions();
    } catch (err) {
      if (err instanceof ApiError) {
        const detail =
          (err.body as Record<string, unknown>)?.detail ||
          JSON.stringify(err.body);
        setError(`Fout: ${detail}`);
      } else {
        setError(
          `Fout: ${err instanceof Error ? err.message : String(err)}`,
        );
      }
    } finally {
      setIsUpdating(false);
    }
  }

  async function handleUpload() {
    if (!uploadFile.trim() || !executionId) return;
    setIsUpdating(true);
    setError(null);
    try {
      await apiFetch('/documents/input-documents/', {
        method: 'POST',
        body: JSON.stringify({
          step_execution_id: executionId,
          source_type: uploadType,
          storage_path: uploadFile.trim(),
          status: 'pending',
          uploaded_at: new Date().toISOString(),
        }),
      });
      setShowUpload(false);
      setUploadFile('');
    } catch (err) {
      if (err instanceof ApiError) {
        const detail =
          (err.body as Record<string, unknown>)?.detail ||
          JSON.stringify(err.body);
        setError(`Upload fout: ${detail}`);
      } else {
        setError(`Upload fout: ${err instanceof Error ? err.message : String(err)}`);
      }
    } finally {
      setIsUpdating(false);
    }
  }

  if (stepLoading || execLoading) {
    return (
      <PageWrapper title="Stap laden...">
        <CardSkeleton />
      </PageWrapper>
    );
  }

  if (!step) {
    return (
      <PageWrapper title="Stap niet gevonden">
        <Card>
          <p className="text-sm text-neutral-600">
            De gevraagde stap kon niet worden gevonden.
          </p>
          <Button
            variant="secondary"
            size="sm"
            className="mt-4"
            onClick={() => router.push('/inrichten')}
          >
            Terug naar overzicht
          </Button>
        </Card>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper
      title={`Stap ${step.number} -- ${step.name}`}
      actions={
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/inrichten')}
        >
          <ArrowLeftIcon className="mr-1.5 h-4 w-4" />
          Overzicht
        </Button>
      }
    >
      <div className="flex flex-col gap-6 lg:flex-row">
        {/* Left sidebar -- step metadata */}
        <div className="w-full lg:w-[300px] flex-shrink-0 space-y-4">
          <Card>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary-50 text-xl font-bold text-primary-700">
                  {step.number}
                </div>
                <div>
                  <p className="text-xs text-neutral-500">Fase {step.phase}</p>
                  <h2 className="text-sm font-semibold text-neutral-900">
                    {step.name}
                  </h2>
                </div>
              </div>

              <div className="space-y-3 pt-2 border-t border-neutral-100">
                <div>
                  <p className="text-xs text-neutral-500 mb-1">Status</p>
                  <StatusBadge status={currentStatus} />
                </div>

                <div>
                  <p className="text-xs text-neutral-500 mb-1">Gremium</p>
                  <Badge variant="neutral">{step.required_gremium}</Badge>
                </div>

                {step.domain && (
                  <div>
                    <p className="text-xs text-neutral-500 mb-1">Domein</p>
                    <Badge variant="primary">{step.domain}</Badge>
                  </div>
                )}

                {step.is_optional && (
                  <Badge variant="default">Optioneel</Badge>
                )}

                {isBlocked && (
                  <div className="flex items-center gap-2 rounded-md bg-yellow-50 px-3 py-2 text-xs text-yellow-800">
                    <LockClosedIcon className="h-4 w-4" />
                    <span>Blokkerende afhankelijkheden niet voldaan</span>
                  </div>
                )}
              </div>

              {step.waarom_nu && (
                <div className="pt-2 border-t border-neutral-100">
                  <div className="flex items-center gap-1 mb-1">
                    <p className="text-xs text-neutral-500">Waarom nu</p>
                    <WaaromTooltip text={step.waarom_nu} />
                  </div>
                  <p className="text-xs text-neutral-600 leading-relaxed">
                    {step.waarom_nu}
                  </p>
                </div>
              )}

              {stepConfig && stepConfig.outputs.length > 0 && (
                <div className="pt-2 border-t border-neutral-100">
                  <p className="text-xs text-neutral-500 mb-2">
                    Verwachte outputs
                  </p>
                  <ul className="space-y-1">
                    {stepConfig.outputs.map((output) => (
                      <li
                        key={output}
                        className="text-xs text-neutral-600 flex items-start gap-1.5"
                      >
                        <span className="mt-1 h-1 w-1 rounded-full bg-neutral-400 flex-shrink-0" />
                        {output}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </Card>

          {/* Linked outputs count */}
          {execution && (
            <Card>
              <p className="text-xs text-neutral-500 mb-2">
                Gekoppelde outputs
              </p>
              <div className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-neutral-600">Besluiten</span>
                  <Badge variant={linkedDecisions.length > 0 ? 'success' : 'neutral'}>
                    {linkedDecisions.length}
                  </Badge>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-neutral-600">Documenten</span>
                  <Badge variant={linkedDocuments.length > 0 ? 'success' : 'neutral'}>
                    {linkedDocuments.length}
                  </Badge>
                </div>
              </div>
            </Card>
          )}
        </div>

        {/* Right main area */}
        <div className="flex-1 min-w-0 space-y-4">
          {/* Completed banner */}
          {isCompleted && (
            <div className="flex items-center gap-2 rounded-lg bg-green-50 border border-green-200 px-4 py-3">
              <CheckCircleIcon className="h-5 w-5 text-green-600" />
              <span className="text-sm font-medium text-green-800">
                Deze stap is vastgesteld
              </span>
            </div>
          )}

          {/* Step description */}
          <Card>
            {stepConfig && (
              <div>
                <h3 className="text-base font-semibold text-neutral-900 mb-2">
                  {stepConfig.title}
                </h3>
                <p className="text-sm text-neutral-600 leading-relaxed">
                  {stepConfig.description}
                </p>
              </div>
            )}
          </Card>

          {/* Action buttons (direct, no dropdown) */}
          {!isCompleted && !isBlocked && actions.length > 0 && (
            <Card>
              <div className="space-y-3">
                <h4 className="text-sm font-medium text-neutral-800">
                  Acties
                </h4>

                {/* Gate warning */}
                {currentStatus !== 'niet_gestart' && outputCount === 0 && (
                  <div className="rounded-md bg-amber-50 border border-amber-200 px-3 py-2 text-xs text-amber-800">
                    Voeg eerst een besluit of document toe aan deze stap
                    voordat je verder kunt.
                  </div>
                )}

                <div className="flex flex-wrap gap-2">
                  {actions.map((action) => (
                    <Button
                      key={action.target}
                      variant={action.variant}
                      size="md"
                      disabled={isUpdating}
                      onClick={() => handleTransition(action.target)}
                    >
                      {isUpdating ? 'Bezig...' : action.label}
                    </Button>
                  ))}
                </div>

                {error && (
                  <div className="rounded-md bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
                    {error}
                  </div>
                )}
              </div>
            </Card>
          )}

          {/* Document upload (secundaire invoerroute K6) */}
          {execution && !isCompleted && (
            <Card>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-medium text-neutral-800">
                    Document uploaden
                  </h4>
                  {!showUpload && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setShowUpload(true)}
                    >
                      <ArrowUpTrayIcon className="mr-1.5 h-4 w-4" />
                      Upload
                    </Button>
                  )}
                </div>

                <p className="text-xs text-neutral-500">
                  Upload een bestaand document (PDF, Word, Markdown) als input
                  voor deze stap. Het document wordt geanalyseerd door een
                  AI-agent.
                </p>

                {showUpload && (
                  <div className="space-y-3 pt-2 border-t border-neutral-100">
                    <Select
                      label="Documenttype"
                      value={uploadType}
                      onChange={(e) => setUploadType(e.target.value)}
                      options={[
                        { value: 'pdf', label: 'PDF' },
                        { value: 'docx', label: 'Word (docx)' },
                        { value: 'markdown', label: 'Markdown' },
                      ]}
                    />
                    <Input
                      label="Bestandspad of URL"
                      placeholder="bijv. /docs/beleidsdocument-isms.pdf"
                      value={uploadFile}
                      onChange={(e) => setUploadFile(e.target.value)}
                    />
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        disabled={!uploadFile.trim() || isUpdating}
                        onClick={handleUpload}
                      >
                        {isUpdating ? 'Bezig...' : 'Uploaden'}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setShowUpload(false);
                          setUploadFile('');
                        }}
                      >
                        Annuleren
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </Card>
          )}

          {/* Blocked message */}
          {isBlocked && !isCompleted && (
            <Card>
              <div className="flex items-center gap-2 text-sm text-neutral-500">
                <LockClosedIcon className="h-4 w-4" />
                <span>
                  Deze stap kan pas worden gestart nadat alle blokkerende
                  afhankelijkheden zijn vastgesteld.
                </span>
              </div>
            </Card>
          )}

          {/* Completed read-only */}
          {isCompleted && (
            <Card>
              <div className="flex items-center gap-2 text-sm text-neutral-500">
                <DocumentTextIcon className="h-4 w-4" />
                <span>
                  Deze stap is afgerond. Bekijk de gekoppelde besluiten en
                  documenten in het besluitlog en de documentenviewer.
                </span>
              </div>
            </Card>
          )}
        </div>
      </div>
    </PageWrapper>
  );
}
