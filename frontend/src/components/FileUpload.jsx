import { useState, useRef, useCallback } from "react";
import { Upload, X, Sparkles } from "lucide-react";
import "./FileUpload.css";

function formatBytes(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function FileUpload({ onSubmit, isLoading }) {
    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [dragOver, setDragOver] = useState(false);
    const inputRef = useRef(null);

    const handleFile = useCallback((f) => {
        if (!f || !f.type.startsWith("image/")) return;
        setFile(f);
        const reader = new FileReader();
        reader.onload = (e) => setPreview(e.target.result);
        reader.readAsDataURL(f);
    }, []);

    const handleDrop = (e) => {
        e.preventDefault();
        setDragOver(false);
        const f = e.dataTransfer.files[0];
        handleFile(f);
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        setDragOver(true);
    };

    const handleDragLeave = () => setDragOver(false);

    const handleRemove = () => {
        setFile(null);
        setPreview(null);
        if (inputRef.current) inputRef.current.value = "";
    };

    const handleSubmit = () => {
        if (file && onSubmit) onSubmit(file);
    };

    return (
        <div>
            <div
                className={`file-upload-zone ${dragOver ? "drag-over" : ""}`}
                onClick={() => inputRef.current?.click()}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
            >
                <input
                    ref={inputRef}
                    type="file"
                    accept="image/*"
                    onChange={(e) => handleFile(e.target.files[0])}
                />
                <div className="file-upload-icon">
                    <Upload size={24} />
                </div>
                <p className="file-upload-text">
                    Kliknij lub przeciągnij zdjęcie pojazdu
                </p>
                <p className="file-upload-hint">JPG, PNG, WebP — max 10 MB</p>
            </div>

            {file && preview && (
                <div className="file-upload-preview">
                    <img
                        src={preview}
                        alt="Podgląd"
                        className="file-upload-thumb"
                    />
                    <div className="file-upload-info">
                        <div className="file-upload-name">{file.name}</div>
                        <div className="file-upload-size">{formatBytes(file.size)}</div>
                    </div>
                    <button
                        className="file-upload-remove"
                        onClick={handleRemove}
                        disabled={isLoading}
                    >
                        <X size={18} />
                    </button>
                </div>
            )}

            {file && (
                <button
                    className="file-upload-submit"
                    onClick={handleSubmit}
                    disabled={!file || isLoading}
                >
                    {isLoading ? (
                        <>
                            <span className="spinner" />
                            Klasyfikuję…
                        </>
                    ) : (
                        <>
                            <Sparkles size={16} />
                            Klasyfikuj obraz
                        </>
                    )}
                </button>
            )}
        </div>
    );
}
