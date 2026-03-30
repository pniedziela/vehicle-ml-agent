/**
 * API client — thin wrapper around fetch for backend communication.
 */

const API_BASE = "/api";

// ── Auth helpers ─────────────────────────────────────────────────────────────

export function getToken() {
    return localStorage.getItem("auth_token");
}

export function isAuthenticated() {
    return !!getToken();
}

export function logout() {
    localStorage.removeItem("auth_token");
}

function authHeaders() {
    const token = getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
}

/** Handle responses: throw on non-2xx, auto-logout on 401. */
async function handleResponse(res) {
    if (res.status === 401) {
        logout();
        window.location.reload();
        throw new Error("Sesja wygasła. Zaloguj się ponownie.");
    }
    if (res.status === 429) {
        throw new Error("Przekroczono limit zapytań. Spróbuj ponownie za chwilę.");
    }
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Błąd serwera (${res.status})`);
    }
    return res.json();
}

// ── Auth endpoints ───────────────────────────────────────────────────────────

/**
 * Log in and store the JWT token.
 * @param {string} username
 * @param {string} password
 */
export async function login(username, password) {
    const res = await fetch(`${API_BASE}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
    });
    if (res.status === 401) {
        throw new Error("Nieprawidłowa nazwa użytkownika lub hasło.");
    }
    if (!res.ok) {
        throw new Error(`Błąd serwera (${res.status})`);
    }
    const data = await res.json();
    localStorage.setItem("auth_token", data.access_token);
    return data;
}

// ── API endpoints ────────────────────────────────────────────────────────────

/**
 * Ask the AI Agent a question.
 * @param {string} question
 * @returns {Promise<{question, generated_sql, results, row_count, error}>}
 */
export async function askQuestion(question) {
    const res = await fetch(`${API_BASE}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ question }),
    });
    return handleResponse(res);
}

/**
 * Classify an image file.
 * @param {File} file
 * @returns {Promise<{predicted_class, confidence, imagenet_label}>}
 */
export async function classifyImage(file) {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch(`${API_BASE}/classify`, {
        method: "POST",
        headers: { ...authHeaders() },
        body: fd,
    });
    return handleResponse(res);
}

/**
 * Health check.
 * @returns {Promise<{status: string}>}
 */
export async function healthCheck() {
    const res = await fetch(`${API_BASE}/health`);
    return res.json();
}
