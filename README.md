# 🚗 Vehicle ML Agent

Aplikacja łącząca **klasyfikację obrazów pojazdów** (MobileNetV2) z **agentem AI** tłumaczącym pytania w języku naturalnym na zapytania SQL.

> Zadanie rekrutacyjne – Machine Learning & AI Agent

---

## 📋 Spis treści

- [Architektura](#architektura)
- [Stack technologiczny](#stack-technologiczny)
- [Szybki start](#szybki-start)
- [Docker](#docker)
- [API](#api)
- [Struktura projektu](#struktura-projektu)
- [Decyzje architektoniczne](#decyzje-architektoniczne)
- [Testy](#testy)
- [Rozwój projektu](#rozwój-projektu)

---

## Architektura

```
┌──────────────────────────────────────────────────────┐
│                    Web UI / REST API                  │
│                     (FastAPI)                         │
├──────────────┬──────────────────┬────────────────────┤
│  POST /api/  │  POST /api/      │  GET /             │
│  classify    │  ask             │  (Web UI)          │
├──────────────┼──────────────────┼────────────────────┤
│  Classifier  │   AI Agent       │  Jinja2            │
│  Service     │   Service        │  Templates         │
│  (MobileNet  │   (OpenAI        │                    │
│   V2)        │    GPT-4o-mini)  │                    │
├──────────────┴──────────────────┴────────────────────┤
│               SQLite (dev) / PostgreSQL (prod)                │
│           + SQLAlchemy ORM (auto-detects driver)             │
│   vehicles │ owners │ transaction_history │ images   │
└──────────────────────────────────────────────────────┘
```

**Przepływ end-to-end:**

1. Użytkownik zadaje pytanie w języku naturalnym (np. *„Znajdź samochody Jana Kowalskiego"*)
2. Agent wysyła pytanie + schemat DB do GPT-4o-mini
3. GPT-4o-mini generuje zapytanie SQL SELECT
4. Aplikacja wykonuje SQL na bazie SQLite
5. Dla każdego pojazdu z wyników sprawdza, czy istnieje zdjęcie w `sample_images`/s3
6. Jeśli tak – uruchamia klasyfikator  EfficientNet-B0 i dodaje kolumnę z typem pojazdu
7. Zwraca wyniki jako tabelę JSON (API) lub HTML (Web UI)

---

## Stack technologiczny

| Komponent | Technologia | Uzasadnienie |
|-----------|------------|--------------|
| **Backend** | FastAPI + Uvicorn | Async, auto-docs Swagger, type hints |
| **Baza danych** | SQLite (dev) / PostgreSQL (prod) | SQLite: zero konfiguracji lokalnie. PostgreSQL: Railway plugin jednym kliknięciem |
| **Klasyfikator** |  EfficientNet-B0 (torchvision, pretrained) | Lekki, szybki inference bez GPU, ImageNet zawiera klasy pojazdów |
| **Agent AI** | OpenAI GPT-4o-mini | Najtańszy model OpenAI, wystarczający do generowania SQL |
| **Frontend** | Vanilla HTML/CSS/JS (Jinja2) | Brak dodatkowych zależności, szybki dev |
| **Konteneryzacja** | Docker + docker-compose | Jedno polecenie do uruchomienia |
| **Testy** | pytest | Unit + integration |

---

## Szybki start

### Wymagania

- Python 3.11+
- Klucz API OpenAI ([platform.openai.com](https://platform.openai.com))

### 1. Klonowanie i setup

```bash
git clone https://github.com/YOUR_USERNAME/vehicle-ml-agent.git
cd vehicle-ml-agent

# Virtualenv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Zależności
pip install -r requirements.txt
```

### 2. Konfiguracja

```bash
cp .env.example .env
# Edytuj .env i wstaw swój OPENAI_API_KEY
```

### 4. Uruchomienie

Backend: 
```bash
uvicorn app.main:app --reload
```

Otwórz **http://localhost:8000** w przeglądarce.

---

Frontend: 
```bash
cd frontend
npm install
npm run dev 
```

Otwórz **http://localhost:3000** w przeglądarce.


## Docker

```bash
# Ustaw klucz API
export OPENAI_API_KEY=sk-your-key-here

# Buduj i uruchom
docker-compose up --build

# Lub bez compose:
docker build -t vehicle-ml-agent .
docker run -p 8000:8000 -e OPENAI_API_KEY=$OPENAI_API_KEY vehicle-ml-agent
```

---

## Railway (Deploy do chmury)

Projekt jest przygotowany do deploymentu na [Railway](https://railway.app):


## API

Interaktywna dokumentacja Swagger: **http://localhost:8000/docs**

### POST `/api/ask` – Agent AI

Zadaj pytanie w języku naturalnym.

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Znajdź wszystkie samochody, których właścicielem był Jan Kowalski."}'
```

**Odpowiedź:**
```json
{
  "question": "Znajdź wszystkie samochody, których właścicielem był Jan Kowalski.",
  "generated_sql": "SELECT v.vehicle_id, v.brand AS marka, v.model AS model, v.year AS rok, v.price AS cena FROM vehicles v JOIN transaction_history t ON v.vehicle_id = t.vehicle_id JOIN owners o ON t.buyer_id = o.owner_id WHERE o.first_name = 'Jan' AND o.last_name = 'Kowalski'",
  "results": [
    {
      "vehicle_id": 1,
      "marka": "Toyota",
      "model": "Corolla",
      "rok": 2018,
      "cena": 45000.0,
      "klasyfikacja_obrazu": "samochód osobowy",
      "pewność_klasyfikacji": 0.7234,
      "etykieta_imagenet": "sports_car"
    }
  ],
  "row_count": 1,
  "error": null
}
```

### POST `/api/classify` – Klasyfikacja obrazu

Prześlij zdjęcie pojazdu.

```bash
curl -X POST http://localhost:8000/api/classify \
  -F "file=@sample_images/bmw_x5.jpg"
```

**Odpowiedź:**
```json
{
  "predicted_class": "samochód osobowy",
  "confidence": 0.8542,
  "imagenet_label": "sports_car"
}
```

### GET `/api/health` – Health check

```bash
curl http://localhost:8000/api/health
# {"status": "ok"}
```

---

## Struktura projektu

```
vehicle-ml-agent/
├── app/
│   ├── main.py                 # FastAPI entry point + lifespan
│   ├── config.py               # Pydantic settings (.env)
│   ├── api/
│   │   └── routes.py           # REST endpoints (/ask, /classify, /health)
│   ├── agent/
│   │   └── service.py          # NL→SQL agent (OpenAI GPT-4o-mini)
│   ├── classifier/
│   │   └── service.py          # EfficientNet-B0 image classifier
│   ├── db/
│   │   ├── models.py           # SQLAlchemy ORM models (4 tabele)
│   │   ├── session.py          # Async engine + session factory
│   │   └── seed.py             # Seed data 
│   └── templates/
│       └── index.html          # Web UI
├── tests/
│   ├── test_classifier.py      # Unit tests – klasyfikator
│   ├── test_agent.py           # Unit tests – agent (SQL safety)
│   └── test_api.py             # Integration tests – API endpoints
├── scripts/
│   └── download_images.py      # Pobieranie przykładowych zdjęć
├── sample_images/              # Zdjęcia pojazdów (git-ignored)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
├── .env.example
├── .gitignore
└── README.md
```

---

## Decyzje architektoniczne

### Dlaczego FastAPI?
- Natywny async – pasuje do async OpenAI client i async SQLAlchemy
- Automatyczna dokumentacja Swagger/OpenAPI
- Type hints + Pydantic = walidacja danych out-of-the-box
- Łatwe dodawanie middleware, CORS, auth w przyszłości

### Dlaczego SQLite?
- Zero konfiguracji – plik w repo, działa od razu
- Idealne do demo/MVP
- SQLAlchemy ORM = zamiana na PostgreSQL to zmiana jednej linii w `.env`

### Dlaczego EfficientNet-B0?
- Pretrained na ImageNet (1000 klas, w tym ~20 klas pojazdów)
- Lekki (~5.3M parametrów, ~20 MB wag) – szybki inference na CPU
- Wyższa dokładność niż MobileNetV2 przy podobnym rozmiarze modelu
- Oficjalnie wspierany przez torchvision
- Mapujemy klasy ImageNet na uproszczone kategorie (samochód, ciężarówka, motocykl, inne)

### Dlaczego GPT-4o-mini?
- Najtańszy model OpenAI (~$0.15/1M input tokens)
- Wystarczająca jakość do generowania SQL z prostego schematu
- Łatwa podmiana na inny model (zmiana `OPENAI_MODEL` w `.env`)

### Bezpieczeństwo SQL
- Agent generuje TYLKO zapytania SELECT
- Walidacja: regex sprawdza obecność niebezpiecznych słów kluczowych (DROP, DELETE, INSERT, PRAGMA, ATTACH, itp.)
- Blokowanie komentarzy SQL (`--`, `/*`) – zapobiega ukrywaniu payloadów
- Blokowanie wielokrotnych zapytań (`;`) – zapobiega SQL injection
- Automatyczne usuwanie trailing semicolons z odpowiedzi LLM
- ⚠️ **Uwaga**: zapytania są wykonywane jako raw SQL via `text()` – w produkcji zalecane jest dodanie dodatkowej warstwy walidacji (np. parsowanie AST SQL)

---

## Testy

```bash
# Wszystkie testy
pytest -v

# Tylko klasyfikator
pytest tests/test_classifier.py -v

# Tylko agent
pytest tests/test_agent.py -v

# Tylko API
pytest tests/test_api.py -v
```

---

## Rozwój projektu

- **Podmiana bazy danych** – zmiana `DATABASE_URL` na PostgreSQL/MySQL
- **Podmiana LLM** – zmiana `OPENAI_MODEL` lub refaktor na innego providera (Claude, Ollama)
- **Lepszy klasyfikator** – fine-tuning na dedykowanym datasecie pojazdów
- **Autoryzacja** – dodanie JWT/OAuth2 middleware w FastAPI
- **CI/CD** – GitHub Actions z testami i budowaniem Dockera
- **Monitoring** – Prometheus metrics, structured logging
- **Cache** – Redis cache dla powtarzających się zapytań SQL
- **Alembic** – migracje schematu bazy danych

---

