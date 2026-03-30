import { NavLink } from "react-router-dom";
import { Bot, ImagePlus, LogOut } from "lucide-react";
import { useEffect, useState } from "react";
import { healthCheck, logout } from "../api/client";
import "./Sidebar.css";

export default function Sidebar({ onLogout }) {
    const [online, setOnline] = useState(null);

    useEffect(() => {
        healthCheck()
            .then(() => setOnline(true))
            .catch(() => setOnline(false));

        const interval = setInterval(() => {
            healthCheck()
                .then(() => setOnline(true))
                .catch(() => setOnline(false));
        }, 30000);

        return () => clearInterval(interval);
    }, []);

    function handleLogout() {
        logout();
        onLogout();
    }

    return (
        <aside className="sidebar">
            <div className="sidebar-logo">
                <div className="sidebar-logo-icon">🚗</div>
                <div>
                    <h1>Vehicle ML</h1>
                    <span>Agent Platform</span>
                </div>
            </div>

            <div className="sidebar-label">Narzędzia</div>

            <nav className="sidebar-nav">
                <NavLink
                    to="/"
                    end
                    className={({ isActive }) =>
                        `sidebar-link ${isActive ? "active" : ""}`
                    }
                >
                    <Bot />
                    Agent AI
                </NavLink>
                <NavLink
                    to="/classify"
                    className={({ isActive }) =>
                        `sidebar-link ${isActive ? "active" : ""}`
                    }
                >
                    <ImagePlus />
                    Klasyfikator
                </NavLink>
            </nav>

            <div className="sidebar-footer">
                <div className="sidebar-status">
                    <div
                        className={`sidebar-status-dot ${online === false ? "offline" : ""}`}
                    />
                    {online === null
                        ? "Łączenie…"
                        : online
                            ? "Backend online"
                            : "Backend offline"}
                </div>
                <button className="sidebar-logout" onClick={handleLogout} title="Wyloguj">
                    <LogOut size={15} />
                    Wyloguj
                </button>
            </div>
        </aside>
    );
}
