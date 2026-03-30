import { useState } from "react";
import { Send } from "lucide-react";
import "./QueryInput.css";

const EXAMPLES = [
    "Znajdź wszystkie samochody, których właścicielem był Jan Kowalski.",
    "Pokaż pojazdy droższe niż 100000 zł.",
    "Kto kupił BMW X5?",
    "Wyświetl historię transakcji z 2021 roku.",
    "Ile pojazdów jest dostępnych?",
    "Pokaż wszystkie motocykle.",
];

export default function QueryInput({ onSubmit, isLoading }) {
    const [value, setValue] = useState("");

    const handleSubmit = () => {
        const q = value.trim();
        if (!q || isLoading) return;
        onSubmit(q);
    };

    const handleKeyDown = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    return (
        <div className="query-input-wrapper">
            <div className="query-input-bar">
                <input
                    type="text"
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Zadaj pytanie o pojazdy w języku naturalnym…"
                    disabled={isLoading}
                />
                <button
                    className="query-send-btn"
                    onClick={handleSubmit}
                    disabled={!value.trim() || isLoading}
                >
                    {isLoading ? (
                        <>
                            <span className="spinner" />
                            Przetwarzam…
                        </>
                    ) : (
                        <>
                            <Send size={16} />
                            Zapytaj
                        </>
                    )}
                </button>
            </div>

            <div className="query-examples">
                <div className="query-examples-label">Przykładowe pytania</div>
                <div className="query-chips">
                    {EXAMPLES.map((ex) => (
                        <button
                            key={ex}
                            className="query-chip"
                            onClick={() => setValue(ex)}
                            disabled={isLoading}
                        >
                            {ex}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}
