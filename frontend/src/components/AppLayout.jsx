import { Link, Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "../AuthContext";

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link className="brand" to="/projetos">
          <span className="brand-mark">PT</span>
          <span>
            <strong>PowerTrace</strong>
            <small>Dimensionamento elétrico residencial</small>
          </span>
        </Link>
        <div className="user-menu">
          <span>{user?.name}</span>
          <button
            type="button"
            className="button button-quiet"
            onClick={handleLogout}
          >
            Sair
          </button>
        </div>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
