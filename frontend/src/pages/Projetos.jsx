import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiRequest } from "../api";
import Feedback from "../components/Feedback";

function formatDate(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function Projetos() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [form, setForm] = useState({ name: "", description: "" });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function loadProjects() {
    setLoading(true);
    setError("");
    try {
      const response = await apiRequest("/api/v1/projects");
      setProjects(response.items);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadProjects();
  }, []);

  async function createProject(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const project = await apiRequest("/api/v1/projects", {
        method: "POST",
        body: JSON.stringify(form),
      });
      navigate(`/projetos/${project.id}`);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page-grid projects-layout">
      <section>
        <div className="page-heading">
          <div>
            <p className="eyebrow">Projetos</p>
            <h1>Seus projetos elétricos</h1>
          </div>
          <button
            type="button"
            className="button button-quiet"
            onClick={loadProjects}
          >
            Atualizar
          </button>
        </div>
        <Feedback type="error">{error}</Feedback>
        {loading ? (
          <div className="page-status">Carregando projetos...</div>
        ) : projects.length === 0 ? (
          <div className="empty-state">
            <h2>Nenhum projeto criado</h2>
            <p>Use o formulário ao lado para iniciar sua primeira planta.</p>
          </div>
        ) : (
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Projeto</th>
                  <th>Descrição</th>
                  <th>Atualizado em</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {projects.map((project) => (
                  <tr key={project.id}>
                    <td><strong>{project.name}</strong></td>
                    <td>{project.description || "Sem descrição"}</td>
                    <td>{formatDate(project.updated_at)}</td>
                    <td className="align-right">
                      <button
                        type="button"
                        className="button button-small"
                        onClick={() => navigate(`/projetos/${project.id}`)}
                      >
                        Abrir
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <aside className="side-panel">
        <h2>Novo projeto</h2>
        <form className="form-stack" onSubmit={createProject}>
          <label>
            Nome
            <input
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              maxLength="120"
              required
            />
          </label>
          <label>
            Descrição
            <textarea
              rows="4"
              value={form.description}
              onChange={(event) => setForm({
                ...form,
                description: event.target.value,
              })}
            />
          </label>
          <button
            type="submit"
            className="button button-primary"
            disabled={submitting}
          >
            {submitting ? "Criando..." : "Criar projeto"}
          </button>
        </form>
      </aside>
    </div>
  );
}
