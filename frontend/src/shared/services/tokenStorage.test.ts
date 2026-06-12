import { beforeEach, describe, expect, it } from "vitest";

import {
  clearSession,
  getAccessToken,
  getRefreshToken,
  persistSession,
} from "@/shared/services/tokenStorage";

describe("tokenStorage", () => {
  beforeEach(() => {
    clearSession();
  });

  it("persiste access en memoria y refresh en sessionStorage", () => {
    persistSession("access-1", "refresh-1");
    expect(getAccessToken()).toBe("access-1");
    expect(getRefreshToken()).toBe("refresh-1");
  });

  it("clearSession elimina ambos tokens", () => {
    persistSession("access-1", "refresh-1");
    clearSession();
    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
  });
});
