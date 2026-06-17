import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { EquiposPanel } from "@/features/coordinacion/components/EquiposPanel";

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

vi.mock("@/features/coordinacion/services/equiposCoordService", () => ({
  fetchAsignaciones: vi.fn().mockResolvedValue([
    {
      id: "as1",
      usuario_id: "u1",
      rol: "PROFESOR",
      materia_id: "m1",
      carrera_id: "ca1",
      cohorte_id: "c1",
      comisiones: [],
      vigente: true,
      desde: "2026-03-01",
      hasta: null,
    },
  ]),
  exportarEquipoCsv: vi.fn(),
  clonarEquipo: vi.fn(),
}));

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("EquiposPanel", () => {
  it("lista asignaciones del equipo", async () => {
    renderWithQuery(<EquiposPanel />);

    await waitFor(() => {
      expect(screen.getByText(/PROFESOR/)).toBeInTheDocument();
    });
    expect(screen.getByText("Vigente")).toBeInTheDocument();
  });
});
