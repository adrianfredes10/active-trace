const ACCESS_KEY = "activia.access";
const REFRESH_KEY = "activia.refresh";

let accessTokenMemory: string | null = null;

export function getAccessToken(): string | null {
  return accessTokenMemory;
}

export function setAccessToken(token: string | null): void {
  accessTokenMemory = token;
}

export function getRefreshToken(): string | null {
  return sessionStorage.getItem(REFRESH_KEY);
}

export function setRefreshToken(token: string | null): void {
  if (token) {
    sessionStorage.setItem(REFRESH_KEY, token);
  } else {
    sessionStorage.removeItem(REFRESH_KEY);
  }
}

export function persistSession(access: string, refresh: string): void {
  setAccessToken(access);
  setRefreshToken(refresh);
}

export function clearSession(): void {
  setAccessToken(null);
  setRefreshToken(null);
  sessionStorage.removeItem(ACCESS_KEY);
}

export function restoreRefreshFromStorage(): string | null {
  return getRefreshToken();
}
