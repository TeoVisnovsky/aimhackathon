# Clinical Summary Desk

AIM Hackathon · Track 1: Clinical Documentation.
Enter a clinical role and task to find relevant patient facts, linked source passages, and contradictions.

## Setup

With **Python 3.12+**, **Node.js 22+** (including npm), and Git installed:

```sh
git clone https://github.com/TeoVisnovsky/aimhackathon.git
cd aimhackathon
python run.py
```

**Open Gemini keys in the app and paste the keys from the submission form:** one primary key and up to two optional backups. Click **Save Gemini keys**, then import the patient. Keys are masked and saved locally, excluded from Git. The backend tries another key on quota or key rejection; keys belonging to the same Google project share quota. Dependencies and the frontend build are handled automatically.

On macOS/Linux use `python3` if needed. The first run installs dependencies and builds the interface; setup and Gemini requests need internet access. Open **http://127.0.0.1:8000** when the server says `ready`. Stop with **Ctrl+C**.

Later starts: `python run.py --skip-setup`. To replace keys, open **Gemini keys** on the search screen. If a patient is already loaded, restart the app after saving. Terminal configuration is also available: `python run.py --skip-setup --configure-keys`. After pulling changes, run `python run.py` again. For a different port, add `--port 8001`.

## Jury guide

1. Click **Import patient folder** and select the supplied patient directory containing `patient.json` and `documents/`, not the entire challenge repository. No challenge data is included here.
2. Import starts processing immediately. Write your role and task below while it runs; the assessment button becomes available when import finishes. The first import builds the Gemini search index; quota limits can delay indexing.
3. Enter your role and task, or paste a challenge situation's title and description, and click **Generate assessment**.
4. Read the relevant facts and documentation status. Click a linked fact for its original passage; open a contradiction to compare its sources.
5. Use **New search** for another situation. The last imported patient is selected automatically; no name or date of birth entry is needed. Switch English/German in the header.

Imports are stored locally in ignored `backend/.cache/imports/` and survive restarts. A fresh clone starts without a patient. Use only synthetic data. Never commit patient folders, caches, prepared evidence, or patient-containing reports.

## Architecture and models

Gemini powers semantic retrieval (`gemini-embedding-001`) and checked ranking/summary calls (`gemini-flash-lite-latest`). Python rules build source-linked evidence during import (`blocks14/prep`). A role/task decision graph selects questions; the backend retrieves passages, checks polarity and chronology, and calculates supported values (`backend/app`). React displays results and citations (`frontend`). The Python server serves both the built interface and API.

Cloud requests pass through the de-identification gate. The jury launcher selects Gemini; no Claude or Ollama configuration is needed. If Gemini is unavailable or rate-limited, the backend can temporarily fall back to keyword retrieval and templates; a configured key does not guarantee that every request uses a model. Import extraction remains rules-based, so unsupported narrative facts may be missed. The supplied record is evaluated locally; no patient-containing reports are published. This prototype does not claim all challenge metrics are satisfied.

## Development checks

Use the Python interpreter in `backend/.venv` (`Scripts/python` on Windows; `bin/python` elsewhere):

```sh
cd backend
.venv/Scripts/python -m pytest -q
cd ../blocks14
../backend/.venv/Scripts/python -m pytest tests -q
cd ../frontend
npm test
npm run build
npm run lint
```

Based on the team implementation in [AIMhackathonTORU](https://github.com/ProgramHamza/AIMhackathonTORU). This repository contains the import-first jury build.
