import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { store } from "@/mocks/store";
import type { Role, User } from "@/types";

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  hydrated: boolean;
  login: (email: string) => Promise<User>;
  logout: () => void;
  setDemoUser: (id: string) => void;
  hasRole: (role: Role | Role[]) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);
const STORAGE_KEY = "assetflow.userId";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [userId, setUserId] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [, force] = useState({});
  useEffect(() => {
    setUserId(window.localStorage.getItem(STORAGE_KEY));
    setHydrated(true);
    return store.subscribe(() => force({}));
  }, []);

  const user = useMemo(
    () => (userId ? store.employees.find((e) => e.id === userId) || null : null),
    [userId],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: !!user,
      hydrated,
      async login(email: string) {
        const u = store.employees.find((e) => e.email.toLowerCase() === email.toLowerCase());
        if (!u) throw new Error("Invalid credentials");
        window.localStorage.setItem(STORAGE_KEY, u.id);
        setUserId(u.id);
        return u;
      },
      logout() {
        window.localStorage.removeItem(STORAGE_KEY);
        setUserId(null);
      },
      setDemoUser(id: string) {
        window.localStorage.setItem(STORAGE_KEY, id);
        setUserId(id);
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
