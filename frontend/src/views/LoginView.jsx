import { useState } from "react";
import { LogIn } from "lucide-react";
import { login } from "../api/client";
import "./LoginView.css";

export default function LoginView({ onLogin }) {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    async function handleSubmit(e) {
        e.preventDefault();
        setError(null);
        setLoading(true);
        try {
            await login(username, password);
            onLogin();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="login-wrapper">
            <div className="login-card">
                <div className="login-logo">🚗</div>
                <h1 className="login-title">Vehicle ML Agent</h1>
                <p className="login-subtitle">Zaloguj się, aby kontynuować</p>

                <form className="login-form" onSubmit={handleSubmit}>
                    <div className="login-field">
                        <label htmlFor="username">Użytkownik</label>
                        <input
                            id="username"
                            type="text"
                            autoComplete="username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="recruiter"
                            required
                            disabled={loading}
                        />
                    </div>

                    <div className="login-field">
                        <label htmlFor="password">Hasło</label>
                        <input
                            id="password"
                            type="password"
                            autoComplete="current-password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                            required
                            disabled={loading}
                        />
                    </div>

                    {error && <div className="login-error">{error}</div>}

                    <button className="login-btn" type="submit" disabled={loading}>
                        <LogIn size={16} />
                        {loading ? "Logowanie…" : "Zaloguj się"}
                    </button>
                </form>
            </div>
        </div>
    );
}
