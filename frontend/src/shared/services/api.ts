import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

import {
  clearSession,
  getAccessToken,
  getRefreshToken,
  persistSession,
  setAccessToken,
} from "@/shared/services/tokenStorage";

type RetryConfig = InternalAxiosRequestConfig & { _retry?: boolean };

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "";

export const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

let refreshPromise: Promise<string | null> | null = null;

function isPublicAuthPath(url: string | undefined): boolean {
  if (!url) return false;
  return (
    url.includes("/api/auth/login") ||
    url.includes("/api/auth/refresh") ||
    url.includes("/api/auth/forgot-password") ||
    url.includes("/api/auth/reset-password") ||
    url.includes("/api/auth/2fa/verify")
  );
}

async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) {
    return null;
  }
  try {
    const { data } = await axios.post<{ access_token: string; refresh_token: string }>(
      `${baseURL}/api/auth/refresh`,
      { refresh_token: refresh },
      { headers: { "Content-Type": "application/json" } },
    );
    persistSession(data.access_token, data.refresh_token);
    return data.access_token;
  } catch {
    clearSession();
    return null;
  }
}

export function onSessionExpired(callback: () => void): () => void {
  sessionExpiredHandlers.add(callback);
  return () => sessionExpiredHandlers.delete(callback);
}

const sessionExpiredHandlers = new Set<() => void>();

function notifySessionExpired(): void {
  sessionExpiredHandlers.forEach((handler) => handler());
}

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetryConfig | undefined;
    if (
      !original ||
      error.response?.status !== 401 ||
      original._retry ||
      isPublicAuthPath(original.url)
    ) {
      return Promise.reject(error);
    }

    original._retry = true;

    if (!refreshPromise) {
      refreshPromise = refreshAccessToken().finally(() => {
        refreshPromise = null;
      });
    }

    const newAccess = await refreshPromise;
    if (!newAccess) {
      notifySessionExpired();
      return Promise.reject(error);
    }

    original.headers.Authorization = `Bearer ${newAccess}`;
    return api(original);
  },
);

export function setSessionTokens(access: string, refresh: string): void {
  persistSession(access, refresh);
}

export function wipeSession(): void {
  clearSession();
}

export async function tryRestoreSession(): Promise<boolean> {
  if (getAccessToken()) {
    return true;
  }
  const token = await refreshAccessToken();
  return Boolean(token);
}

export function peekAccessToken(): string | null {
  return getAccessToken();
}

export function setPeekAccessToken(token: string | null): void {
  setAccessToken(token);
}
