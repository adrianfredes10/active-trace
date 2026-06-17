import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { LoginPage } from "@/features/auth/pages/LoginPage";

vi.mock("@/features/auth/hooks/AuthProvider", () => ({
  useAuth: () => ({
    login: vi.fn(),
    isAuthenticated: false,
    isBootstrapping: false,
  }),
}));

describe("LoginPage", () => {
  it("renderiza el formulario de login", () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: /activia-trace/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /ingresar/i })).toBeInTheDocument();
  });
});
