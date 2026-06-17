import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { MonitorGeneralPanel } from "@/features/coordinacion/components/MonitorGeneralPanel";

vi.mock("@/features/coordinacion/hooks/CoordinacionProvider", () => ({
  useCoordinacionContext: () => ({
    contexto: {
      asignacion_id: "a1",
      materia_id: "m1",
      cohorte_id: "c1",
      carrera_id: "ca1",
    },
    equipos: [],
    isLoading: false,
    selected: null,
    setSelectedId: vi.fn(),
  }),
}));

const fetchMonitorGeneral = vi.fn().mockResolvedValue([
  {
    entrada_padron_id: "e1",
    email: "a@test.com",
    nombre: "Ana",
    apellidos: "García",
    comision: "A",
    regional: null,
    aprobadas: 2,
    total_actividades: 5,
    atrasado: true,
  },
]);

vi.mock("@/features/coordinacion/services/monitorService", () => ({
  fetchMonitorGeneral: (...args: unknown[]) => fetchMonitorGeneral(...args),
}));

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("MonitorGeneralPanel", () => {
  it("aplica filtro solo atrasados", async () => {
    const user = userEvent.setup();
    renderWithQuery(<MonitorGeneralPanel />);

    await waitFor(() => {
      expect(screen.getByText(/García, Ana/)).toBeInTheDocument();
    });

    await user.click(screen.getByLabelText(/solo atrasados/i));
    await user.click(screen.getByRole("button", { name: /aplicar filtros/i }));

    await waitFor(() => {
      expect(fetchMonitorGeneral).toHaveBeenCalledWith(
        expect.objectContaining({ solo_atrasados: true }),
      );
    });
  });
});
