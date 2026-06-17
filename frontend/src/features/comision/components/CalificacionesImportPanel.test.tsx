import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { CalificacionesImportPanel } from "@/features/comision/components/CalificacionesImportPanel";

vi.mock("@/features/comision/hooks/ComisionProvider", () => ({
  useComisionContext: () => ({
    contexto: { asignacion_id: "a1", materia_id: "m1", cohorte_id: "c1" },
    equipos: [],
    isLoading: false,
    selected: null,
    setSelectedId: vi.fn(),
  }),
}));

const previewCalificaciones = vi.fn().mockResolvedValue({
  actividades: [{ nombre: "TP1", tipo: "tp" }],
  total_filas: 10,
  muestra_emails: ["a@test.com"],
});

vi.mock("@/features/comision/services/calificacionService", () => ({
  previewCalificaciones: (...args: unknown[]) => previewCalificaciones(...args),
  importarCalificaciones: vi.fn(),
}));

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient();
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("CalificacionesImportPanel", () => {
  it("ejecuta preview al seleccionar archivo y confirmar", async () => {
    const user = userEvent.setup();
    renderWithQuery(<CalificacionesImportPanel />);

    const input = screen.getByLabelText(/archivo csv/i);
    const file = new File(["email,nota"], "notas.csv", { type: "text/csv" });
    await user.upload(input, file);

    await user.click(screen.getByRole("button", { name: /preview/i }));

    expect(previewCalificaciones).toHaveBeenCalled();
    expect(await screen.findByText(/TP1/)).toBeInTheDocument();
  });
});
