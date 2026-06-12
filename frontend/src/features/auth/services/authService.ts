import { api } from "@/shared/services/api";
import type {
  ForgotPasswordPayload,
  LoginPayload,
  LoginResponse,
  PermisosEfectivosResponse,
  ResetPasswordPayload,
  TokenResponse,
  TwoFactorVerifyPayload,
} from "@/features/auth/types/auth";

export async function loginRequest(payload: LoginPayload): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>("/api/auth/login", payload);
  return data;
}

export async function verify2faRequest(
  payload: TwoFactorVerifyPayload,
): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/api/auth/2fa/verify", payload);
  return data;
}

export async function logoutRequest(refreshToken: string): Promise<void> {
  await api.post("/api/auth/logout", { refresh_token: refreshToken });
}

export async function forgotPasswordRequest(
  payload: ForgotPasswordPayload,
): Promise<void> {
  await api.post("/api/auth/forgot-password", payload);
}

export async function resetPasswordRequest(payload: ResetPasswordPayload): Promise<void> {
  await api.post("/api/auth/reset-password", payload);
}

export async function fetchPermisosEfectivos(): Promise<string[]> {
  const { data } = await api.get<PermisosEfectivosResponse>("/api/rbac/permisos-efectivos");
  return data.permisos;
}
