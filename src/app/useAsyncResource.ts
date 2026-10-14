import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError } from '@/api/client';

export type ResourcePhase = 'idle' | 'loading' | 'success' | 'error';

export interface AsyncResource<T> {
  data: T | undefined;
  error: ApiError | Error | undefined;
  phase: ResourcePhase;
  isStale: boolean;
  reload: () => Promise<void>;
}

/** Keeps latest response only and cancels superseded reads on unmount/reload. */
export function useAsyncResource<T>(
  loader: (signal: AbortSignal) => Promise<T>,
  dependencies: readonly unknown[],
): AsyncResource<T> {
  const [data, setData] = useState<T>();
  const [error, setError] = useState<ApiError | Error>();
  const [phase, setPhase] = useState<ResourcePhase>('idle');
  const activeController = useRef<AbortController>();

  const reload = useCallback(async () => {
    activeController.current?.abort();
    const controller = new AbortController();
    activeController.current = controller;
    setPhase('loading');
    setError(undefined);
    try {
      const next = await loader(controller.signal);
      if (!controller.signal.aborted) {
        setData(next);
        setPhase('success');
      }
    } catch (nextError) {
      if (!controller.signal.aborted) {
        setError(nextError instanceof Error ? nextError : new Error('请求失败'));
        setPhase('error');
      }
    }
  }, dependencies);

  useEffect(() => {
    void reload();
    return () => activeController.current?.abort();
  }, [reload]);

  return { data, error, phase, isStale: phase === 'loading' && data !== undefined, reload };
}
