import { Navigate, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "@/features/auth/components/ProtectedRoute";
import { ForgotPasswordPage } from "@/features/auth/pages/ForgotPasswordPage";
import { LoginPage } from "@/features/auth/pages/LoginPage";
import { ResetPasswordPage } from "@/features/auth/pages/ResetPasswordPage";
import { TwoFactorPage } from "@/features/auth/pages/TwoFactorPage";
import { AuditoriaPage } from "@/features/auditoria/pages/AuditoriaPage";
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
          <Route path="/auditoria" element={<AuditoriaPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
