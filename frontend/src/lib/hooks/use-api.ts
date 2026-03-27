import useSWR from 'swr';
import { apiFetch } from '@/lib/api-client';

export function useApi<T>(key: string | null, path?: string) {
  return useSWR<T>(key, () => apiFetch<T>(path || key!));
}
