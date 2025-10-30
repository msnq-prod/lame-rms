import {useCallback, useEffect, useMemo, useRef, useState} from "react";
import {
  enqueueIntegration,
  integrationProgress,
  listIntegrations,
  IntegrationSummary,
  IntegrationTaskStatus,
} from "../../shared/api/integrationProgress";

export interface UseIntegrationProgressOptions {
  pollInterval?: number;
}

export interface UseIntegrationProgressResult {
  integrations: IntegrationSummary[];
  isLoadingIntegrations: boolean;
  loadError: string | null;
  refresh: () => Promise<void>;
  runIntegration: (name: string) => Promise<void>;
  isEnqueuing: boolean;
  currentIntegration: string | null;
  currentTask: IntegrationTaskStatus | null;
  isPolling: boolean;
  pollingError: string | null;
}

const DEFAULT_POLL_INTERVAL = 5000;

const TERMINAL_STATES = new Set([
  "completed",
  "failed",
  "cancelled",
  "canceled",
  "succeeded",
  "success",
  "error",
]);

function isTerminal(state: string | undefined | null): boolean {
  if (!state) {
    return false;
  }
  return TERMINAL_STATES.has(state.toLowerCase());
}

export function useIntegrationProgress(
  options: UseIntegrationProgressOptions = {},
): UseIntegrationProgressResult {
  const {pollInterval = DEFAULT_POLL_INTERVAL} = options;
  const [integrations, setIntegrations] = useState<IntegrationSummary[]>([]);
  const [isLoadingIntegrations, setIsLoadingIntegrations] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [isEnqueuing, setIsEnqueuing] = useState(false);
  const [currentIntegration, setCurrentIntegration] = useState<string | null>(null);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [currentTask, setCurrentTask] = useState<IntegrationTaskStatus | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [pollingError, setPollingError] = useState<string | null>(null);

  const pollTimerRef = useRef<number | null>(null);

  const clearPollTimer = useCallback(() => {
    if (pollTimerRef.current !== null) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  const fetchIntegrations = useCallback(async () => {
    setIsLoadingIntegrations(true);
    setLoadError(null);
    try {
      const items = await listIntegrations();
      setIntegrations(items);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setLoadError(message);
    } finally {
      setIsLoadingIntegrations(false);
    }
  }, []);

  const pollTask = useCallback(
    async (taskId: string) => {
      setIsPolling(true);
      setPollingError(null);
      try {
        const status = await integrationProgress(taskId);
        setCurrentTask(status);
        if (isTerminal(status.state)) {
          clearPollTimer();
          setCurrentTaskId(null);
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unknown error";
        setPollingError(message);
        clearPollTimer();
        setCurrentTaskId(null);
      } finally {
        setIsPolling(false);
      }
    },
    [clearPollTimer],
  );

  useEffect(() => {
    fetchIntegrations().catch(() => {
      // error state handled above
    });
    return () => {
      clearPollTimer();
    };
  }, [fetchIntegrations, clearPollTimer]);

  useEffect(() => {
    if (!currentTaskId) {
      return;
    }

    pollTask(currentTaskId).catch(() => {
      // error state handled above
    });

    pollTimerRef.current = window.setInterval(() => {
      pollTask(currentTaskId).catch(() => {
        // error state handled above
      });
    }, pollInterval);

    return () => {
      clearPollTimer();
    };
  }, [currentTaskId, pollInterval, pollTask, clearPollTimer]);

  const runIntegration = useCallback(
    async (name: string) => {
      setIsEnqueuing(true);
      setCurrentIntegration(name);
      setPollingError(null);
      try {
        const {task_id: taskId} = await enqueueIntegration(name);
        setCurrentTask({id: taskId, state: "pending"});
        setCurrentTaskId(taskId);
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unknown error";
        setPollingError(message);
        setCurrentIntegration(null);
      } finally {
        setIsEnqueuing(false);
      }
    },
    [],
  );

  return useMemo(
    () => ({
      integrations,
      isLoadingIntegrations,
      loadError,
      refresh: fetchIntegrations,
      runIntegration,
      isEnqueuing,
      currentIntegration,
      currentTask,
      isPolling,
      pollingError,
    }),
    [
      integrations,
      isLoadingIntegrations,
      loadError,
      fetchIntegrations,
      runIntegration,
      isEnqueuing,
      currentIntegration,
      currentTask,
      isPolling,
      pollingError,
    ],
  );
}

