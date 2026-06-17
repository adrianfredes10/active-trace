import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ComunicacionTracking } from "@/features/comision/components/ComunicacionTracking";

vi.mock("@/features/comision/services/comunicacionService", () => ({
  fetchLote: vi.fn().mockResolvedValue({
    lote_id: "lote-1",
    total: 2,
    items: [
      {
        id: "c1",
        materia_id: "m1",
        asunto: "Aviso",
        estado: "Pendiente",
        lote_id: "lote-1",
        es_masivo: true,
        aprobado: true,
        enviado_at: null,
      },
      {
        id: "c2",
        materia_id: "m1",
        asunto: "Aviso",
        estado: "Enviado",
        lote_id: "lote-1",
        es_masivo: true,
        aprobado: true,
        enviado_at: "2026-06-17T12:00:00Z",
      },
    ],
  }),
}));

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("ComunicacionTracking", () => {
  it("lista estados del lote", async () => {
    renderWithQuery(<ComunicacionTracking loteId="lote-1" />);

    await waitFor(() => {
      expect(screen.getByText("Pendiente")).toBeInTheDocument();
    });
    expect(screen.getByText("Enviado")).toBeInTheDocument();
  });
});
