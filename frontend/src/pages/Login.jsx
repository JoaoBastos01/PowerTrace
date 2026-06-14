import { useState } from "react";
import {
  Link,
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";

import { useAuth } from "../AuthContext";
import Feedback from "../components/Feedback";

export default function Login() {
  const { user, login } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (user) {
    return <Navigate to="/projetos" replace />;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/projetos");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-panel">
        <div className="auth-heading">
          <span className="brand-mark large">PT</span>
          <div>
            <h1>PowerTrace</h1>
            <p>Entre para acessar seus projetos elétricos.</p>
          </div>
        </div>
        <Feedback>{location.state?.message}</Feedback>
        <Feedback type="error">{error}</Feedback>
        <form className="form-stack" onSubmit={handleSubmit}>
          <label>
            E-mail
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              required
            />
          </label>
          <label>
            Senha
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              minLength="8"
              required
            />
          </label>
          <button
            type="submit"
            className="button button-primary"
            disabled={submitting}
          >
            {submitting ? "Entrando..." : "Entrar"}
          </button>
        </form>
        <p className="auth-link">
          Ainda não possui conta? <Link to="/cadastro">Cadastre-se</Link>
        </p>
      </section>
    </main>
  );
}
