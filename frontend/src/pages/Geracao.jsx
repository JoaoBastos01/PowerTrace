import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { apiRequest, downloadAuthenticatedFile } from "../api";
import Feedback from "../components/Feedback";

const DEFAULT_TUES = {
  kitchen: [
    { id: "kitchen_electric_faucet", name: "Torneira elétrica" },
  ],
  living_kitchen: [
    { id: "living_kitchen_electric_faucet", name: "Torneira elétrica" },
  ],
  garage: [
    { id: "garage_gate_motor", name: "Motor do portão" },
  ],
};

function roomDefaults(roomType) {
  if (roomType.startsWith("bathroom_") && roomType !== "bathroom_social") {
    return [{ id: "bathroom_electric_shower", name: "Chuveiro elétrico" }];
  }
  return DEFAULT_TUES[roomType] || [];
}

function formatNumber(value, decimals = 2) {
  return new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value || 0);
}

function circuitType(value) {
  return {
    lighting: "Iluminação",
    general: "TUG",
    dedicated: "TUE",
  }[value] || value;
}

function generationStatus(value) {
  return {
    pending: "Pendente",
    generated: "Gerada",
    failed: "Falhou",
  }[value] || value;
}

function categoryName(value) {
  return {
    kitnet: "Kitnet",
    small: "Pequena",
    medium: "Média",
    large: "Grande",
  }[value] || value;
}

function createEditorState(detail) {
  const inputRooms = new Map(
    (detail.input?.rooms || []).map((room) => [room.room_key, room]),
  );

  return (detail.result?.rooms || []).map((room) => {
    const inputRoom = inputRooms.get(room.room_type);
    const disabledDefaults = new Set(
      (inputRoom?.specific_outlets || [])
        .filter((outlet) => outlet.source === "default" && !outlet.enabled)
        .map((outlet) => outlet.id),
    );
    const activeDefaults = new Set(
      room.specific_outlets
        .filter((outlet) => outlet.source === "default")
        .map((outlet) => outlet.key),
    );
    const defaults = roomDefaults(room.room_type).map((outlet) => ({
      ...outlet,
      enabled: !disabledDefaults.has(outlet.id)
        && (
          activeDefaults.has(outlet.id)
          || room.specific_outlets.length === 0
        ),
    }));
    const inputCustom = (inputRoom?.specific_outlets || []).filter(
      (outlet) => outlet.source === "custom" && outlet.enabled,
    );
    const custom = inputCustom.length > 0
      ? inputCustom.map((outlet) => ({ ...outlet }))
      : room.specific_outlets
          .filter((outlet) => outlet.source === "custom")
          .map((outlet) => ({
            id: outlet.key,
            name: outlet.name,
            quantity: 1,
            power_w: outlet.power_w,
            voltage: outlet.voltage,
            power_factor: outlet.power_factor,
            enabled: true,
            source: "custom",
          }));

    return {
      room_key: room.room_type,
      room_type: room.room_type,
      room_name: room.name,
      defaults,
      custom,
    };
  });
}

export default function Geracao() {
  const { projectId, generationId } = useParams();
  const navigate = useNavigate();
  const [detail, setDetail] = useState(null);
  const [editor, setEditor] = useState([]);
  const [activeTab, setActiveTab] = useState("rooms");
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadGeneration() {
      setLoading(true);
      setError("");
      try {
        const response = await apiRequest(
          `/api/v1/projects/${projectId}/generations/${generationId}`,
        );
        setDetail(response);
        setEditor(createEditorState(response));
      } catch (requestError) {
        setError(requestError.message);
      } finally {
        setLoading(false);
      }
    }
    loadGeneration();
  }, [projectId, generationId]);

  const rooms = detail?.result?.rooms || [];
  const circuits = detail?.result?.circuits || [];
  const canDownload = detail?.status === "generated" && detail?.download_url;

  const totalPoints = useMemo(
    () => rooms.reduce((total, room) => total + room.load_points.length, 0),
    [rooms],
  );

  function toggleDefault(roomIndex, outletIndex) {
    setEditor((current) => current.map((room, currentRoomIndex) => {
      if (currentRoomIndex !== roomIndex) return room;
      return {
        ...room,
        defaults: room.defaults.map((outlet, currentOutletIndex) => (
          currentOutletIndex === outletIndex
            ? { ...outlet, enabled: !outlet.enabled }
            : outlet
        )),
      };
    }));
  }

  function addCustom(roomIndex) {
    const id = `custom_${Date.now()}`;
    setEditor((current) => current.map((room, index) => (
      index === roomIndex
        ? {
            ...room,
            custom: [
              ...room.custom,
              {
                id,
                name: "",
                quantity: 1,
                power_w: "",
                voltage: 127,
                power_factor: 1,
                enabled: true,
                source: "custom",
              },
            ],
          }
        : room
    )));
  }

  function updateCustom(roomIndex, outletIndex, field, value) {
    setEditor((current) => current.map((room, currentRoomIndex) => (
      currentRoomIndex === roomIndex
        ? {
            ...room,
            custom: room.custom.map((outlet, currentOutletIndex) => (
              currentOutletIndex === outletIndex
                ? { ...outlet, [field]: value }
                : outlet
            )),
          }
        : room
    )));
  }

  function removeCustom(roomIndex, outletIndex) {
    setEditor((current) => current.map((room, currentRoomIndex) => (
      currentRoomIndex === roomIndex
        ? {
            ...room,
            custom: room.custom.filter((_, index) => index !== outletIndex),
          }
        : room
    )));
  }

  function buildOverrideRooms() {
    return editor.flatMap((room) => {
      const disabledDefaults = room.defaults
        .filter((outlet) => !outlet.enabled)
        .map((outlet) => ({
          id: outlet.id,
          enabled: false,
          source: "default",
        }));
      const custom = room.custom.map((outlet) => {
        const quantity = Number(outlet.quantity);
        const power = Number(outlet.power_w);
        const powerFactor = Number(outlet.power_factor);
        if (!outlet.name.trim()) {
          throw new Error(`Informe o nome da TUE em ${room.room_name}.`);
        }
        if (quantity < 1 || quantity > 20) {
          throw new Error(`A quantidade em ${room.room_name} deve ser de 1 a 20.`);
        }
        if (power <= 0) {
          throw new Error(`A potência em ${room.room_name} deve ser positiva.`);
        }
        if (powerFactor <= 0 || powerFactor > 1) {
          throw new Error(
            `O fator de potência em ${room.room_name} deve ser maior que 0 e até 1.`,
          );
        }
        return {
          id: outlet.id,
          name: outlet.name.trim(),
          quantity,
          power_w: power,
          voltage: Number(outlet.voltage),
          power_factor: powerFactor,
          enabled: true,
          source: "custom",
        };
      });
      const specificOutlets = [...disabledDefaults, ...custom];
      return specificOutlets.length > 0
        ? [{
            room_key: room.room_key,
            room_type: room.room_type,
            general_outlets_locked: true,
            specific_outlets: specificOutlets,
          }]
        : [];
    });
  }

  async function regenerate() {
    setError("");
    setWorking(true);
    try {
      const payload = {
        width: detail.input.width,
        length: detail.input.length,
        seed: detail.input.seed,
        rooms: buildOverrideRooms(),
        output_format: "dxf",
      };
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
      setWorking(false);
    }
  }

  async function download() {
    setWorking(true);
    setError("");
    try {
      await downloadAuthenticatedFile(detail.download_url);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setWorking(false);
    }
  }

  if (loading) {
    return <div className="page-status">Carregando geração...</div>;
  }

  return (
    <div>
      <Link className="back-link" to={`/projetos/${projectId}`}>
        ← Voltar ao projeto
      </Link>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Resultado da geração</p>
          <h1>Planta elétrica dimensionada</h1>
          <p>
            Seed {detail?.seed} · Status {generationStatus(detail?.status)}
          </p>
        </div>
        <button
          type="button"
          className="button button-primary"
          onClick={download}
          disabled={!canDownload || working}
        >
          Baixar DXF
        </button>
      </div>
      <Feedback type="error">
        {error || (
          detail?.status === "failed"
            ? "A geração falhou. Revise as dimensões ou as cargas informadas."
            : ""
        )}
      </Feedback>

      {detail?.result && (
        <>
          <section className="metrics">
            <div><span>Área total</span><strong>{formatNumber(detail.result.total_area)} m²</strong></div>
            <div><span>Potência total</span><strong>{detail.result.total_power_w} W</strong></div>
            <div><span>Cômodos</span><strong>{rooms.length}</strong></div>
            <div><span>Pontos de carga</span><strong>{totalPoints}</strong></div>
            <div>
              <span>Categoria</span>
              <strong>{categoryName(detail.result.category)}</strong>
            </div>
          </section>

          <nav className="tabs" aria-label="Resultado da geração">
            <button
              type="button"
              className={activeTab === "rooms" ? "active" : ""}
              onClick={() => setActiveTab("rooms")}
            >
              Cômodos
            </button>
            <button
              type="button"
              className={activeTab === "circuits" ? "active" : ""}
              onClick={() => setActiveTab("circuits")}
            >
              Circuitos
            </button>
            <button
              type="button"
              className={activeTab === "tues" ? "active" : ""}
              onClick={() => setActiveTab("tues")}
            >
              Personalizar TUEs
            </button>
          </nav>

          {activeTab === "rooms" && (
            <div className="data-table-wrap">
              <table className="data-table technical-table">
                <thead>
                  <tr>
                    <th>Cômodo</th>
                    <th>Área</th>
                    <th>Luminárias</th>
                    <th>TUGs</th>
                    <th>TUEs</th>
                    <th>Potência total</th>
                  </tr>
                </thead>
                <tbody>
                  {rooms.map((room) => (
                    <tr key={room.room_type}>
                      <td><strong>{room.name}</strong></td>
                      <td>{formatNumber(room.area)} m²</td>
                      <td>
                        {room.load_summary.lighting.count} ·{" "}
                        {room.load_summary.lighting.total_power_w} W
                      </td>
                      <td>
                        {room.load_summary.general_outlets.count} ·{" "}
                        {room.load_summary.general_outlets.total_power_w} W
                      </td>
                      <td>
                        {room.load_summary.specific_outlets.count} ·{" "}
                        {room.load_summary.specific_outlets.total_power_w} W
                      </td>
                      <td><strong>{room.load_summary.total_power_w} W</strong></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === "circuits" && (
            <div className="data-table-wrap">
              <table className="data-table technical-table">
                <thead>
                  <tr>
                    <th>Circuito</th>
                    <th>Cômodo</th>
                    <th>Tipo</th>
                    <th>Cargas</th>
                    <th>Potência</th>
                    <th>Tensão</th>
                    <th>FP</th>
                    <th>Corrente</th>
                    <th>Projeto</th>
                    <th>Disjuntor</th>
                    <th>Bitola</th>
                    <th>Capacidade</th>
                    <th>Resistência</th>
                  </tr>
                </thead>
                <tbody>
                  {circuits.map((circuit) => (
                    <tr key={circuit.id}>
                      <td><strong>{circuit.id}</strong></td>
                      <td>{circuit.room_name}</td>
                      <td>{circuitType(circuit.circuit_type)}</td>
                      <td title={circuit.load_points.map((point) => point.name).join(", ")}>
                        {circuit.load_count}
                      </td>
                      <td>{circuit.total_power_w} W</td>
                      <td>{circuit.voltage} V</td>
                      <td>{formatNumber(circuit.power_factor)}</td>
                      <td>{formatNumber(circuit.current_a)} A</td>
                      <td>{formatNumber(circuit.design_current_a)} A</td>
                      <td>{circuit.breaker_a} A</td>
                      <td>{formatNumber(circuit.wire_gauge_mm2, 1)} mm²</td>
                      <td>{formatNumber(circuit.wire_max_current_a, 1)} A</td>
                      <td>{formatNumber(circuit.wire_resistance_ohm_km, 3)} Ω/km</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === "tues" && (
            <section className="tue-editor">
              <div className="section-heading">
                <div>
                  <h2>Tomadas de uso específico</h2>
                  <p>Altere as cargas e gere uma nova versão com a mesma seed.</p>
                </div>
                <button
                  type="button"
                  className="button button-primary"
                  onClick={regenerate}
                  disabled={working}
                >
                  {working ? "Gerando..." : "Regenerar planta"}
                </button>
              </div>

              {editor.map((room, roomIndex) => (
                <div className="room-editor" key={room.room_key}>
                  <div className="room-editor-heading">
                    <h3>{room.room_name}</h3>
                    <button
                      type="button"
                      className="button button-small"
                      onClick={() => addCustom(roomIndex)}
                    >
                      Adicionar TUE
                    </button>
                  </div>

                  {room.defaults.map((outlet, outletIndex) => (
                    <label className="switch-row" key={outlet.id}>
                      <span>
                        <strong>{outlet.name}</strong>
                        <small>TUE padrão do cômodo</small>
                      </span>
                      <input
                        type="checkbox"
                        checked={outlet.enabled}
                        onChange={() => toggleDefault(roomIndex, outletIndex)}
                      />
                    </label>
                  ))}

                  {room.custom.map((outlet, outletIndex) => (
                    <div className="custom-tue" key={outlet.id}>
                      <label>
                        Nome
                        <input
                          value={outlet.name}
                          onChange={(event) => updateCustom(
                            roomIndex, outletIndex, "name", event.target.value,
                          )}
                        />
                      </label>
                      <label>
                        Quantidade
                        <input
                          type="number"
                          min="1"
                          max="20"
                          value={outlet.quantity}
                          onChange={(event) => updateCustom(
                            roomIndex, outletIndex, "quantity", event.target.value,
                          )}
                        />
                      </label>
                      <label>
                        Potência (W)
                        <input
                          type="number"
                          min="1"
                          value={outlet.power_w}
                          onChange={(event) => updateCustom(
                            roomIndex, outletIndex, "power_w", event.target.value,
                          )}
                        />
                      </label>
                      <label>
                        Tensão
                        <select
                          value={outlet.voltage}
                          onChange={(event) => updateCustom(
                            roomIndex, outletIndex, "voltage", event.target.value,
                          )}
                        >
                          <option value="127">127 V</option>
                          <option value="220">220 V</option>
                        </select>
                      </label>
                      <label>
                        Fator de potência
                        <input
                          type="number"
                          min="0.01"
                          max="1"
                          step="0.01"
                          value={outlet.power_factor}
                          onChange={(event) => updateCustom(
                            roomIndex,
                            outletIndex,
                            "power_factor",
                            event.target.value,
                          )}
                        />
                      </label>
                      <button
                        type="button"
                        className="button button-danger button-small"
                        onClick={() => removeCustom(roomIndex, outletIndex)}
                      >
                        Remover
                      </button>
                    </div>
                  ))}
                </div>
              ))}
            </section>
          )}
        </>
      )}
    </div>
  );
}
