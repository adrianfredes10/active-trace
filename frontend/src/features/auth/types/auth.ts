export type LoginPayload = {
  tenant_slug: string;
  email: string;
  password: string;
};

export type LoginResponse = {
  requires_2fa: boolean;
  challenge_token?: string | null;
  access_token?: string | null;
  refresh_token?: string | null;
  token_type?: string;
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type TwoFactorVerifyPayload = {
  challenge_token: string;
  code: string;
};

export type ForgotPasswordPayload = {
  tenant_slug: string;
  email: string;
};

export type ResetPasswordPayload = {
  token: string;
  new_password: string;
};

export type PermisosEfectivosResponse = {
  permisos: string[];
  roles: string[];
};

export type AuthSession = {
  accessToken: string;
  refreshToken: string;
};
