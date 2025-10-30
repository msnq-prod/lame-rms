import {IntegrationSummary} from "../../shared/api/integrationProgress";

export interface RunIntegrationButtonProps {
  integration: IntegrationSummary;
  onRun: (name: string) => void;
  disabled?: boolean;
  running?: boolean;
}

export function RunIntegrationButton({
  integration,
  onRun,
  disabled = false,
  running = false,
}: RunIntegrationButtonProps) {
  const label = running
    ? `Выполняется ${integration.name}...`
    : `Запустить ${integration.name}`;
  return (
    <button
      type="button"
      onClick={() => onRun(integration.name)}
      disabled={disabled || running}
      aria-live="polite"
    >
      {label}
    </button>
  );
}

