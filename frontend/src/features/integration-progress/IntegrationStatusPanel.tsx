import {IntegrationTaskStatus} from "../../shared/api/integrationProgress";

export interface IntegrationStatusPanelProps {
  integrationName: string | null;
  task: IntegrationTaskStatus | null;
  isPolling: boolean;
  error: string | null;
}

export function IntegrationStatusPanel({
  integrationName,
  task,
  isPolling,
  error,
}: IntegrationStatusPanelProps) {
  if (!integrationName && !task) {
    return (
      <section aria-live="polite">
        <h2>Статус задачи</h2>
        <p>Задача ещё не запускалась.</p>
      </section>
    );
  }

  return (
    <section aria-live="polite">
      <h2>Статус задачи</h2>
      {integrationName ? <p>Интеграция: {integrationName}</p> : null}
      {task ? (
        <>
          <p>
            Состояние: <strong>{task.state ?? "неизвестно"}</strong>
          </p>
          {task.status ? <p>Сообщение: {task.status}</p> : null}
          {task.result ? (
            <details>
              <summary>Результат</summary>
              <pre style={{whiteSpace: "pre-wrap"}}>{JSON.stringify(task.result, null, 2)}</pre>
            </details>
          ) : null}
        </>
      ) : (
        <p>Ожидание ответа от сервиса.</p>
      )}
      {isPolling ? <p role="status">Обновление статуса...</p> : null}
      {error ? (
        <p role="alert" style={{color: "#b30000"}}>
          Ошибка: {error}
        </p>
      ) : null}
    </section>
  );
}

