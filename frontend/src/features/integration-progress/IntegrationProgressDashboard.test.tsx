import {render, screen, waitFor} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {afterEach, beforeEach, describe, expect, it, vi} from "vitest";
import {IntegrationProgressDashboard} from "./IntegrationProgressDashboard";

const API_BASE = "/api";

describe("IntegrationProgressDashboard", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  it("loads integrations and polls task status", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify([
            {name: "crm_sync", description: "CRM"},
            {name: "notifications", description: "Notifications"},
          ]),
          {status: 200},
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({task_id: "task-1"}), {status: 200}),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({id: "task-1", state: "running"}), {
          status: 200,
        }),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            id: "task-1",
            state: "completed",
            status: "done",
            result: {ok: true},
          }),
          {status: 200},
        ),
      );

    render(<IntegrationProgressDashboard pollInterval={1000} />);

    await waitFor(() => {
      expect(
        screen.getByRole("button", {name: "Запустить crm_sync"}),
      ).toBeInTheDocument();
    });

    await userEvent.click(
      screen.getByRole("button", {name: "Запустить crm_sync"}),
    );

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        `${API_BASE}/integrations/crm_sync/enqueue`,
        expect.objectContaining({method: "POST"}),
      );
    });

    await waitFor(() => {
      expect(
        screen.getByRole("button", {name: "Выполняется crm_sync..."}),
      ).toBeDisabled();
    });

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        `${API_BASE}/integrations/tasks/task-1`,
        expect.anything(),
      );
    });

    vi.advanceTimersByTime(1000);

    await waitFor(() => {
      expect(screen.getByText(/Состояние:/)).toHaveTextContent("completed");
      expect(screen.getByText(/Сообщение:/)).toHaveTextContent("done");
    });
  });

  it("отображает ошибку загрузки", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new Error("Network"));

    render(<IntegrationProgressDashboard />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Network");
    });
  });
});

