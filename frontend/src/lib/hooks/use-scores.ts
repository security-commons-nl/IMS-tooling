import { useApi } from './use-api';
import type { SetupScoreResponse } from '@/lib/api-types';

export function useSetupScores() {
  return useApi<SetupScoreResponse[]>(
    '/scores/setup-scores/',
    '/scores/setup-scores/',
  );
}
