import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle } from "lucide-react";
import FileUpload from "../components/FileUpload";
import ClassificationCard from "../components/ClassificationCard";
import { classifyImage } from "../api/client";
import "./ClassifierView.css";

export default function ClassifierView() {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const handleSubmit = async (file) => {
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const res = await classifyImage(file);
            setResult(res);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="classifier-view">
            <div className="classifier-view-header">
                <h2>📷 Klasyfikator obrazów</h2>
                <p>
                    Prześlij zdjęcie pojazdu — model MobileNetV2 rozpozna jego typ.
                </p>
            </div>

            <FileUpload onSubmit={handleSubmit} isLoading={loading} />

            <AnimatePresence mode="wait">
                {error && (
                    <motion.div
                        className="classifier-error"
                        key="error"
                        initial={{ opacity: 0, y: -8 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                    >
                        <AlertTriangle size={18} />
                        {error}
                    </motion.div>
                )}

                {result && (
                    <motion.div
                        className="classifier-result-section"
                        key="result"
                        initial={{ opacity: 0, y: 12 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                    >
                        <ClassificationCard result={result} />
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
