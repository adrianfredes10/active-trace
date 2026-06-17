import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { EstructuraPanel } from "@/features/admin/components/EstructuraPanel";

const crearCarrera = vi.fn().mockResolvedValue({ id: "c1", codigo: "TUP", nombre: "TUP", estado: "Activa" });
const crearMateria = vi.fn().mockResolvedValue({ id: "m1", codigo: "MAT01", nombre: "Mat", estado: "Activa" });

vi.mock("@/features/admin/services/estructuraAdminService", () => ({
  fetchCarreras: vi.fn().mockResolvedValue([]),
  fetchMaterias: vi.fn().mockResolvedValue([]),
  crearCarrera: (...args: unknown[]) => crearCarrera(...args),
  crearMateria: (...args: unknown[]) => crearMateria(...args),
}));

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("EstructuraPanel", () => {
  it("crea carrera con código y nombre", async () => {
    const user = userEvent.setup();
    renderWithQuery(<EstructuraPanel />);

    await user.type(screen.getByLabelText(/código carrera/i), "TUP");
    await user.type(screen.getByLabelText(/nombre carrera/i), "Tecnicatura");
    await user.click(screen.getByRole("button", { name: /crear carrera/i }));

    await waitFor(() => {
      expect(crearCarrera).toHaveBeenCalledWith({ codigo: "TUP", nombre: "Tecnicatura" });
    });
  });

  it("crea materia con código y nombre", async () => {
    const user = userEvent.setup();
    renderWithQuery(<EstructuraPanel />);

    await user.type(screen.getByLabelText(/código materia/i), "MAT01");
    await user.type(screen.getByLabelText(/nombre materia/i), "Matemática");
    await user.click(screen.getByRole("button", { name: /crear materia/i }));

    await waitFor(() => {
      expect(crearMateria).toHaveBeenCalledWith({ codigo: "MAT01", nombre: "Matemática" });
    });
  });
});
