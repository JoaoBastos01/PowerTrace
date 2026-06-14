import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "../AuthContext";

export default function ProtectedRoute() {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="page-status">Verificando sessão...</div>;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}
