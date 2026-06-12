import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useQueryClient } from "@tanstack/react-query";

import {
  loginRequest,
  logoutRequest,
  verify2faRequest,
} from "@/features/auth/services/authService";
import type { LoginPayload } from "@/features/auth/types/auth";
import {
  onSessionExpired,
  setSessionTokens,
  tryRestoreSession,
  wipeSession,
} from "@/shared/services/api";
import {
  clearSession,
  getAccessToken,
  getRefreshToken,
  persistSession,
} from "@/shared/services/tokenStorage";

type AuthContextValue = {
  isAuthenticated: boolean;
  isBootstrapping: boolean;
  login: (payload: LoginPayload) => Promise<{ requires2fa: boolean; challengeToken?: string }>;
  complete2fa: (challengeToken: string, code: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isBootstrapping, setIsBootstrapping] = useState(true);

  const markLoggedOut = useCallback(() => {
    wipeSession();
    setIsAuthenticated(false);
    queryClient.clear();
  }, [queryClient]);

  useEffect(() => {
    let active = true;
    void (async () => {
      const restored = await tryRestoreSession();
      if (!active) return;
      setIsAuthenticated(restored);
      setIsBootstrapping(false);
    })();
    const unsubscribe = onSessionExpired(markLoggedOut);
    return () => {
      active = false;
      unsubscribe();
    };
  }, [markLoggedOut]);

  const login = useCallback(async (payload: LoginPayload) => {
    const result = await loginRequest(payload);
    if (result.requires_2fa) {
      return {
        requires2fa: true,
        challengeToken: result.challenge_token ?? undefined,
      };
    }
    if (!result.access_token || !result.refresh_token) {
      throw new Error("Respuesta de login inválida");
    }
    setSessionTokens(result.access_token, result.refresh_token);
    setIsAuthenticated(true);
    return { requires2fa: false };
  }, []);

  const complete2fa = useCallback(async (challengeToken: string, code: string) => {
    const tokens = await verify2faRequest({ challenge_token: challengeToken, code });
    setSessionTokens(tokens.access_token, tokens.refresh_token);
    setIsAuthenticated(true);
  }, []);

  const logout = useCallback(async () => {
    const refresh = getRefreshToken();
    if (refresh && getAccessToken()) {
      try {
        await logoutRequest(refresh);
      } catch {
        // logout best-effort
      }
    }
    markLoggedOut();
  }, [markLoggedOut]);

  const value = useMemo(
    () => ({ isAuthenticated, isBootstrapping, login, complete2fa, logout }),
    [isAuthenticated, isBootstrapping, login, complete2fa, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth debe usarse dentro de AuthProvider");
  }
  return ctx;
}

export function bootstrapSession(access: string, refresh: string): void {
  persistSession(access, refresh);
}

export function hardLogout(): void {
  clearSession();
}
