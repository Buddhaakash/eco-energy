# EcoEnergy — AI Energy Leak Finder

**Problem statement:** Smart & Sustainable Future
**What it does:** A user uploads their electricity meter data (CSV) or lets the app
generate a realistic demo dataset. The app finds "energy leaks" — unusual spikes,
a device left running overnight, unusually high standby load — and turns each
finding into a plain-language, ranked action with an estimated ₹ saving. Everything
is done from a single dashboard.

## Why it matters
Most households and small offices have no idea where wasted electricity is going.
Smart meters produce data, but nobody reads it. This app turns raw kWh numbers into
a short list of "do this and save ₹X/month" actions, verified by AI narration on top
of real statistics (the numbers are computed in Python — the AI only explains them).

## Tech stack
- **Backend:** Python (FastAPI)
- **Frontend / Dashboard:** Python (Streamlit)
- **Database:** SQLite (via SQLAlchemy) — trivially swappable to Postgres
- **AI:** Google Gemini API (swap providers by editing one file:
  `backend/services/llm_client.py`)

## Project structure
See `docs/architecture.png` (add after first run) and the folder tree in the repo.

## Setup

```bash
git clone <your-repo-url>
cd eco-energy
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then paste your AI_API_KEY into .env

# generate demo data + load the database
python -m data.generate_demo_data
python -m backend.seed

# terminal 1
uvicorn backend.main:app --reload --port 8000

# terminal 2
streamlit run frontend/app.py
```

Open the Streamlit URL it prints (usually http://localhost:8501).

## Environment variables (`.env`)
```
AI_API_KEY=your_key_here
AI_MODEL=gemini-2.0-flash
DATABASE_URL=sqlite:///./eco_energy.db
API_URL=http://localhost:8000
```

## Submission checklist
- [ ] Project description (this README)
- [ ] GitHub repository (public)
- [ ] Demo video (~90s) — see `docs/demo-script.md`
- [ ] Live demo link (backend on Render, frontend on Streamlit Cloud)

## Impact estimate methodology
CO₂ and cost figures are estimates based on user-entered tariff and standard
grid emission factors — labelled as estimates throughout the app, not guarantees.
