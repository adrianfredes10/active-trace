import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AvisoPublicarForm } from "@/features/coordinacion/components/AvisoPublicarForm";

const crearAviso = vi.fn().mockResolvedValue({ id: "av1", titulo: "Test" });

vi.mock("@/features/coordinacion/services/avisoService", () => ({
  crearAviso: (...args: unknown[]) => crearAviso(...args),
}));

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient();
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("AvisoPublicarForm", () => {
  it("publica aviso con título y cuerpo", async () => {
    const user = userEvent.setup();
    const onPublicado = vi.fn();
    renderWithQuery(
      <AvisoPublicarForm
        contexto={{
          asignacion_id: "a1",
          materia_id: "m1",
          cohorte_id: "c1",
          carrera_id: "ca1",
        }}
        onPublicado={onPublicado}
      />,
    );

    await user.click(screen.getByRole("button", { name: /publicar/i }));

    await waitFor(() => {
      expect(crearAviso).toHaveBeenCalled();
    });
    expect(onPublicado).toHaveBeenCalled();
  });
});
