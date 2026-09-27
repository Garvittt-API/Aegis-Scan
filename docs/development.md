# AegisScan — Local Development Guide

## 1. Local Setup

### Backend Setup (Python 3.12)
```bash
# 1. Create and activate virtual environment
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate
# On Windows PowerShell:
.venv\Scripts\Activate.ps1

# 2. Install backend dependencies
pip install -r backend/requirements.txt

# 3. Start development API server
cd backend
python -m app.main
```
Backend API will be accessible at: `http://127.0.0.1:8000` (API Docs: `http://127.0.0.1:8000/api/docs`)

---

### Frontend Setup (React / Vite)
```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite hot-reloading dev server
npm run dev
```
Frontend Web UI will be accessible at: `http://localhost:5173`

---

## 2. Running Automated Tests

Run the full pytest suite:
```bash
pytest backend/tests -v
```

Run test suite with code coverage:
```bash
pytest backend/tests --cov=app --cov-report=term-missing
```

---

## 3. Running Local CI Policy Scan

Run the standalone CLI scanner locally against any authorized project or source directory:
```bash
cd backend
python -m app ci \
  --target . \
  --policy ../security-policy.example.yaml \
  --format json,sarif,html \
  --output ../artifacts
```

---

## 4. Code Formatting & Linting

```bash
# Frontend ESLint
cd frontend
npm run lint

# Python tests
pytest backend/tests
```
