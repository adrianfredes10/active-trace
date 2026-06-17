import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { TareasPanel } from "@/features/coordinacion/components/TareasPanel";

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

const actualizarEstadoTarea = vi.fn().mockResolvedValue({ id: "t1", estado: "Resuelta" });

vi.mock("@/features/coordinacion/services/tareaService", () => ({
  fetchTareasAdmin: vi.fn().mockResolvedValue([
    {
      id: "t1",
      materia_id: "m1",
      asignado_a: "u1",
      asignado_por: "u2",
      estado: "Pendiente",
      descripcion: "Revisar padrón",
      contexto_id: null,
    },
  ]),
  actualizarEstadoTarea: (...args: unknown[]) => actualizarEstadoTarea(...args),
}));

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("TareasPanel", () => {
  it("actualiza estado de tarea", async () => {
    const user = userEvent.setup();
    renderWithQuery(<TareasPanel />);

    await waitFor(() => {
      expect(screen.getByText(/Revisar padrón/)).toBeInTheDocument();
    });

    await user.selectOptions(screen.getByRole("combobox"), "Resuelta");

    await waitFor(() => {
      expect(actualizarEstadoTarea).toHaveBeenCalledWith("t1", "Resuelta");
    });
  });
});
