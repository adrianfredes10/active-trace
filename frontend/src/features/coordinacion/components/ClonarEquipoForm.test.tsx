import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ClonarEquipoForm } from "@/features/coordinacion/components/ClonarEquipoForm";

const contexto = {
  asignacion_id: "a1",
  materia_id: "m1",
  carrera_id: "carr1",
  cohorte_id: "coh1",
};

const clonarEquipo = vi.fn().mockResolvedValue({ creadas: 3, actualizadas: 0, items: [] });

vi.mock("@/features/coordinacion/services/equiposCoordService", () => ({
  clonarEquipo: (...args: unknown[]) => clonarEquipo(...args),
}));

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient();
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("ClonarEquipoForm", () => {
  it("envía clonado al submit", async () => {
    const user = userEvent.setup();
    const onClonado = vi.fn();
    renderWithQuery(<ClonarEquipoForm contexto={contexto} onClonado={onClonado} />);

    await user.type(screen.getByLabelText(/cohorte destino/i), "cohorte-dest");
    await user.click(screen.getByRole("button", { name: /clonar equipo/i }));

    await waitFor(() => {
      expect(clonarEquipo).toHaveBeenCalled();
    });
    expect(onClonado).toHaveBeenCalled();
  });
});
