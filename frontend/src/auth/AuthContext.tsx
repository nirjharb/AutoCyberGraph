import React, { createContext, useCallback, useContext, useState } from "react";
import { ApiUser, clearSession, getUser, setSession } from "../api/client";

interface AuthState {
  user: ApiUser | null;
  login: (token: string, user: ApiUser) => void;
  logout: () => void;
  hasRole: (...roles: string[]) => boolean;
}

const AuthContext = createContext<AuthState>({
  user: null,
  login: () => undefined,
  logout: () => undefined,
  hasRole: () => false,
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<ApiUser | null>(() => getUser());

  const login = useCallback((token: string, u: ApiUser) => {
    setSession(token, u);
    setUser(u);
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setUser(null);
  }, []);

  const hasRole = useCallback(
    (...roles: string[]) => {
      if (!user) return false;
      return user.role === "ADMIN" || roles.includes(user.role);
    },
    [user],
  );

  return <AuthContext.Provider value={{ user, login, logout, hasRole }}>{children}</AuthContext.Provider>;
};

export const useAuth = () => useContext(AuthContext);
