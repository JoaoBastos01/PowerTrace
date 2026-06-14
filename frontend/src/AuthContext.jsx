import { createContext, useContext, useEffect, useState } from "react";

import {
  apiRequest,
  clearToken,
  getToken,
  setToken,
} from "./api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(getToken()));

  useEffect(() => {
    let active = true;

    async function restoreSession() {
      if (!getToken()) {
        setLoading(false);
        return;
      }
      try {
        const currentUser = await apiRequest("/api/v1/auth/me");
        if (active) {
          setUser(currentUser);
        }
      } catch {
        clearToken();
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    function handleUnauthorized() {
      setUser(null);
      setLoading(false);
    }

    restoreSession();
    window.addEventListener("powertrace:unauthorized", handleUnauthorized);
    return () => {
      active = false;
      window.removeEventListener("powertrace:unauthorized", handleUnauthorized);
    };
  }, []);

  async function login(email, password) {
    const response = await apiRequest("/api/v1/auth/login", {
      method: "POST",
      auth: false,
      body: JSON.stringify({ email, password }),
    });
    setToken(response.access_token);
    const currentUser = await apiRequest("/api/v1/auth/me");
    setUser(currentUser);
  }

  function logout() {
    clearToken();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
