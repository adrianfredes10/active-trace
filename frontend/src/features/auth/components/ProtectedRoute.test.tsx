import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { ProtectedRoute } from "@/features/auth/components/ProtectedRoute";

vi.mock("@/features/auth/hooks/AuthProvider", () => ({
  useAuth: () => ({
    isAuthenticated: false,
    isBootstrapping: false,
  }),
}));

describe("ProtectedRoute", () => {
  it("redirige a login sin sesión", () => {
    render(
      <MemoryRouter initialEntries={["/privado"]}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route path="/privado" element={<div>Secreto</div>} />
          </Route>
          <Route path="/login" element={<div>Pantalla login</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("Pantalla login")).toBeInTheDocument();
  });
});
