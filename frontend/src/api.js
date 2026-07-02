const API_URL = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");
const TOKEN_KEY = "powertrace_token";

export class ApiError extends Error {
  constructor(message, status, data = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

export function getToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  sessionStorage.removeItem(TOKEN_KEY);
}

function errorMessage(data, status) {
  const translatedDetails = {
    "An account with this email already exists.":
      "Este e-mail já está cadastrado.",
    "Email already registered.": "Este e-mail já está cadastrado.",
    "Invalid email or password.": "E-mail ou senha inválidos.",
    "Invalid or expired authentication credentials.":
      "E-mail, senha ou sessão inválidos.",
    "Could not validate credentials.": "Sua sessão não é válida.",
    "Project not found.": "Projeto não encontrado.",
    "Generation not found.": "Geração não encontrada.",
  };
  if (typeof data?.detail === "string" && translatedDetails[data.detail]) {
    return translatedDetails[data.detail];
  }
  if (Array.isArray(data?.detail)) {
    return "Revise os campos informados e tente novamente.";
  }
  if (typeof data?.error_message === "string") {
    return data.error_message;
  }
  const messages = {
    401: "Sua sessão expirou. Entre novamente.",
    404: "O recurso solicitado não foi encontrado.",
    409: "O arquivo ainda não está disponível.",
    422: "Revise os dados informados.",
    500: "Ocorreu um erro inesperado no servidor.",
  };
  if (messages[status]) {
    return messages[status];
  }
  return "Não foi possível concluir a solicitação.";
}

export async function apiRequest(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = getToken();

  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token && options.auth !== false) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401 && options.auth !== false) {
    clearToken();
    window.dispatchEvent(new Event("powertrace:unauthorized"));
  }

  const data = response.status === 204
    ? null
    : await response.json().catch(() => null);

  if (!response.ok) {
    throw new ApiError(errorMessage(data, response.status), response.status, data);
  }

  return data;
}

export async function downloadAuthenticatedFile(path) {
  const token = getToken();
  const response = await fetch(`${API_URL}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (response.status === 401) {
    clearToken();
    window.dispatchEvent(new Event("powertrace:unauthorized"));
  }
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new ApiError(errorMessage(data, response.status), response.status, data);
  }

  const disposition = response.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?([^";]+)"?/i);
  const filename = match?.[1] || "planta-powertrace.dxf";
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
