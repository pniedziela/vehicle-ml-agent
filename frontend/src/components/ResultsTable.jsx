import { motion } from "framer-motion";
import { Table, Database } from "lucide-react";
import "./ResultsTable.css";

function getBadgeClass(label) {
    if (!label) return "badge-other";
    if (label.includes("samochód") || label.includes("osobowy")) return "badge-car";
    if (label.includes("SUV") || label.includes("terenowy")) return "badge-suv";
    if (label.includes("ciężarówka")) return "badge-truck";
    if (label.includes("motocykl")) return "badge-moto";
    if (label.includes("autobus")) return "badge-bus";
    return "badge-other";
}

function formatValue(key, val) {
    if (val === null || val === undefined) return "—";
    if (key === "pewność_klasyfikacji") return `${(val * 100).toFixed(1)}%`;
    if (key === "cena" || key === "price") {
        return new Intl.NumberFormat("pl-PL", {
            style: "currency",
            currency: "PLN",
            maximumFractionDigits: 0,
        }).format(val);
    }
    return String(val);
}

export default function ResultsTable({ rows }) {
    if (!rows || rows.length === 0) {
        return (
            <div className="results-table-wrapper">
                <div className="results-empty">
                    <Database size={40} />
                    <p>Brak wyników do wyświetlenia</p>
                </div>
            </div>
        );
    }

    const columns = Object.keys(rows[0]);

    return (
        <motion.div
            className="results-table-wrapper"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
        >
            <div className="results-table-header">
                <h3>
                    <Table size={16} />
                    Wyniki zapytania
                </h3>
                <span className="results-count">{rows.length} rekordów</span>
            </div>
            <div className="results-table-scroll">
                <table className="results-table">
                    <thead>
                        <tr>
                            {columns.map((col) => (
                                <th key={col}>{col}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {rows.map((row, i) => (
                            <motion.tr
                                key={i}
                                initial={{ opacity: 0, x: -8 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ duration: 0.2, delay: i * 0.03 }}
                            >
                                {columns.map((col) => (
                                    <td key={col}>
                                        {col === "klasyfikacja_obrazu" ? (
                                            <span className={`badge ${getBadgeClass(row[col])}`}>
                                                {row[col] || "—"}
                                            </span>
                                        ) : (
                                            formatValue(col, row[col])
                                        )}
                                    </td>
                                ))}
                            </motion.tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </motion.div>
    );
}
