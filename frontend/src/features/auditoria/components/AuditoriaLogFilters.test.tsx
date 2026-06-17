import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AuditoriaLogFilters } from "@/features/auditoria/components/AuditoriaLogFilters";

const fetchAuditoriaLog = vi.fn().mockResolvedValue({
  limit: 50,
  items: [
    {
      id: "a1",
      fecha_hora: "2026-06-17T12:00:00Z",
      actor_id: "actor-1",
      impersonado_id: null,
      materia_id: "m1",
      accion: "CALIFICACIONES_IMPORTAR",
      detalle: null,
      filas_afectadas: 10,
      ip: null,
    },
  ],
});

vi.mock("@/features/auditoria/services/auditoriaPanelService", () => ({
  fetchAuditoriaLog: (...args: unknown[]) => fetchAuditoriaLog(...args),
  fetchAccionesPorDia: vi.fn(),
  fetchComunicacionesPorDocente: vi.fn(),
  fetchInteracciones: vi.fn(),
}));

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("AuditoriaLogFilters", () => {
  it("aplica filtros al log", async () => {
    const user = userEvent.setup();
    renderWithQuery(<AuditoriaLogFilters />);

    await waitFor(() => {
      expect(screen.getByText("CALIFICACIONES_IMPORTAR")).toBeInTheDocument();
    });

    await user.clear(screen.getByLabelText(/límite/i));
    await user.type(screen.getByLabelText(/límite/i), "50");
    await user.type(screen.getByLabelText(/acción/i), "PADRON");
    await user.click(screen.getByRole("button", { name: /aplicar filtros/i }));

    await waitFor(() => {
      expect(fetchAuditoriaLog).toHaveBeenCalledWith(
        expect.objectContaining({ accion: "PADRON", limit: 50 }),
      );
    });
  });
});
