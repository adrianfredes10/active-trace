import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ComunicacionAtrasadosPanel } from "@/features/comision/components/ComunicacionAtrasadosPanel";

vi.mock("@/features/comision/hooks/ComisionProvider", () => ({
  useComisionContext: () => ({
    contexto: { asignacion_id: "a1", materia_id: "m1", cohorte_id: "c1" },
    equipos: [],
    isLoading: false,
    selected: null,
    setSelectedId: vi.fn(),
  }),
}));

vi.mock("@/features/comision/services/analisisService", () => ({
  fetchAtrasados: vi.fn().mockResolvedValue({
    total_alumnos: 1,
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

const previewComunicacion = vi.fn().mockResolvedValue({
  asunto: "Recordatorio",
  cuerpo: "Hola Ana",
});

vi.mock("@/features/comision/services/comunicacionService", () => ({
  previewComunicacion: (...args: unknown[]) => previewComunicacion(...args),
  enviarComunicacion: vi.fn(),
  fetchLote: vi.fn(),
}));

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("ComunicacionAtrasadosPanel", () => {
  it("muestra preview de comunicación", async () => {
    const user = userEvent.setup();
    renderWithQuery(<ComunicacionAtrasadosPanel />);

    await waitFor(() => {
      expect(screen.getByText(/1 alumno/i)).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /preview/i }));

    expect(previewComunicacion).toHaveBeenCalled();
    expect(await screen.findByText(/Hola Ana/)).toBeInTheDocument();
  });
});
