import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AtrasadosTable } from "@/features/comision/components/AtrasadosTable";

const mockContexto = {
  asignacion_id: "a1",
  materia_id: "m1",
  cohorte_id: "c1",
  comision: "A",
};

vi.mock("@/features/comision/hooks/ComisionProvider", () => ({
  useComisionContext: () => ({
    contexto: mockContexto,
    equipos: [],
    isLoading: false,
    selected: null,
    setSelectedId: vi.fn(),
  }),
}));

vi.mock("@/features/comision/services/analisisService", () => ({
  fetchAtrasados: vi.fn().mockResolvedValue({
    total_alumnos: 2,
    total_atrasados: 1,
    items: [
      {
        entrada_padron_id: "e1",
        email: "alumno@test.com",
        nombre: "Ana",
        apellidos: "García",
        comision: "A",
        motivos: ["TP1"],
      },
    ],
  }),
}));

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("AtrasadosTable", () => {
  it("muestra filas de alumnos atrasados", async () => {
    renderWithQuery(<AtrasadosTable />);

    await waitFor(() => {
      expect(screen.getByText(/García, Ana/)).toBeInTheDocument();
    });
    expect(screen.getByText("alumno@test.com")).toBeInTheDocument();
    expect(screen.getByText("TP1")).toBeInTheDocument();
  });
});
