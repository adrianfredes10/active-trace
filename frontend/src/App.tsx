import { Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "@/features/auth/components/ProtectedRoute";
import { ForgotPasswordPage } from "@/features/auth/pages/ForgotPasswordPage";
import { LoginPage } from "@/features/auth/pages/LoginPage";
import { ResetPasswordPage } from "@/features/auth/pages/ResetPasswordPage";
import { TwoFactorPage } from "@/features/auth/pages/TwoFactorPage";
import { AuditoriaPage } from "@/features/auditoria/pages/AuditoriaPage";
import { ComisionPage } from "@/features/comision/pages/ComisionPage";
import { CoordinacionPage } from "@/features/coordinacion/pages/CoordinacionPage";
import { AdminLayout } from "@/features/admin/layout/AdminLayout";
import { AdminCarrerasPage } from "@/features/admin/pages/AdminCarrerasPage";
import { AdminCohortesPage } from "@/features/admin/pages/AdminCohortesPage";
import { AdminDashboardPage } from "@/features/admin/pages/AdminDashboardPage";
import { AdminMateriasPage } from "@/features/admin/pages/AdminMateriasPage";
import { AdminUsuariosPage } from "@/features/admin/pages/AdminUsuariosPage";
import { ColoquiosLayout } from "@/features/coloquios/layout/ColoquiosLayout";
import { ColoquioCrearPage } from "@/features/coloquios/pages/ColoquioCrearPage";
import { ColoquioDetailPage } from "@/features/coloquios/pages/ColoquioDetailPage";
import { ColoquiosDashboardPage } from "@/features/coloquios/pages/ColoquiosDashboardPage";
import { ColoquiosPage } from "@/features/coloquios/pages/ColoquiosPage";
import { EncuentrosPage } from "@/features/encuentros/pages/EncuentrosPage";
import { FinanzasLayout } from "@/features/finanzas/layout/FinanzasLayout";
import { FinanzasFacturasPage } from "@/features/finanzas/pages/FinanzasFacturasPage";
import { FinanzasGrillaPage } from "@/features/finanzas/pages/FinanzasGrillaPage";
import { FinanzasLiquidacionesPage } from "@/features/finanzas/pages/FinanzasLiquidacionesPage";
import { FinanzasPage } from "@/features/finanzas/pages/FinanzasPage";
import { AppLayout } from "@/shared/components/AppLayout";
import { HomePage } from "@/shared/pages/HomePage";
import { NotFoundPage } from "@/shared/pages/NotFoundPage";

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
          <Route path="/encuentros" element={<EncuentrosPage />} />
          <Route path="/coloquios" element={<ColoquiosPage />}>
            <Route element={<ColoquiosLayout />}>
              <Route index element={<ColoquiosDashboardPage />} />
              <Route path="crear" element={<ColoquioCrearPage />} />
              <Route path=":evaluacionId" element={<ColoquioDetailPage />} />
            </Route>
          </Route>
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<AdminDashboardPage />} />
            <Route path="carreras" element={<AdminCarrerasPage />} />
            <Route path="materias" element={<AdminMateriasPage />} />
            <Route path="cohortes" element={<AdminCohortesPage />} />
            <Route path="usuarios" element={<AdminUsuariosPage />} />
          </Route>
          <Route path="/finanzas" element={<FinanzasPage />}>
            <Route element={<FinanzasLayout />}>
              <Route index element={<FinanzasLiquidacionesPage />} />
              <Route path="grilla" element={<FinanzasGrillaPage />} />
              <Route path="facturas" element={<FinanzasFacturasPage />} />
            </Route>
          </Route>
          <Route path="/auditoria" element={<AuditoriaPage />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
