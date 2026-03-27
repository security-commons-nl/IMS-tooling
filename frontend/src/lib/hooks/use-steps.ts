import { useApi } from './use-api';
import type {
  StepResponse,
  StepExecutionResponse,
  StepDependencyResponse,
} from '@/lib/api-types';

export function useSteps() {
  return useApi<StepResponse[]>('/steps/', '/steps/');
}

export function useStepExecutions() {
  return useApi<StepExecutionResponse[]>(
    '/steps/executions/',
    '/steps/executions/',
  );
}

export function useStepDependencies() {
  return useApi<StepDependencyResponse[]>(
    '/steps/dependencies/',
    '/steps/dependencies/',
  );
}
