import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { LiquidacionesPanel } from "@/features/finanzas/components/LiquidacionesPanel";

const cerrarLiquidacion = vi.fn().mockResolvedValue({ id: "l1", estado: "Cerrada" });

vi.mock("@/features/finanzas/services/liquidacionService", () => ({
  fetchLiquidacionKpis: vi.fn().mockResolvedValue({
    total_general: "100000",
    total_nexo: "20000",
    total_factura: "15000",
    cantidad_abiertas: 1,
  }),
  fetchLiquidaciones: vi.fn().mockResolvedValue([
    {
      id: "l1",
      periodo: "2026-06",
      segmento: "general",
      usuario_id: "u-11111111",
      total: "50000",
      estado: "Abierta",
      es_nexo: false,
      excluido_por_factura: false,
    },
  ]),
  cerrarLiquidacion: (...args: unknown[]) => cerrarLiquidacion(...args),
  fetchGrillaSalarial: vi.fn(),
  guardarSalarioBase: vi.fn(),
}));

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("LiquidacionesPanel", () => {
  it("muestra segmento y permite cerrar liquidación", async () => {
    const user = userEvent.setup();
    renderWithQuery(<LiquidacionesPanel />);

    await waitFor(() => {
      expect(screen.getByText(/Total general/)).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /NEXO/i }));
    await user.click(screen.getByRole("button", { name: /Cerrar/i }));

    expect(cerrarLiquidacion).toHaveBeenCalledWith("l1", expect.anything());
  });
});
