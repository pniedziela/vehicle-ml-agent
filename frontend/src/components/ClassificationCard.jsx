import { motion } from "framer-motion";
import "./ClassificationCard.css";

function getBadgeClass(label) {
    if (!label) return "badge-other";
    if (label.includes("samochód") || label.includes("osobowy")) return "badge-car";
    if (label.includes("SUV") || label.includes("terenowy")) return "badge-suv";
    if (label.includes("ciężarówka")) return "badge-truck";
    if (label.includes("motocykl")) return "badge-moto";
    if (label.includes("autobus")) return "badge-bus";
    return "badge-other";
}

const CIRCUMFERENCE = 2 * Math.PI * 54; // radius = 54

export default function ClassificationCard({ result }) {
    if (!result) return null;

    const { predicted_class, confidence, imagenet_label } = result;
    const pct = Math.round(confidence * 100);
    const offset = CIRCUMFERENCE - confidence * CIRCUMFERENCE;

    const ringClass =
        confidence >= 0.7 ? "high" : confidence >= 0.4 ? "medium" : "low";

    return (
        <motion.div
            className="classification-card"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.35 }}
        >
            <div className="classification-card-inner">
                <div className="confidence-ring-wrapper">
                    <svg className="confidence-ring" viewBox="0 0 120 120">
                        <circle
                            className="confidence-ring-bg"
                            cx="60"
                            cy="60"
                            r="54"
                        />
                        <circle
                            className={`confidence-ring-fill ${ringClass}`}
                            cx="60"
                            cy="60"
                            r="54"
                            strokeDasharray={CIRCUMFERENCE}
                            strokeDashoffset={offset}
                        />
                    </svg>
                    <div className="confidence-value">{pct}%</div>
                </div>
                <div className="confidence-label">Pewność klasyfikacji</div>

                <div className="classification-details">
                    <div className="classification-row">
                        <span className="classification-row-label">Typ pojazdu</span>
                        <span className="classification-row-value">
                            <span className={`badge ${getBadgeClass(predicted_class)}`}>
                                {predicted_class}
                            </span>
                        </span>
                    </div>
                    <div className="classification-row">
                        <span className="classification-row-label">Etykieta ImageNet</span>
                        <span className="classification-row-value">{imagenet_label}</span>
                    </div>
                    <div className="classification-row">
                        <span className="classification-row-label">Pewność</span>
                        <span className="classification-row-value">
                            {(confidence * 100).toFixed(1)}%
                        </span>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
