import {IntegrationList} from "./IntegrationList";
import {IntegrationStatusPanel} from "./IntegrationStatusPanel";
import {useIntegrationProgress} from "./useIntegrationProgress";

export interface IntegrationProgressDashboardProps {
  pollInterval?: number;
}

export function IntegrationProgressDashboard({
  pollInterval,
}: IntegrationProgressDashboardProps) {
  const {
    integrations,
    isLoadingIntegrations,
    loadError,
    refresh,
    runIntegration,
    isEnqueuing,
    currentIntegration,
    currentTask,
    isPolling,
    pollingError,
  } = useIntegrationProgress({pollInterval});

  return (
    <div style={{display: "grid", gap: "1.5rem"}}>
      <header>
        <h1>Мониторинг интеграций</h1>
        <p>Запускайте интеграции вручную и отслеживайте их выполнение в реальном времени.</p>
        <button type="button" onClick={() => refresh()} disabled={isLoadingIntegrations}>
          Обновить список
        </button>
      </header>

      <section>
        <h2>Доступные интеграции</h2>
        {isLoadingIntegrations ? <p role="status">Загрузка списка интеграций...</p> : null}
        {loadError ? (
          <p role="alert" style={{color: "#b30000"}}>
            Ошибка: {loadError}
          </p>
        ) : null}
        {!isLoadingIntegrations && !loadError ? (
          <IntegrationList
            integrations={integrations}
            onRun={runIntegration}
            disabled={isEnqueuing}
            runningIntegration={currentIntegration}
          />
        ) : null}
      </section>

      <IntegrationStatusPanel
        integrationName={currentIntegration}
        task={currentTask}
        isPolling={isPolling}
        error={pollingError}
      />
    </div>
  );
}

export default IntegrationProgressDashboard;

