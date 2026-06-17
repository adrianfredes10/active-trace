import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { GrillaSalarialPanel } from "@/features/finanzas/components/GrillaSalarialPanel";

const guardarSalarioBase = vi.fn().mockResolvedValue({
  id: "g1",
  rol: "PROFESOR",
  monto: "150000",
  vig_desde: "2026-06-01",
  vig_hasta: null,
});

vi.mock("@/features/finanzas/services/liquidacionService", () => ({
  fetchGrillaSalarial: vi.fn().mockResolvedValue([
    { id: "g0", rol: "TUTOR", monto: "80000", vig_desde: "2026-01-01", vig_hasta: null },
  ]),
  guardarSalarioBase: (...args: unknown[]) => guardarSalarioBase(...args),
  fetchLiquidaciones: vi.fn(),
  fetchLiquidacionKpis: vi.fn(),
  cerrarLiquidacion: vi.fn(),
}));

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient();
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("GrillaSalarialPanel", () => {
  it("guarda salario base", async () => {
    const user = userEvent.setup();
    renderWithQuery(<GrillaSalarialPanel />);

    await waitFor(() => {
      expect(screen.getByText("TUTOR")).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText(/monto/i), "150000");
    await user.click(screen.getByRole("button", { name: /guardar/i }));

    expect(guardarSalarioBase).toHaveBeenCalled();
  });
});
