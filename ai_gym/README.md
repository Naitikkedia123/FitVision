# AI GYM — Workout Execution Engine

This directory contains the AI GYM computer-vision workout execution module.

## Current role

The AI GYM module is responsible for:

- MediaPipe pose processing
- Exercise detectors
- Rep counting
- Form metrics
- Real-time coaching
- WebRTC camera execution

Personalized exercise selection, dosage, scheduling, user profiles, and Supabase persistence belong to the separate `fitness_predictor` module during integration.

## Local setup

Create a virtual environment and install:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add the required local secrets.

Do not commit `.env`, local databases, or virtual environments.
