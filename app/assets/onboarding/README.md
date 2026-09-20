# FitVision pre-dashboard onboarding assets

These assets are ready to place under `app/assets/onboarding/`.

## Mapping

- `login_background.webp` → Sign-in screen
- `signup_background.webp` → Create-account screen
- `email_confirmation_background.webp` → Email confirmation screen
- `profile_setup_background.webp` → Onboarding step 1 / profile setup
- `limitations_background.webp` → Onboarding step 2 / movement limitations
- `profile_ready_background.webp` → Onboarding step 3 / profile ready
- `plan_generation_background.webp` → Plan generation/loading screen
- `final_transition_background.webp` → Final pre-dashboard loading/transition

## Intended use

Use these as background/hero artwork with a dark CSS overlay so Streamlit form controls remain readable. The files are WebP and can be loaded by the existing `asset_data_uri()` helper in `main.py`.

The existing dashboard, warm-up, trainer, workout, detector, metrics, persistence, and transition logic do not need these assets.
