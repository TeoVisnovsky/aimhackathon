# Local jury build

Run `python run.py` from the repository root. Open Gemini keys in the browser and save one to three keys supplied separately. The launcher installs dependencies, builds React, and serves both UI and API at http://127.0.0.1:8000.

The app starts without a patient. Import the supplied synthetic patient folder in the browser. Imported records persist in ignored `backend/.cache/imports/`; keep this folder private. The local server binds to 127.0.0.1 and has no authentication or user isolation. Do not expose the imported record as a public hosted demo.

Use `python run.py --skip-setup` for later starts. See the root README for the jury guide.
