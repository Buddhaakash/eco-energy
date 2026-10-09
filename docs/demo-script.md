# Demo video script (~90 seconds)

## 0:00–0:10 — Hook (problem)
"Most homes and small offices have smart meters, but nobody actually reads
the data. Electricity gets wasted — a fan left running overnight, a faulty
fridge — and nobody notices until the bill arrives. EcoEnergy finds these
leaks automatically and tells you exactly what to fix."

## 0:10–0:55 — Walkthrough (solution)
1. Open the dashboard. Show the sidebar: tariff, budget, sensitivity.
2. Data tab → click "Load demo dataset". (~5s)
3. Overview tab → point at the 5 KPIs, then the timeline chart —
   highlight a shaded red region ("this is a detected leak").
4. Anomalies tab → open one finding, read the AI explanation out loud,
   mark it "Fixed" live to show the interactivity.
5. Savings Plan tab → show the ranked actions and the ₹ savings progress bar.
6. (Optional, if time) Ask AI tab → type "Why was my usage high last week?"
   and show the answer streaming in.

## 0:55–1:10 — Impact close
"Across this month of data, EcoEnergy found ₹X in avoidable electricity
cost — automatically, with zero setup beyond uploading a CSV. Scale this
to a hostel, a campus, or a whole apartment block, and the savings add up
fast, both in money and in carbon."

## 1:10–1:30 — Wrap
"Built with Python end-to-end — FastAPI backend, Streamlit dashboard, and
an AI layer that only explains numbers we've already calculated, so every
figure you see is verifiable. Thanks for watching."

## Recording tips
- Seed the demo dataset BEFORE recording (`python -m backend.seed`) so the
  dashboard is never empty on camera.
- If using the live-hosted link, open it 2-3 minutes early so a free-tier
  backend has time to wake up from sleep.
- Record at 1080p, keep the mouse movements slow and deliberate.
