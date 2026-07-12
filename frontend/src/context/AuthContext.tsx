import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { store } from "@/mocks/store";
import { authService } from "@/services";
import { USE_MOCKS, setToken } from "@/services/apiClient";
import type { Role, User } from "@/types";

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  hydrated: boolean;
  login: (email: string, password: string) => Promise<User>;
  logout: () => void;
  setDemoUser: (id: string) => void;
  hasRole: (role: Role | Role[]) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);
const STORAGE_KEY = "assetflow.userId";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [, force] = useState({});

  // Rehydrate on mount
  useEffect(() => {
    let cancelled = false;

    async function hydrate() {
      if (USE_MOCKS) {
        // Mock: restore user from stored userId
        const storedId = window.localStorage.getItem(STORAGE_KEY);
        const found = storedId
          ? store.employees.find((e) => e.id === storedId) ?? null
          : null;
        if (!cancelled) {
          setUser(found);
          setHydrated(true);
        }
      } else {
        // API: rehydrate from JWT via /auth/me
        const me = await authService.me();
        if (!cancelled) {
          setUser(me);
          setHydrated(true);
        }
      }
    }

    hydrate();

    // Keep mock store in sync when it mutates
    const unsub = USE_MOCKS
      ? store.subscribe(() => {
          const storedId = window.localStorage.getItem(STORAGE_KEY);
          setUser(storedId ? store.employees.find((e) => e.id === storedId) ?? null : null);
          force({});
        })
      : () => {};

    return () => {
      cancelled = true;
      unsub();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: !!user,
      hydrated,
      async login(email, password) {
        const u = await authService.login(email, password);
        if (USE_MOCKS) {
          // Mock path: persist the userId
          window.localStorage.setItem(STORAGE_KEY, u.id);
        }
        setUser(u);
        return u;
      },
      logout() {
        authService.logout();
        if (USE_MOCKS) {
          window.localStorage.removeItem(STORAGE_KEY);
        }
        setUser(null);
      },
      setDemoUser(id: string) {
        // Mock-only: switch the active demo persona
        window.localStorage.setItem(STORAGE_KEY, id);
        const found = store.employees.find((e) => e.id === id) ?? null;
        setUser(found);
      },
      hasRole(role) {
        if (!user) return false;
        const roles = Array.isArray(role) ? role : [role];
        return roles.includes(user.role);
      },
    }),
    [user, hydrated],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export const roleLabel = (r: Role) =>
  ({
    admin: "Admin",
    asset_manager: "Asset Manager",
    department_head: "Department Head",
    employee: "Employee",
  })[r];

// Re-export for convenience so callers don't need to import setToken separately
export { setToken };
