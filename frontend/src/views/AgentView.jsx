import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Code, AlertTriangle } from "lucide-react";
import QueryInput from "../components/QueryInput";
import ResultsTable from "../components/ResultsTable";
import { askQuestion } from "../api/client";
import "./AgentView.css";

export default function AgentView() {
    const [loading, setLoading] = useState(false);
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

    const handleSubmit = async (question) => {
        setLoading(true);
        setError(null);
        setData(null);

        try {
            const res = await askQuestion(question);
            setData(res);
            if (res.error) {
                setError(res.error);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="agent-view">
            <div className="agent-view-header">
                <h2>🤖 Agent AI</h2>
                <p>
                    Zadaj pytanie o pojazdy — agent przetłumaczy je na SQL i doda
                    klasyfikację obrazów.
                </p>
            </div>

            <QueryInput onSubmit={handleSubmit} isLoading={loading} />

            <AnimatePresence mode="wait">
                {error && (
                    <motion.div
                        className="agent-error"
                        key="error"
                        initial={{ opacity: 0, y: -8 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                    >
                        <AlertTriangle size={18} />
                        {error}
                    </motion.div>
                )}

                {data && (
                    <motion.div
                        key="results"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                    >
                        {data.generated_sql && (
                            <div className="sql-section">
                                <div className="sql-label">
                                    <Code size={14} />
                                    Wygenerowane zapytanie SQL
                                </div>
                                <div className="sql-block">{data.generated_sql}</div>
                            </div>
                        )}

                        <ResultsTable rows={data.results} />
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
