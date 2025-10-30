import {IntegrationSummary} from "../../shared/api/integrationProgress";
import {RunIntegrationButton} from "./RunIntegrationButton";

export interface IntegrationListProps {
  integrations: IntegrationSummary[];
  onRun: (name: string) => void;
  disabled?: boolean;
  runningIntegration?: string | null;
}

export function IntegrationList({
  integrations,
  onRun,
  disabled = false,
  runningIntegration,
}: IntegrationListProps) {
  if (integrations.length === 0) {
    return <p role="status">Нет доступных интеграций.</p>;
  }

  return (
    <ul aria-label="Список интеграций">
      {integrations.map((integration) => {
        const isRunning = runningIntegration === integration.name;
        return (
          <li key={integration.name} style={{marginBottom: "1rem"}}>
            <div style={{display: "flex", flexDirection: "column", gap: "0.25rem"}}>
              <span style={{fontWeight: 600}}>{integration.name}</span>
              {integration.description ? (
                <span style={{color: "#555"}}>{integration.description}</span>
              ) : null}
              <RunIntegrationButton
                integration={integration}
                onRun={onRun}
                disabled={disabled}
                running={isRunning}
              />
            </div>
          </li>
        );
      })}
    </ul>
  );
}

