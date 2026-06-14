import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { apiRequest } from "../api";
import Feedback from "../components/Feedback";

export default function Projeto() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [form, setForm] = useState({ width: "8", length: "12", seed: "" });
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadProject() {
      try {
        setProject(await apiRequest(`/api/v1/projects/${projectId}`));
      } catch (requestError) {
        setError(requestError.message);
      } finally {
        setLoading(false);
      }
    }
    loadProject();
  }, [projectId]);

  async function generate(event) {
    event.preventDefault();
    setGenerating(true);
    setError("");
    const payload = {
      width: Number(form.width),
      length: Number(form.length),
      seed: form.seed === "" ? null : Number(form.seed),
      rooms: [],
      output_format: "dxf",
    };
    try {
      const response = await apiRequest(
        `/api/v1/projects/${projectId}/generations`,
        { method: "POST", body: JSON.stringify(payload) },
      );
      navigate(
        `/projetos/${projectId}/geracoes/${response.generation_id}`,
      );
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setGenerating(false);
    }
  }

  if (loading) {
    return <div className="page-status">Carregando projeto...</div>;
  }

  return (
    <div className="content-narrow">
      <Link className="back-link" to="/projetos">← Voltar aos projetos</Link>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Projeto</p>
          <h1>{project?.name || "Projeto não encontrado"}</h1>
          <p>{project?.description || "Sem descrição."}</p>
        </div>
      </div>
      <Feedback type="error">{error}</Feedback>

      <section className="workspace-section">
        <div className="section-heading">
          <div>
            <h2>Gerar planta elétrica</h2>
            <p>Informe as dimensões externas da residência em metros.</p>
          </div>
        </div>
        <form className="inline-form generation-form" onSubmit={generate}>
          <label>
            Largura (m)
            <input
              type="number"
              min="1"
              step="0.1"
              value={form.width}
              onChange={(event) => setForm({ ...form, width: event.target.value })}
              required
            />
          </label>
          <label>
            Comprimento (m)
            <input
              type="number"
              min="1"
              step="0.1"
              value={form.length}
              onChange={(event) => setForm({ ...form, length: event.target.value })}
              required
            />
          </label>
          <label>
            Seed opcional
            <input
              type="number"
              min="0"
              max="4294967295"
              value={form.seed}
              onChange={(event) => setForm({ ...form, seed: event.target.value })}
              placeholder="Gerada automaticamente"
            />
          </label>
          <button
            type="submit"
            className="button button-primary"
            disabled={generating}
          >
            {generating ? "Gerando planta..." : "Gerar planta"}
          </button>
        </form>
        <p className="helper-text">
          A geração é síncrona e pode levar alguns segundos.
        </p>
      </section>
    </div>
  );
}
