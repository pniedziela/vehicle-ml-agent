import { useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Menu } from "lucide-react";
import Sidebar from "./components/Sidebar";
import AgentView from "./views/AgentView";
import ClassifierView from "./views/ClassifierView";
import LoginView from "./views/LoginView";
import { isAuthenticated } from "./api/client";
import "./App.css";

export default function App() {
    const [authed, setAuthed] = useState(isAuthenticated());
    const [sidebarOpen, setSidebarOpen] = useState(false);

    if (!authed) {
        return <LoginView onLogin={() => setAuthed(true)} />;
    }

    return (
        <BrowserRouter>
            <div className="app-layout">
                {/* Mobile overlay */}
                <div
                    className={`mobile-overlay ${sidebarOpen ? "visible" : ""}`}
                    onClick={() => setSidebarOpen(false)}
                />

                {/* Sidebar */}
                <div className={sidebarOpen ? "" : ""}>
                    <div className={sidebarOpen ? "sidebar-mobile-open" : ""}>
                        <Sidebar onLogout={() => setAuthed(false)} />
                    </div>
                </div>

                {/* Main content */}
                <main className="app-main">
                    {/* Mobile header */}
                    <div className="mobile-header">
                        <button
                            className="mobile-burger"
                            onClick={() => setSidebarOpen(!sidebarOpen)}
                        >
                            <Menu size={22} />
                        </button>
                        <h1>🚗 Vehicle ML Agent</h1>
                    </div>

                    <div className="app-content">
                        <Routes>
                            <Route path="/" element={<AgentView />} />
                            <Route path="/classify" element={<ClassifierView />} />
                        </Routes>
                    </div>
                </main>
            </div>
        </BrowserRouter>
    );
}
