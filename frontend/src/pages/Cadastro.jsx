import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { apiRequest } from "../api";
import { useAuth } from "../AuthContext";
import Feedback from "../components/Feedback";

export default function Cadastro() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (user) {
    return <Navigate to="/projetos" replace />;
  }

  function updateField(event) {
    setForm({ ...form, [event.target.name]: event.target.value });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await apiRequest("/api/v1/auth/register", {
        method: "POST",
        auth: false,
        body: JSON.stringify(form),
      });
      navigate("/login", {
        replace: true,
        state: { message: "Cadastro realizado. Entre com sua nova conta." },
      });
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
            <h1>Criar conta</h1>
            <p>Cadastre-se para salvar e gerar seus projetos.</p>
          </div>
        </div>
        <Feedback type="error">{error}</Feedback>
        <form className="form-stack" onSubmit={handleSubmit}>
          <label>
            Nome
            <input
              name="name"
              value={form.name}
              onChange={updateField}
              maxLength="120"
              required
            />
          </label>
          <label>
            E-mail
            <input
              name="email"
              type="email"
              value={form.email}
              onChange={updateField}
              required
            />
          </label>
          <label>
            Senha
            <input
              name="password"
              type="password"
              value={form.password}
              onChange={updateField}
              minLength="8"
              maxLength="128"
              required
            />
          </label>
          <button
            type="submit"
            className="button button-primary"
            disabled={submitting}
          >
            {submitting ? "Cadastrando..." : "Cadastrar"}
          </button>
        </form>
        <p className="auth-link">
          Já possui conta? <Link to="/login">Entrar</Link>
        </p>
      </section>
    </main>
  );
}
