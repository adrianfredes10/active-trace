import { Navigate, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "@/features/auth/components/ProtectedRoute";
import { ForgotPasswordPage } from "@/features/auth/pages/ForgotPasswordPage";
import { LoginPage } from "@/features/auth/pages/LoginPage";
import { ResetPasswordPage } from "@/features/auth/pages/ResetPasswordPage";
import { TwoFactorPage } from "@/features/auth/pages/TwoFactorPage";
import { AuditoriaPage } from "@/features/auditoria/pages/AuditoriaPage";
import { ComisionPage } from "@/features/comision/pages/ComisionPage";
import { CoordinacionPage } from "@/features/coordinacion/pages/CoordinacionPage";
import { FinanzasPage } from "@/features/finanzas/pages/FinanzasPage";
import { AdminPage } from "@/features/admin/pages/AdminPage";
import { AppLayout } from "@/shared/components/AppLayout";
import { HomePage } from "@/shared/pages/HomePage";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/2fa" element={<TwoFactorPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/comision" element={<ComisionPage />} />
          <Route path="/coordinacion" element={<CoordinacionPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/finanzas" element={<FinanzasPage />} />
          <Route path="/auditoria" element={<AuditoriaPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
