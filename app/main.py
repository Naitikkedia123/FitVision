from pathlib import Path
from textwrap import dedent
import sys
import time
from datetime import date
from functools import lru_cache
from html import escape
import base64

import streamlit as st
# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
FITNESS_PREDICTOR_DIR = PROJECT_ROOT / "fitness_predictor"

for path in (PROJECT_ROOT, FITNESS_PREDICTOR_DIR):
    path_str = str(path)

    if path_str not in sys.path:
        sys.path.insert(0, path_str)


from services.auth_service import AuthService
from services.fitness_profile_service import FitnessProfileService
from services.user_limitation_service import UserLimitationService
from database.client import (
    get_supabase_client,
    set_authenticated_session,
)
from models.user_profile import UserProfile
from rules.eligibility import EligibilityService
from services.four_week_plan_service import FourWeekPlanService
from services.plan_persistence_service import PlanPersistenceService
from services.dashboard_service import DashboardService
from data.exercise_catalog import EXERCISES
from ai_gym.services.execution.workout_controller import WorkoutCommand
from ai_gym.services.execution.workout_runner import render_workout_runner
from integration.workout_adapter import (
    adapt_workout_exercise,
    is_workout_exercise_executable,
)
from ai_gym.services.tracking.metrics import sync_metrics_update
from ai_gym.services.config.workout_config import METRICS_FIELDS
from shared.exercise_mapping import get_trainer_exercise_type

THEME_PATH = APP_DIR / "styles" / "theme.css"

ASSET_DIR = APP_DIR / "assets"

EXERCISE_ASSET_IDS = {
    "march_in_place": "march_in_place",
    "wall_sit": "wall_sit",
    "plank": "plank",
    "standing_knee_raise": "standing_knee_raise",
    "low_impact_jumping_jack": "low_impact_jumping_jack",
    "bodyweight_squat": "bodyweight_squat",
    "reverse_lunge": "reverse_lunge",
    "standing_side_leg_raise": "standing_side_leg_raise",
    "hamstring_curl": "hamstring_curl",
    "hip_extension": "hip_extension",
    "calf_raise": "calf_raise",
    "glute_bridge": "glute_bridge",
    "sit_to_stand": "sit_to_stand",
    "wall_push_up": "wall_push_up",
    "knee_push_up": "knee_push_up",
    "standard_push_up": "standard_push_up",
    "shoulder_press": "shoulder_press",
    "biceps_curl": "biceps_curl",
}


@lru_cache(maxsize=64)
def asset_data_uri(relative_path: str) -> str:
    """Return a local app asset as a browser-safe data URI."""
    path = ASSET_DIR / relative_path

    if not path.exists():
        return ""

    mime = "image/webp" if path.suffix.lower() == ".webp" else "image/png"

    encoded = base64.b64encode(
        path.read_bytes()
    ).decode("ascii")

    return f"data:{mime};base64,{encoded}"


def exercise_image_uri(exercise_id: str) -> str:
    asset_id = EXERCISE_ASSET_IDS.get(
        exercise_id,
        exercise_id,
    )

    return asset_data_uri(
        f"exercises/{asset_id}.webp"
    )


def ui_action_is_locked(
    action_key: str,
    cooldown_seconds: float = 0.9,
) -> bool:
    """
    One-shot guard against rapid repeated clicks across Streamlit reruns.
    Returns True when the same action was fired too recently.
    """
    now = time.monotonic()

    last_actions = st.session_state.setdefault(
        "_ui_action_last_at",
        {},
    )

    previous = float(
        last_actions.get(action_key, 0.0)
    )

    if now - previous < cooldown_seconds:
        return True

    last_actions[action_key] = now

    return False


def clear_warmup_setup_state() -> None:
    """Clear warm-up setup state without touching persisted workout data."""
    for key in (
        "warmup_mode",
        "warmup_exercise",
        "warmup_target_sets",
        "warmup_target_reps",
        "warmup_target_duration_seconds",
    ):
        st.session_state.pop(key, None)


def render_product_sidebar(
    active: str,
    *,
    navigation_locked: bool = False,
) -> None:
    """Render the authenticated product navigation.

    The visual sidebar remains pure HTML/CSS. A single fixed Streamlit
    action host contains the three real buttons so the navigation stays
    functional without creating multiple fixed Streamlit blocks in the
    normal document flow.
    """
    logo_uri = asset_data_uri("brand/logo.webp")

    nav_items = [
        ("dashboard", "Dashboard", "⌂"),
        ("workout_plan", "Workout Plan", "▣"),
        ("warmup", "Warm-up", "◉"),
    ]

    nav_html = []
    for _, label, icon in nav_items:
        active_class = " active" if label == active else ""
        nav_html.append(
            f"""
            <div class="fv-side-nav-item{active_class}">
                <span class="fv-side-nav-icon">{icon}</span>
                <span>{escape(label)}</span>
            </div>
            """
        )

    render_html(
        f"""
        <aside class="fv-app-sidebar">
            <div class="fv-sidebar-brand">
                <img
                    src="{logo_uri}"
                    alt="FitVision"
                    class="fv-sidebar-logo"
                />
            </div>

            <nav class="fv-side-nav">
                {''.join(nav_html)}
            </nav>

            <div class="fv-sidebar-spacer"></div>
            <div class="fv-sidebar-motivation" aria-hidden="true"></div>
        </aside>

        <div class="fv-mobile-brand">
            <span class="fv-mobile-brand-mark">FV</span>
            <span class="fv-mobile-brand-name">FITVISION</span>
            <span class="fv-mobile-brand-sub">AI GYM</span>
        </div>
        """
    )

    if navigation_locked:
        return

    # Keep the real Streamlit navigation buttons inside one keyed host.
    # The stylesheet targets this exact host via Streamlit's key class, so
    # there is no fragile :has() selector or browser navigation involved.
    with st.container(key="sidebar-actions-host"):
        for action_key, label, _ in nav_items:
            clicked = st.button(
                label,
                key=f"sidebar_{action_key}",
                use_container_width=True,
            )

            if not clicked:
                continue

            if ui_action_is_locked(
                f"sidebar_{action_key}",
                cooldown_seconds=0.65,
            ):
                return

            if action_key == "warmup":
                if active == "Warm-up":
                    return

                st.session_state["sidebar_page"] = "Warm-up"
                request_workout_transition(
                    screen="warmup",
                    message="Preparing your warm-up...",
                )
                return

            st.session_state.pop(
                "dashboard_selected_day_number",
                None,
            )

            if active == "Warm-up":
                clear_warmup_setup_state()
                st.session_state["workout_started"] = False
                st.session_state["returning_from_workout"] = True

            st.session_state["sidebar_page"] = (
                "Dashboard"
                if action_key == "dashboard"
                else "Workout Plan"
            )

            request_workout_transition(
                screen="dashboard",
                message=(
                    "Returning to your workout plan..."
                    if active == "Warm-up"
                    else "Loading your workout plan..."
                ),
            )
            return


# ---------------------------------------------------------
# HTML helper
# ---------------------------------------------------------

def render_html(html: str) -> None:
    """Render custom HTML directly through Streamlit's HTML API."""
    st.html(dedent(html))


# ---------------------------------------------------------
# Theme
# ---------------------------------------------------------

def load_theme() -> None:
    css = THEME_PATH.read_text(encoding="utf-8")
    st.html(f"<style>{css}</style>")


def render_transition_layer() -> None:
    """Render a short visual layer during workout/warm-up screen changes."""
    message = st.session_state.pop(
        "_screen_transition_message",
        None,
    )

    if not message:
        return

    render_html(
        f"""
        <style>
            @keyframes fv-transition-in {{
                from {{
                    opacity: 0;
                }}
                to {{
                    opacity: 1;
                }}
            }}

            @keyframes fv-transition-out {{
                0%,
                72% {{
                    opacity: 1;
                    visibility: visible;
                }}
                100% {{
                    opacity: 0;
                    visibility: hidden;
                }}
            }}

            .fv-screen-transition {{
                position: fixed !important;
                inset: 0 !important;
                z-index: 2147483647 !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                flex-direction: column !important;
                gap: 18px !important;
                background: #070707 !important;
                color: #ffffff !important;
                animation:
                    fv-transition-in 120ms ease-out,
                    fv-transition-out 720ms ease-in 120ms forwards !important;
                pointer-events: auto !important;
            }}

            .fv-transition-brand {{
                font-size: 13px !important;
                font-weight: 700 !important;
                letter-spacing: 0.22em !important;
                opacity: 0.72 !important;
            }}

            .fv-transition-message {{
                font-size: 20px !important;
                font-weight: 600 !important;
                letter-spacing: 0.02em !important;
            }}

            .fv-transition-dots {{
                display: flex !important;
                align-items: center !important;
                gap: 7px !important;
                height: 14px !important;
            }}

            .fv-transition-dot {{
                width: 7px !important;
                height: 7px !important;
                border-radius: 50% !important;
                background: var(--fv-accent, #d7ff4f) !important;
                animation: fv-dot-pulse 900ms ease-in-out infinite !important;
            }}

            .fv-transition-dot:nth-child(2) {{
                animation-delay: 150ms !important;
            }}

            .fv-transition-dot:nth-child(3) {{
                animation-delay: 300ms !important;
            }}

            @keyframes fv-dot-pulse {{
                0%,
                100% {{
                    opacity: 0.25;
                    transform: translateY(0);
                }}
                50% {{
                    opacity: 1;
                    transform: translateY(-3px);
                }}
            }}
        </style>

        <div class="fv-screen-transition">
            <div class="fv-transition-brand">
                FITVISION
            </div>

            <div class="fv-transition-message">
                {message}
            </div>

            <div class="fv-transition-dots" aria-hidden="true">
                <span class="fv-transition-dot"></span>
                <span class="fv-transition-dot"></span>
                <span class="fv-transition-dot"></span>
            </div>
        </div>
        """
    )


def request_workout_transition(
    screen: str,
    message: str,
) -> None:
    """Queue a visual transition, then perform the normal screen rerun."""

    st.session_state["_screen_transition_message"] = message
    st.session_state["screen"] = screen

    st.rerun()

def user_has_fitness_profile(user_id: str) -> bool:
    service = FitnessProfileService()
    return service.get_profile(user_id) is not None

def user_has_workout_plan(user_id: str) -> bool:
    from database.repositories.workout_plan_repository import WorkoutPlanRepository

    repository = WorkoutPlanRepository()
    return repository.get_active_plan(user_id) is not None

def calculate_age(date_of_birth: date) -> int:
    today = date.today()

    age = today.year - date_of_birth.year

    if (
        today.month,
        today.day,
    ) < (
        date_of_birth.month,
        date_of_birth.day,
    ):
        age -= 1

    return age

def build_user_profile(user_id: str) -> UserProfile:
    profile_service = FitnessProfileService()
    limitation_service = UserLimitationService()

    from database.client import get_supabase_client

    client = get_supabase_client()

    try:
        current_user = client.auth.get_user().user
    except Exception as exc:
        st.write("DEBUG AUTH ERROR:", repr(exc))

    profile = profile_service.get_profile(user_id)

    profile = profile_service.get_profile(user_id)

    if profile is None:
        raise ValueError(
            "Fitness profile could not be found for this user."
        )

    date_of_birth = date.fromisoformat(
        profile["date_of_birth"]
    )

    age = calculate_age(date_of_birth)

    limitations = limitation_service.get_limitations(
        user_id
    )

    user = UserProfile(
        age=age,
        sex=profile["sex"],
        height_cm=float(profile["height_cm"]),
        weight_kg=float(profile["weight_kg"]),
        fitness_level=int(profile["fitness_level"]),
        activity_level=int(profile["activity_level"]),
        goal=profile["goal"],
        workout_time_min=int(profile["workout_time_min"]),
        limitations=limitations,
        user_id=user_id,
    )

    user.validate()

    return user

def generate_and_save_plan(user_id: str) -> dict:
    """
    Build the user's validated profile, determine eligible exercises,
    generate the four-week plan, and persist it to Supabase.
    """

    user = build_user_profile(user_id)

    eligibility_service = EligibilityService()

    eligible_exercises = (
        eligibility_service.get_eligible_exercises(user)
    )

    if not eligible_exercises:
        raise ValueError(
            "No suitable exercises are available for your "
            "current fitness profile and movement limitations."
        )

    plan_service = FourWeekPlanService()

    four_week_plan = plan_service.generate(
        user=user,
        eligible_exercises=eligible_exercises,
    )

    persistence_service = PlanPersistenceService()

    saved_plan = persistence_service.save_plan(
        user=user,
        four_week_plan=four_week_plan,
        start_date=date.today(),
    )

    return saved_plan
# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def handle_authenticated_user(result: dict) -> None:
    session = result.get("session")

    if session is not None:
        set_authenticated_session(
            session.access_token,
            session.refresh_token,
        )

    st.session_state["authenticated"] = True
    st.session_state["user_id"] = result["user_id"]
    st.session_state["user_email"] = result["email"]
    st.session_state["sidebar_page"] = "Dashboard"
    st.session_state.pop("dashboard_selected_day_number", None)

    st.session_state.pop(
        "dashboard_plan_cache",
        None,
    )

    st.session_state.pop(
        "onboarding_step",
        None,
    )

    st.session_state.pop(
        "pending_confirmation_email",
        None,
    )

    st.session_state.pop(
        "confirmation_resend_available_at",
        None,
    )

    st.session_state.pop(
        "screen",
        None,
    )

    st.rerun()

def sign_out_user() -> None:
    """
    Sign the user out from Supabase and clear all
    authentication/workout session state.
    """

    try:
        client = get_supabase_client()
        client.auth.sign_out()
    except Exception:
        # Even if the remote session is already invalid,
        # clear the local Streamlit session.
        pass

    # Authentication state
    st.session_state["authenticated"] = False

    st.session_state.pop(
        "dashboard_plan_cache",
        None,
    )

    st.session_state.pop(
        "user_id",
        None,
    )

    st.session_state.pop(
        "user_email",
        None,
    )

    st.session_state.pop(
        "sidebar_page",
        None,
    )

    # Navigation / onboarding state
    st.session_state.pop(
        "screen",
        None,
    )

    st.session_state.pop(
        "onboarding_step",
        None,
    )

    st.session_state.pop(
        "returning_from_workout",
        None,
    )

    st.session_state.pop(
        "dashboard_plan_cache",
        None,
    )

    # Active workout state
    st.session_state.pop(
        "active_workout_command",
        None,
    )

    st.session_state.pop(
        "active_workout_exercise_id",
        None,
    )

    st.session_state.pop(
        "active_workout_exercise",
        None,
    )

    st.session_state.pop(
        "_active_workout_command",
        None,
    )

    st.session_state["workout_started"] = False

    # Progress cache
    st.session_state.pop(
        "_progress_loaded_for_exercise",
        None,
    )

    st.session_state.pop(
        "_persisted_completed_sets",
        None,
    )

    st.session_state.pop(
        "last_saved_sets_completed",
        None,
    )

    # Return to authentication screen
    st.session_state["auth_mode"] = "signin"

    st.rerun()

def is_email_not_confirmed_error(exc: Exception) -> bool:
    message = str(exc).strip().lower()

    return (
        "email not confirmed" in message
        or "email_not_confirmed" in message
    )


# ---------------------------------------------------------
# Authentication home
# ---------------------------------------------------------

def render_auth_home() -> None:
    auth_service = AuthService()

    if "auth_mode" not in st.session_state:
        st.session_state["auth_mode"] = "signin"

    left_col, right_col = st.columns(
        [1.15, 0.85],
        gap="large",
    )

    # =====================================================
    # LEFT
    # =====================================================

    with left_col:

        render_html(
            """
            <div class="fv-auth-left">

                <div class="fv-auth-kicker">
                    FITVISION / ACCOUNT
                </div>

                <h1 class="fv-auth-title">
                    Your training<br>
                    <span class="fv-auth-title-accent">
                        starts here.
                    </span>
                </h1>

                <div class="fv-accent-line"></div>

                <div class="fv-auth-description">
                    Your workouts are built around your body, your
                    goals, and your current ability. Sign in to
                    continue your personalized training journey.
                </div>

                <div class="fv-auth-feature-list">

                    <div class="fv-auth-feature">
                        <div class="fv-auth-feature-index">
                            01
                        </div>

                        <div>
                            <div class="fv-auth-feature-title">
                                Personalized programming
                            </div>

                            <div class="fv-auth-feature-text">
                                Structured training generated from your
                                fitness profile and goals.
                            </div>
                        </div>
                    </div>

                    <div class="fv-auth-feature">
                        <div class="fv-auth-feature-index">
                            02
                        </div>

                        <div>
                            <div class="fv-auth-feature-title">
                                Real-time movement coaching
                            </div>

                            <div class="fv-auth-feature-text">
                                Exercise execution powered by pose
                                analysis and AI coaching.
                            </div>
                        </div>
                    </div>

                    <div class="fv-auth-feature">
                        <div class="fv-auth-feature-index">
                            03
                        </div>

                        <div>
                            <div class="fv-auth-feature-title">
                                Progress that stays with you
                            </div>

                            <div class="fv-auth-feature-text">
                                Your plan and workout progress are stored
                                with your account.
                            </div>
                        </div>
                    </div>

                </div>

            </div>
            """
        )

    # =====================================================
    # RIGHT
    # =====================================================

    with right_col:

        render_html(
            """
            <div class="fv-auth-right">

                <div class="fv-auth-card">

                    <div class="fv-auth-card-label">
                        ACCOUNT ACCESS
                    </div>

                    <div class="fv-auth-card-title">
                        Continue with FitVision
                    </div>

                    <div class="fv-auth-card-subtitle">
                        Access your personalized training workspace.
                    </div>

                </div>

            </div>
            """
        )

        mode_col1, mode_col2 = st.columns(
            2,
            gap="small",
        )

        with mode_col1:

            if st.button(
                "SIGN IN",
                key="auth_signin_mode",
                type=(
                    "primary"
                    if st.session_state["auth_mode"] == "signin"
                    else "secondary"
                ),
                use_container_width=True,
            ):
                if st.session_state["auth_mode"] != "signin":
                    st.session_state["auth_mode"] = "signin"
                    st.rerun()

        with mode_col2:

            if st.button(
                "CREATE ACCOUNT",
                key="auth_signup_mode",
                type=(
                    "primary"
                    if st.session_state["auth_mode"] == "signup"
                    else "secondary"
                ),
                use_container_width=True,
            ):
                if st.session_state["auth_mode"] != "signup":
                    st.session_state["auth_mode"] = "signup"
                    st.rerun()

        st.divider()

        # =================================================
        # SIGN IN
        # =================================================

        if st.session_state["auth_mode"] == "signin":

            render_html(
                """
                <div class="fv-auth-section-label">
                    WELCOME BACK
                </div>
                """
            )

            email = st.text_input(
                "Email",
                placeholder="you@example.com",
                key="login_email",
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Your password",
                key="login_password",
            )

            st.write("")

            if st.button(
                "SIGN IN →",
                key="signin_button",
                type="primary",
                use_container_width=True,
            ):

                if not email.strip() or not password:
                    st.error(
                        "Please enter your email and password."
                    )

                else:

                    try:

                        result = auth_service.sign_in(
                            email=email,
                            password=password,
                        )

                        handle_authenticated_user(result)

                    except Exception as exc:

                        if is_email_not_confirmed_error(exc):
                            st.error(
                                "Your email is not confirmed yet. "
                                "Please check your inbox and confirm "
                                "your account before signing in."
                            )
                        else:
                            st.error(str(exc))

            render_html(
                """
                <div class="fv-auth-note">
                    Your account uses the existing FitVision
                    authentication service.
                </div>
                """
            )

        # =================================================
        # SIGN UP
        # =================================================

        else:

            render_html(
                """
                <div class="fv-auth-section-label">
                    NEW TO FITVISION
                </div>
                """
            )

            full_name = st.text_input(
                "Full name",
                placeholder="Your name",
                key="signup_name",
            )

            signup_email = st.text_input(
                "Email",
                placeholder="you@example.com",
                key="signup_email",
            )

            signup_password = st.text_input(
                "Password",
                type="password",
                placeholder="At least 6 characters",
                key="signup_password",
            )

            st.write("")

            if st.button(
                "CREATE ACCOUNT →",
                key="signup_button",
                type="primary",
                use_container_width=True,
            ):

                if (
                    not signup_email.strip()
                    or not signup_password
                ):

                    st.error(
                        "Email and password are required."
                    )

                elif len(signup_password) < 6:

                    st.error(
                        "Password must contain at least 6 characters."
                    )

                else:

                    email_value = signup_email.strip().lower()

                    try:

                        result = auth_service.sign_up(
                            email=email_value,
                            password=signup_password,
                            full_name=full_name or None,
                        )

                        # -------------------------------------------------
                        # Brand-new signup with immediate session.
                        # -------------------------------------------------

                        if result["session"] is not None:

                            handle_authenticated_user(result)

                        else:

                            # Signup succeeded, but Supabase returned no session.
                            # This is the expected state when email confirmation
                            # is enabled.
                            st.session_state[
                                "pending_confirmation_email"
                            ] = email_value

                            st.session_state[
                                "confirmation_resend_available_at"
                            ] = time.time() + 60

                            st.session_state[
                                "screen"
                            ] = "email_confirmation"

                            st.rerun()

                    except Exception as exc:

                        message = str(exc)

                        # Clear, actionable duplicate-account message.
                        if (
                            "user already registered"
                            in message.lower()
                        ):

                            st.warning(
                                "An account already exists for this "
                                "email address. Use SIGN IN instead."
                            )

                        elif (
                            "rate limit" in message.lower()
                            or "too many requests" in message.lower()
                            or "60" in message.lower()
                        ):

                            st.warning(
                                "Too many signup attempts were made. "
                                "Please wait a moment before trying again."
                            )

                        else:

                            st.error(
                                message
                            )


# ---------------------------------------------------------
# Live confirmation actions
# ---------------------------------------------------------

@st.fragment(run_every=1)
def render_confirmation_actions(
    email: str,
) -> None:

    auth_service = AuthService()

    available_at = st.session_state.get(
        "confirmation_resend_available_at",
        0,
    )

    remaining = max(
        0,
        int(
            available_at - time.time()
        ),
    )

    if remaining > 0:

        st.button(
            f"RESEND EMAIL · {remaining}s",
            disabled=True,
            use_container_width=True,
            key="resend_confirmation_disabled",
        )

        render_html(
            """
            <div class="fv-confirmation-note">
                Please wait before requesting another confirmation email.
            </div>
            """
        )

        return

    if st.button(
        "RESEND CONFIRMATION EMAIL",
        type="primary",
        use_container_width=True,
        key="resend_confirmation",
    ):

        try:

            auth_service.resend_signup_confirmation(
                email
            )

            st.session_state[
                "confirmation_resend_available_at"
            ] = time.time() + 60

            st.success(
                "A new confirmation email has been sent."
            )

        except Exception as exc:

            st.error(
                str(exc)
            )


# ---------------------------------------------------------
# Email confirmation
# ---------------------------------------------------------

def render_email_confirmation() -> None:

    email = st.session_state.get(
        "pending_confirmation_email",
        "",
    )

    if not email:

        st.session_state["auth_mode"] = "signin"
        st.rerun()
        return

    left_spacer, center, right_spacer = st.columns(
        [0.8, 1.4, 0.8],
    )

    with center:

        render_html(
            """
            <div class="fv-confirmation">

                <div class="fv-confirmation-icon">
                    ✓
                </div>

                <div class="fv-auth-kicker">
                    FITVISION / VERIFY EMAIL
                </div>

                <h1 class="fv-confirmation-title">
                    Check your
                    <span class="fv-auth-title-accent">
                        inbox.
                    </span>
                </h1>

                <div class="fv-accent-line"></div>

                <p class="fv-confirmation-description">
                    We've sent a confirmation link to your email address.
                    Confirm your account before signing in.
                </p>

            </div>
            """
        )

        render_html(
            f"""
            <div class="fv-confirmation-email">

                <span class="fv-confirmation-email-label">
                    CONFIRMATION EMAIL
                </span>

                <span class="fv-confirmation-email-value">
                    {email}
                </span>

            </div>
            """
        )

        st.write("")

        render_confirmation_actions(
            email
        )

        st.write("")

        if st.button(
            "← BACK TO SIGN IN",
            use_container_width=True,
            key="confirmation_back_to_signin",
        ):
            st.session_state["auth_mode"] = "signin"

            st.session_state["login_email"] = email

            st.session_state["screen"] = "auth"

            st.session_state.pop(
                "pending_confirmation_email",
                None,
            )

            st.session_state.pop(
                "confirmation_resend_available_at",
                None,
            )

            st.rerun()


# ---------------------------------------------------------
# dashboard
# ---------------------------------------------------------
def build_execution_command(
    workout_exercise: dict,
) -> WorkoutCommand:
    """
    Convert one persisted FitVision workout exercise into
    an AI GYM execution command.
    """
    if not is_workout_exercise_executable(workout_exercise):
        raise ValueError(
            f"Exercise '{workout_exercise.get('exercise_id')}' "
            "cannot currently be executed by AI GYM."
        )

    config = adapt_workout_exercise(workout_exercise)

    return WorkoutCommand(
        exercise_id=config.exercise_id,
        sets=config.sets,
        target_reps=config.target_reps,
        target_duration_seconds=config.target_duration_seconds,
        workout_exercise_id=config.workout_exercise_id,
        workout_day_id=config.workout_day_id,
    )

@st.fragment(run_every=0.25)
def render_live_metrics(context):
    if not context or not hasattr(context, "state"):
        return

    if not context.state.playing:
        return

    sync_metrics_update(context)

    target_duration_seconds = st.session_state.get(
        "target_duration_seconds"
    )

    is_time_based = (
        target_duration_seconds is not None
        and int(target_duration_seconds) > 0
    )

    if is_time_based:
        target_duration_seconds = int(
            target_duration_seconds
        )

        total_duration = max(
            0.0,
            float(
                st.session_state.get(
                    "total_duration",
                    0,
                )
            ),
        )

        current_set_duration = max(
            0.0,
            float(
                st.session_state.get(
                    "current_set_duration",
                    0,
                )
            ),
        )

        sets_completed = int(
            st.session_state.get(
                "sets_completed",
                0,
            )
        )

        target_sets = int(
            st.session_state.get(
                "target_sets",
                0,
            )
        )

        primary_label = "CURRENT SET"
        primary_value = (
            f"{current_set_duration:.1f}"
            f" / {target_duration_seconds}s"
        )

        progress_ratio = (
            current_set_duration
            / max(1, target_duration_seconds)
        )

        total_label = "TOTAL TIME"
        total_value = (
            f"{total_duration:.1f}s"
        )

    else:
        total_reps = int(
            st.session_state.get(
                "reps",
                0,
            )
        )

        current_set_reps = int(
            st.session_state.get(
                "current_set_reps",
                0,
            )
        )

        reps_per_set = int(
            st.session_state.get(
                "reps_per_set",
                0,
            )
        )

        sets_completed = int(
            st.session_state.get(
                "sets_completed",
                0,
            )
        )

        target_sets = int(
            st.session_state.get(
                "target_sets",
                0,
            )
        )

        primary_label = "CURRENT SET"
        primary_value = (
            f"{current_set_reps}"
            f" / {reps_per_set}"
        )

        progress_ratio = (
            current_set_reps
            / max(1, reps_per_set)
        )

        total_label = "TOTAL REPS"
        total_value = str(
            total_reps
        )

    set_ratio = (
        sets_completed
        / max(1, target_sets)
    )

    progress_ratio = max(
        0.0,
        min(1.0, progress_ratio),
    )

    set_ratio = max(
        0.0,
        min(1.0, set_ratio),
    )

    render_html(
        f"""
        <div class="fv-live-heading">
            <div>
                <div class="fv-live-kicker">
                    WORKOUT PROGRESS
                </div>

                <div class="fv-live-subtitle">
                    Real-time training feedback
                </div>
            </div>

            <div class="fv-live-status">
                <span></span>
                LIVE
            </div>
        </div>

        <div class="fv-progress-stat-grid">

            <div class="fv-progress-stat">
                <div class="fv-progress-stat-label">
                    {escape(total_label)}
                </div>

                <div class="fv-progress-stat-value">
                    {escape(total_value)}
                </div>
            </div>

            <div class="fv-progress-stat">
                <div class="fv-progress-stat-label">
                    {escape(primary_label)}
                </div>

                <div class="fv-progress-stat-value">
                    {escape(primary_value)}
                </div>

                <div class="fv-mini-progress">
                    <span style="width:{progress_ratio * 100:.1f}%"></span>
                </div>
            </div>

            <div class="fv-progress-stat">
                <div class="fv-progress-stat-label">
                    SETS
                </div>

                <div class="fv-progress-stat-value">
                    {sets_completed}
                    <span class="fv-progress-target">
                        / {target_sets}
                    </span>
                </div>

                <div class="fv-mini-progress">
                    <span style="width:{set_ratio * 100:.1f}%"></span>
                </div>
            </div>

        </div>

        <div class="fv-form-heading">
            <span>FORM ANALYSIS</span>
            <span>LIVE</span>
        </div>
        """
    )

    exercise_type = st.session_state.get(
        "exercise_type"
    )

    if not exercise_type:
        return

    fields = METRICS_FIELDS.get(
        exercise_type,
        {},
    )

    form_cards = []

    for key in fields:
        if key == "reps":
            continue

        if (
            key == "duration_seconds"
            and is_time_based
        ):
            continue

        value = st.session_state.get(
            key,
            fields[key],
        )

        label = (
            key
            .replace("_", " ")
            .title()
        )

        if isinstance(value, bool):
            display_value = (
                "Yes"
                if value
                else "No"
            )
        elif key.endswith("_angle"):
            display_value = f"{value}°"
        elif key == "duration_seconds":
            display_value = f"{value} sec"
        else:
            display_value = str(value)

        form_cards.append(
            f"""
            <div class="fv-form-metric-card">
                <div class="fv-form-metric-label">
                    {escape(label)}
                </div>

                <div class="fv-form-metric-value">
                    {escape(display_value)}
                </div>

                <div class="fv-form-metric-status">
                    <span></span>
                    Tracking
                </div>
            </div>
            """
        )

    if form_cards:
        render_html(
            f"""
            <div class="fv-form-grid">
                {''.join(form_cards)}
            </div>

            <div class="fv-coaching-card">
                <div class="fv-coaching-icon">
                    ✓
                </div>

                <div class="fv-coaching-body">
                    <div class="fv-coaching-title">
                        Keep going.
                    </div>

                    <div class="fv-coaching-copy">
                        Maintain your posture and complete the movement smoothly.
                    </div>

                    <div class="fv-coaching-bar">
                        <span style="width:{progress_ratio * 100:.1f}%"></span>
                    </div>
                </div>
            </div>
            """
        )
    else:
        render_html(
            """
            <div class="fv-coaching-card fv-coaching-muted">
                <div class="fv-coaching-icon">•</div>

                <div class="fv-coaching-body">
                    <div class="fv-coaching-title">
                        Tracking movement
                    </div>

                    <div class="fv-coaching-copy">
                        Live exercise feedback will appear here.
                    </div>
                </div>
            </div>
            """
        )


def render_trainer():
    render_html(
        """<div class="fv-screen-marker fv-trainer-screen"></div>"""
    )

    render_product_sidebar(
        "Warm-up" if st.session_state.get("warmup_mode", False)
        else "Workout Plan",
        navigation_locked=True,
    )

    if st.session_state.pop(
        "pending_workout_transition",
        False,
    ):
        st.rerun()

    active_command = st.session_state.get(
        "active_workout_command"
    )

    if active_command is None:
        st.session_state["screen"] = "dashboard"
        st.rerun()
        return

    warmup_mode = st.session_state.get(
        "warmup_mode",
        False,
    )

    exercise_names = {
        exercise["id"]: exercise["name"]
        for exercise in EXERCISES
    }

    exercise_name = exercise_names.get(
        active_command.exercise_id,
        active_command.exercise_id,
    )

    active_exercise = st.session_state.get(
        "active_workout_exercise",
        {},
    )

    current_set = int(
        st.session_state.get(
            "sets_completed",
            0,
        )
    ) + 1

    target_sets = int(
        active_command.sets or 1
    )

    # ---------------------------------------------------------
    # Session header
    # ---------------------------------------------------------
    header_left, header_status, header_action = st.columns(
        [3.0, 1.2, 1.1],
        gap="small",
        vertical_alignment="center",
    )

    with header_left:
        render_html(
            f"""
            <div class="fv-session-header">
                <div class="fv-session-brand">
                    FITVISION · AI GYM
                </div>

                <div class="fv-session-title">
                    {escape(exercise_name)}
                </div>

                <div class="fv-session-subtitle">
                    {(
                        "Trial warm-up"
                        if warmup_mode
                        else "Live workout"
                    )}
                    · Set {current_set} of {target_sets}
                </div>
            </div>
            """
        )

    with header_status:
        render_html(
            """
            <div class="fv-session-live-badge">
                <span></span>
                CAMERA LIVE
            </div>
            """
        )

    with header_action:
        end_button_label = (
            "END WARM-UP"
            if warmup_mode
            else "END WORKOUT"
        )

        if st.button(
            end_button_label,
            type="primary" if not warmup_mode else "secondary",
            use_container_width=True,
            key="end_ai_gym_workout",
        ):
            if ui_action_is_locked(
                "end_warmup"
                if warmup_mode
                else "end_workout"
            ):
                return

            st.session_state.pop(
                "active_workout_command",
                None,
            )

            st.session_state.pop(
                "active_workout_exercise_id",
                None,
            )

            st.session_state.pop(
                "active_workout_exercise",
                None,
            )

            st.session_state.pop(
                "_active_workout_command",
                None,
            )

            st.session_state.pop(
                "_progress_loaded_for_exercise",
                None,
            )

            st.session_state.pop(
                "_persisted_completed_sets",
                None,
            )

            st.session_state.pop(
                "last_saved_sets_completed",
                None,
            )

            st.session_state.pop(
                "warmup_mode",
                None,
            )

            st.session_state.pop(
                "warmup_exercise",
                None,
            )

            st.session_state.pop(
                "warmup_target_sets",
                None,
            )

            st.session_state.pop(
                "warmup_target_reps",
                None,
            )

            st.session_state.pop(
                "warmup_target_duration_seconds",
                None,
            )

            st.session_state["workout_started"] = False
            st.session_state[
                "returning_from_workout"
            ] = True

            request_workout_transition(
                screen="dashboard",
                message=(
                    "Finishing your warm-up..."
                    if warmup_mode
                    else "Finishing your workout..."
                ),
            )
            return

    render_html(
        f"""
        <div class="fv-trainer-hero">
            <div class="fv-trainer-hero-left">
                <span class="fv-trainer-kicker">
                    {(
                        "WARM-UP SESSION"
                        if warmup_mode
                        else "WORKOUT SESSION"
                    )}
                </span>

                <h1>
                    {escape(exercise_name)}
                </h1>

                <p>
                    {(
                        "Nothing from this session is saved."
                        if warmup_mode
                        else "Focus on your movement. Your AI trainer is tracking your form in real time."
                    )}
                </p>
            </div>

            <div class="fv-trainer-target-chip">
                <span>TARGET</span>
                <strong>
                    {(
                        f"{active_command.sets} sets"
                    )}
                </strong>
            </div>
        </div>
        """
    )

    camera_col, info_col = st.columns(
        [1.52, 0.92],
        gap="medium",
    )

    with camera_col:
        render_html(
            """
            <div class="fv-live-camera-heading">
                <span class="fv-live-dot"></span>
                LIVE CAMERA
            </div>
            """
        )

        context = render_workout_runner(
            active_command
        )

    with info_col:
        render_live_metrics(
            context
        )


def render_warmup() -> None:
    """
    Trial / warm-up mode.

    Uses the existing exercise detectors and trainer pipeline,
    but does not attach the session to a persisted workout
    exercise or workout day.
    """
    render_html(
        """<div class="fv-screen-marker fv-warmup-screen"></div>"""
    )

    render_product_sidebar(
        "Warm-up",
        navigation_locked=False,
    )

    exercise_by_id = {
        exercise["id"]: exercise
        for exercise in EXERCISES
    }

    exercise_names = {
        exercise["id"]: exercise["name"]
        for exercise in EXERCISES
    }

    exercise_ids = list(exercise_by_id)

    if not exercise_ids:
        st.error("No exercises are available right now.")
        return

    if "warmup_exercise_name" not in st.session_state:
        st.session_state["warmup_exercise_name"] = exercise_names[exercise_ids[0]]

    # ---------------------------------------------------------
    # Hero comes before the functional category controls.
    # ---------------------------------------------------------
    render_html(
        """
        <div class="fv-warmup-hero">
            <div>
                <div class="fv-eyebrow">
                    FITVISION / WARM-UP
                </div>

                <h1>
                    Prepare. Move. Perform.
                </h1>

                <p class="fv-muted">
                    Explore an exercise before your planned workout
                    and check how the AI trainer responds to your movement.
                </p>
            </div>

            <div class="fv-warmup-tip">
                <div class="fv-warmup-tip-icon">🔥</div>
                <div>
                    <strong>Why warm up?</strong>
                    <span>
                        Improve mobility, increase blood flow,
                        and prepare your body for training.
                    </span>
                </div>
            </div>
        </div>

        <div class="fv-warmup-section-title">
            CHOOSE A WARM-UP EXERCISE
        </div>
        """
    )

    # These are the real categories available in exercise_catalog.py.
    category_options = [
        "All",
        "Cardio",
        "Lower Body",
        "Upper Body",
        "Core",
    ]

    category = st.pills(
        "WARM-UP CATEGORY",
        options=category_options,
        default=st.session_state.get(
            "warmup_category_filter",
            "All",
        ),
        selection_mode="single",
        label_visibility="collapsed",
        key="warmup_category_filter_widget",
    )

    if category is None:
        category = "All"

    st.session_state["warmup_category_filter"] = category

    category_key = {
        "All": None,
        "Cardio": "cardio",
        "Lower Body": "lower_body",
        "Upper Body": "upper_body",
        "Core": "core",
    }[category]

    filtered_ids = [
        exercise_id
        for exercise_id in exercise_ids
        if category_key is None
        or exercise_by_id[exercise_id].get("category") == category_key
    ]

    if not filtered_ids:
        filtered_ids = exercise_ids

    selected_exercise_name = st.session_state["warmup_exercise_name"]
    selected_exercise_id = next(
        (
            exercise_id
            for exercise_id in filtered_ids
            if exercise_names[exercise_id] == selected_exercise_name
        ),
        filtered_ids[0],
    )

    selected_exercise_name = exercise_names[selected_exercise_id]
    st.session_state["warmup_exercise_name"] = selected_exercise_name
    selected_exercise = exercise_by_id[selected_exercise_id]

    # ---------------------------------------------------------
    # Interactive exercise grid.
    # Each exercise is a real Streamlit button styled as the entire card.
    # This removes the offset overlay that previously made clicks land on
    # neighboring cards.
    # ---------------------------------------------------------
    warmup_card_css = []

    for exercise_id in filtered_ids:
        card_key = f"warmup-card-{exercise_id}"
        image_uri = exercise_image_uri(exercise_id)
        is_selected = exercise_id == selected_exercise_id
        selected_border = "#FFC928" if is_selected else "rgba(255,255,255,0.10)"
        selected_shadow = (
            "0 0 0 0.8px rgba(255,201,40,0.82), "
            "0 12px 30px rgba(255,201,40,0.10)"
            if is_selected
            else "0 12px 30px rgba(0,0,0,0.18)"
        )

        warmup_card_css.append(
            f"""
            .st-key-{card_key} {{
                flex: 1 1 0 !important;
                min-width: 0 !important;
                padding: 0 !important;
                margin: 0 !important;
            }}

            .st-key-{card_key} [data-testid=\"stButton\"] {{
                width: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
            }}

            .st-key-{card_key} [data-testid=\"stButton\"] button {{
                width: 100% !important;
                min-height: 138px !important;
                height: 138px !important;
                padding: 82px 14px 12px !important;
                display: flex !important;
                align-items: flex-end !important;
                justify-content: flex-start !important;
                text-align: left !important;
                border-radius: 16px !important;
                border: 1px solid {selected_border} !important;
                background-image:
                    linear-gradient(180deg, rgba(5,8,9,0.02) 28%, rgba(5,8,9,0.88) 100%),
                    url(\"{image_uri}\") !important;
                background-size: cover !important;
                background-position: center center !important;
                background-repeat: no-repeat !important;
                background-color: #0B1012 !important;
                color: #F5F7F8 !important;
                box-shadow: {selected_shadow} !important;
                font-size: 0.78rem !important;
                font-weight: 900 !important;
                letter-spacing: 0.01em !important;
                white-space: normal !important;
                overflow: hidden !important;
                line-height: 1.15 !important;
            }}

            .st-key-{card_key} [data-testid=\"stButton\"] button:hover {{
                border-color: #FFC928 !important;
                box-shadow: 0 0 0 1px rgba(255,201,40,0.28), 0 14px 34px rgba(0,0,0,0.25) !important;
                transform: translateY(-1px) !important;
            }}

            .st-key-{card_key} [data-testid=\"stButton\"] button p {{
                margin: 0 !important;
                color: inherit !important;
                text-shadow: 0 2px 8px rgba(0,0,0,0.55) !important;
            }}
            """
        )

    render_html(
        f"""
        <style>
            {''.join(warmup_card_css)}
        </style>
        """
    )

    for row_start in range(0, len(filtered_ids), 4):
        row_ids = filtered_ids[row_start:row_start + 4]
        cols = st.columns(len(row_ids), gap="small")

        for column, exercise_id in zip(cols, row_ids):
            with column:
                with st.container(key=f"warmup-card-{exercise_id}"):
                    if st.button(
                        exercise_names[exercise_id],
                        use_container_width=True,
                        key=f"warmup_pick_{exercise_id}",
                    ):
                        if ui_action_is_locked(
                            f"warmup_pick_{exercise_id}",
                            cooldown_seconds=0.35,
                        ):
                            return

                        st.session_state["warmup_exercise_name"] = exercise_names[exercise_id]
                        st.rerun()

    trainer_exercise_type = get_trainer_exercise_type(selected_exercise_id)
    exercise_metrics = METRICS_FIELDS.get(trainer_exercise_type, {})
    is_time_based = "duration_seconds" in exercise_metrics

    default_target_text = "30–60 SEC" if is_time_based else "REP BASED"

    render_html(
        f"""
        <div class="fv-warmup-config">
            <div class="fv-warmup-selected">
                <img
                    src="{exercise_image_uri(selected_exercise_id)}"
                    alt="{escape(selected_exercise_name)}"
                />
                <div>
                    <span>SELECTED EXERCISE</span>
                    <strong>{escape(selected_exercise_name)}</strong>
                    <small>{default_target_text}</small>
                </div>
            </div>
        </div>
        """
    )

    config_col, preview_col = st.columns([1.15, 0.85], gap="medium")

    with config_col:
        if is_time_based:
            target_duration = st.number_input(
                "Seconds per set",
                min_value=5,
                max_value=600,
                value=30,
                step=5,
                key="warmup_target_duration",
            )
            target_reps = None
        else:
            target_reps = st.number_input(
                "Repetitions per set",
                min_value=1,
                max_value=100,
                value=10,
                step=1,
                key="warmup_target_reps",
            )
            target_duration = None

        target_sets = st.number_input(
            "Number of sets",
            min_value=1,
            max_value=10,
            value=1,
            step=1,
            key="warmup_target_sets",
        )

    with preview_col:
        if is_time_based:
            target_summary = (
                f"{int(target_sets)} set"
                f"{'s' if int(target_sets) != 1 else ''}"
                f" × {int(target_duration)} seconds"
            )
        else:
            target_summary = (
                f"{int(target_sets)} set"
                f"{'s' if int(target_sets) != 1 else ''}"
                f" × {int(target_reps)} reps"
            )

        render_html(
            f"""
            <div class="fv-warmup-summary-card">
                <span>SESSION TARGET</span>
                <strong>{escape(target_summary)}</strong>
                <small>Trial mode · Nothing is saved</small>
            </div>
            """
        )

    action_col, back_col = st.columns([3, 1], gap="small")

    with action_col:
        if st.button(
            "START WARM-UP →",
            type="primary",
            use_container_width=True,
            key="start_warmup",
        ):
            if ui_action_is_locked("start_warmup"):
                return

            st.session_state.pop("_progress_loaded_for_exercise", None)
            st.session_state.pop("_persisted_completed_sets", None)
            st.session_state.pop("last_saved_sets_completed", None)

            st.session_state["sidebar_page"] = "Warm-up"
            st.session_state["warmup_mode"] = True
            st.session_state["warmup_exercise"] = dict(selected_exercise)

            warmup_command = WorkoutCommand(
                exercise_id=selected_exercise_id,
                sets=int(target_sets),
                target_reps=(
                    int(target_reps)
                    if target_reps is not None
                    else None
                ),
                target_duration_seconds=(
                    int(target_duration)
                    if target_duration is not None
                    else None
                ),
                workout_exercise_id=None,
                workout_day_id=None,
            )

            st.session_state["active_workout_command"] = warmup_command
            st.session_state["active_workout_exercise"] = {
                "id": f"warmup_{selected_exercise_id}",
                "exercise_id": selected_exercise_id,
                "sets": int(target_sets),
                "target_reps": (
                    int(target_reps)
                    if target_reps is not None
                    else None
                ),
                "target_duration_seconds": (
                    int(target_duration)
                    if target_duration is not None
                    else None
                ),
                "completed_sets": 0,
                "status": "warmup",
            }
            st.session_state["active_workout_exercise_id"] = None
            st.session_state["workout_day_id"] = None
            st.session_state["workout_started"] = True

            request_workout_transition(
                screen="trainer",
                message="Starting your warm-up...",
            )

    with back_col:
        if st.button(
            "← BACK",
            use_container_width=True,
            key="warmup_back",
        ):
            if ui_action_is_locked("warmup_back"):
                return

            clear_warmup_setup_state()
            st.session_state["workout_started"] = False
            st.session_state["returning_from_workout"] = True
            st.session_state["sidebar_page"] = "Workout Plan"

            request_workout_transition(
                screen="dashboard",
                message="Returning to your workout plan...",
            )


def _parse_dashboard_day_date(day: dict) -> date | None:
    """Read the persisted workout day date without changing backend data."""
    raw_value = day.get("workout_date") or day.get("date")

    try:
        return date.fromisoformat(str(raw_value)[:10])
    except (TypeError, ValueError):
        return None


def _calculate_dashboard_stats(
    day_entries: list[tuple[dict, str]],
    today: date,
) -> tuple[int, int, int, int, int]:
    """Return completed days, remaining days, weekly workouts, weekly exercises, streak."""
    completed_days = sum(
        bool(day.get("is_completed"))
        for day, _ in day_entries
    )

    remaining_days = max(
        0,
        len(day_entries) - completed_days,
    )

    week_start = today.fromordinal(
        today.toordinal() - today.weekday()
    )
    week_end = week_start.fromordinal(
        week_start.toordinal() + 6
    )

    weekly_days = []
    weekly_exercises = 0

    for day, _ in day_entries:
        day_date = _parse_dashboard_day_date(day)
        if day_date is None or not (week_start <= day_date <= week_end):
            continue

        weekly_days.append(day)
        weekly_exercises += sum(
            str(exercise.get("status") or "").strip().lower() == "completed"
            for exercise in day.get("exercises", [])
        )

    weekly_workouts = sum(
        bool(day.get("is_completed"))
        for day in weekly_days
    )

    streak_days = 0
    for day, _ in reversed(day_entries):
        if not day.get("is_completed"):
            continue

        day_date = _parse_dashboard_day_date(day)
        if day_date is None:
            continue

        if streak_days == 0:
            expected = today if day_date == today else day_date
        else:
            expected = previous_date

        if day_date != expected:
            break

        streak_days += 1
        previous_date = day_date.fromordinal(day_date.toordinal() - 1)

    return (
        completed_days,
        remaining_days,
        weekly_workouts,
        weekly_exercises,
        streak_days,
    )


def render_dashboard() -> None:
    render_html(
        """<div class="fv-screen-marker fv-dashboard-screen"></div>"""
    )

    active_sidebar_page = st.session_state.get(
        "sidebar_page",
        "Dashboard",
    )

    render_product_sidebar(
        active_sidebar_page
        if active_sidebar_page in {"Dashboard", "Workout Plan"}
        else "Dashboard"
    )

    user_id = st.session_state.get("user_id")

    if not user_id:
        st.error("Your session has expired. Please sign in again.")
        return

    dashboard_service = DashboardService()

    returning_from_workout = st.session_state.pop(
        "returning_from_workout",
        False,
    )

    cached_plan = st.session_state.get("dashboard_plan_cache")

    if returning_from_workout and cached_plan is not None:
        plan = cached_plan
    else:
        plan = dashboard_service.get_active_plan(user_id)

        if plan is None:
            st.error("No active training plan was found.")
            return

        st.session_state["dashboard_plan_cache"] = plan

    days = plan.get("days", [])

    if not days:
        st.warning("No workout days are available in your plan.")
        return

    user_email = st.session_state.get("user_email", "")
    display_name = (
        user_email.split("@")[0]
        .replace(".", " ")
        .replace("_", " ")
        .replace("-", " ")
        .title()
        if user_email
        else "Athlete"
    )

    today = date.today()
    day_entries: list[tuple[dict, str]] = []

    for day in days:
        day_date = _parse_dashboard_day_date(day)
        is_completed = bool(day.get("is_completed"))
        persisted_state = str(day.get("workout_state") or "").strip().lower()

        # Initial placeholder; normalized after current day number is known.
        day_entries.append((day, "pending"))

    (
        completed_days,
        remaining_days,
        weekly_workouts,
        weekly_exercises,
        streak_days,
    ) = _calculate_dashboard_stats(day_entries, today)

    today_entry = next(
        (
            (day, state)
            for day, state in day_entries
            if _parse_dashboard_day_date(day) == today
        ),
        None,
    )

    today_day = today_entry[0] if today_entry is not None else None

    if today_day is not None:
        current_day_number = int(today_day.get("day_number", 1))
    else:
        # Fallback to the persisted plan start date so the rail still has a
        # deterministic TODAY position if a day-date value is absent/misaligned.
        first_day_date = _parse_dashboard_day_date(day_entries[0][0])
        if first_day_date is not None:
            current_day_number = max(
                1,
                min(
                    len(day_entries),
                    (today - first_day_date).days + 1,
                ),
            )
        else:
            current_day_number = int(day_entries[0][0].get("day_number", 1))

    # Normalize the timeline strictly by day number.
    # Today = yellow, future = locked, past completed = green,
    # past incomplete = red.
    normalized_day_entries: list[tuple[dict, str]] = []
    for day, _ in day_entries:
        day_number = int(day.get("day_number", 0))
        is_completed = bool(day.get("is_completed"))
        persisted_state = str(day.get("workout_state") or "").strip().lower()

        if day_number == current_day_number:
            state = "today"
        elif day_number > current_day_number:
            state = "locked"
        elif is_completed or persisted_state == "completed":
            state = "completed"
        else:
            state = "missed"

        normalized_day_entries.append((day, state))

    day_entries = normalized_day_entries

    valid_day_numbers = {
        int(day.get("day_number", 0))
        for day, _ in day_entries
    }

    selected_day_number = int(
        st.session_state.get(
            "dashboard_selected_day_number",
            current_day_number,
        )
    )

    if selected_day_number not in valid_day_numbers:
        selected_day_number = current_day_number

    selected_state = next(
        state
        for day, state in day_entries
        if int(day.get("day_number", 0)) == selected_day_number
    )

    if selected_state == "locked":
        selected_day_number = current_day_number
        selected_state = next(
            state
            for day, state in day_entries
            if int(day.get("day_number", 0)) == selected_day_number
        )

    st.session_state["dashboard_selected_day_number"] = selected_day_number

    gym_uri = asset_data_uri("dashboard/gym_header.webp")

    render_html(
        f"""
        <style>
            .fv-dashboard-header {{
                background-image:
                    linear-gradient(
                        90deg,
                        rgba(5,8,9,0.98) 0%,
                        rgba(5,8,9,0.90) 44%,
                        rgba(5,8,9,0.44) 75%,
                        rgba(5,8,9,0.78) 100%
                    ),
                    url("{gym_uri}");
            }}
        </style>

        <section class="fv-dashboard-header">
            <div class="fv-dashboard-header-copy">
                <div class="fv-dashboard-kicker">
                    FITVISION / AI GYM TRAINER
                </div>
                <h1>
                    Good evening,
                    <span>{escape(display_name)}</span>
                    👋
                </h1>
                <p>Consistency today. Results tomorrow.</p>
            </div>

            <div class="fv-dashboard-quote">
                “Discipline today.<br>
                <span>Stronger tomorrow.</span>”
            </div>

            <div class="fv-dashboard-profile">
                <div class="fv-profile-avatar">
                    {escape(display_name[:1].upper())}
                </div>
                <div>
                    <strong>{escape(display_name)}</strong>
                    <span>Free Plan</span>
                    <small>PREMIUM · SOON</small>
                </div>
                <b>⌄</b>
            </div>
        </section>
        """
    )

    render_html(
        """
        <div class="fv-plan-heading">
            <div>
                <div class="fv-plan-kicker">YOUR 28-DAY PLAN</div>
                <h2>Stay consistent. Get stronger.</h2>
                <p>Complete today's session to keep your momentum.</p>
            </div>
        </div>
        """
    )

    # ---------------------------------------------------------
    # Scrollable 28-day timeline
    # ---------------------------------------------------------
    # Use real Streamlit buttons inside a keyed horizontal container.
    # This keeps selection in the existing Streamlit session instead of
    # using query parameters/browser navigation.
    rail_css = []

    with st.container(
        horizontal=True,
        wrap=False,
        horizontal_alignment="left",
        gap="small",
        key="dashboard-day-rail",
    ):
        for day, state in day_entries:
            day_number = int(day.get("day_number", 0))
            button_key = f"dashboard_day_button_{day_number}"
            is_selected = day_number == selected_day_number

            if state == "completed":
                accent = "#38E27B"
                background = "rgba(56,226,123,0.08)"
                border = "rgba(56,226,123,0.30)"
                label = f"✓  DAY {day_number}  DONE"
            elif state == "today":
                accent = "#FFC928"
                background = "rgba(255,201,40,0.12)"
                border = "rgba(255,201,40,0.48)"
                label = f"●  DAY {day_number}  TODAY"
            elif state == "missed":
                accent = "#FF5A5F"
                background = "rgba(255,90,95,0.08)"
                border = "rgba(255,90,95,0.28)"
                label = f"×  DAY {day_number}  NOT DONE"
            else:
                accent = "#89939A"
                background = "rgba(255,255,255,0.025)"
                border = "rgba(255,255,255,0.10)"
                label = f"🔒  DAY {day_number}  LOCKED"

            if is_selected:
                shadow = (
                    f"0 0 0 1px {border}, "
                    f"0 8px 24px {background}"
                )
            else:
                shadow = "none"

            rail_css.append(
                f"""
                .st-key-{button_key} {{
                    flex: 0 0 auto !important;
                    width: auto !important;
                    min-width: 0 !important;
                    padding: 0 !important;
                    margin: 0 !important;
                }}

                .st-key-{button_key} [data-testid=\"stButton\"] {{
                    margin: 0 !important;
                    padding: 0 !important;
                }}

                .st-key-{button_key} [data-testid=\"stBaseButton-secondary\"],
                .st-key-{button_key} [data-testid=\"stBaseButton-primary\"] {{
                    min-width: 92px !important;
                    min-height: 48px !important;
                    height: 48px !important;
                    padding: 0 12px !important;
                    border-radius: 13px !important;
                    border: 1px solid {border} !important;
                    background: {background} !important;
                    color: {accent} !important;
                    font-size: 0.62rem !important;
                    font-weight: 900 !important;
                    letter-spacing: 0.035em !important;
                    white-space: nowrap !important;
                    box-shadow: {shadow} !important;
                }}

                .st-key-{button_key} [data-testid=\"stBaseButton-secondary\"]:hover,
                .st-key-{button_key} [data-testid=\"stBaseButton-primary\"]:hover {{
                    border-color: {accent} !important;
                    background: {background} !important;
                    color: {accent} !important;
                    transform: translateY(-1px);
                }}
                """
            )

            clicked = st.button(
                label,
                key=button_key,
                type="secondary",
                disabled=(state == "locked"),
                use_container_width=False,
            )

            if clicked:
                if ui_action_is_locked(
                    f"dashboard_day_{day_number}",
                    cooldown_seconds=0.25,
                ):
                    return

                selected_day_number = day_number
                selected_state = state
                st.session_state["dashboard_selected_day_number"] = day_number
                st.rerun()

    render_html(
        f"""
        <style>
            {''.join(rail_css)}
        </style>
        """
    )

    # Resolve the selected day after the button interaction path.
    selected_day = next(
        day
        for day, _ in day_entries
        if int(day.get("day_number", 0)) == selected_day_number
    )

    exercise_names = {
        exercise["id"]: exercise["name"]
        for exercise in EXERCISES
    }

    strength_uri = asset_data_uri("dashboard/strength_hero.webp")
    exercise_html = []

    for exercise in selected_day.get("exercises", []):
        exercise_id = exercise.get("exercise_id", "")
        exercise_name = exercise_names.get(exercise_id, exercise_id)
        sets = int(exercise.get("sets", 0))
        target_reps = exercise.get("target_reps")
        target_duration = exercise.get("target_duration_seconds")

        if target_reps is not None:
            target_text = f"{sets} sets · {int(target_reps)} reps"
        else:
            target_text = f"{sets} sets · {int(target_duration or 0)} sec"

        status = str(exercise.get("status") or "").strip().lower()

        if status == "completed":
            status_text, status_class, status_icon = "Completed", "done", "✓"
        elif status == "in_progress":
            status_text, status_class, status_icon = "In progress", "progress", "●"
        elif status == "warmup":
            status_text, status_class, status_icon = "Warm-up", "progress", "●"
        else:
            status_text, status_class, status_icon = "Ready", "pending", "•"

        current_marker = ""

        image_uri = exercise_image_uri(exercise_id)

        exercise_html.append(
            f"""
            <div class="fv-pro-exercise-card{current_marker}">
                <div class="fv-pro-exercise-index">
                    {int(exercise.get("order_index", 0))}
                </div>
                <div class="fv-pro-exercise-image">
                    <img src="{image_uri}" alt="{escape(exercise_name)}" />
                </div>
                <div class="fv-pro-exercise-copy">
                    <strong>{escape(exercise_name)}</strong>
                    <span>{escape(target_text)}</span>
                </div>
                <div class="fv-pro-exercise-status {status_class}">
                    <span>{status_icon}</span>
                    {escape(status_text)}
                </div>
            </div>
            """
        )

    selected_day_title = (
        f"Day {selected_day_number} · Today's Strength Session"
        if selected_day_number == current_day_number
        else f"Day {selected_day_number} · Workout"
    )

    workout_label = (
        "TODAY'S WORKOUT"
        if selected_day_number == current_day_number
        else "WORKOUT PLAN"
    )

    render_html(
        f"""
        <div class="fv-dashboard-grid">
            <section class="fv-workout-panel">
                <div class="fv-workout-panel-head">
                    <div>
                        <span>{workout_label}</span>
                        <h3>{escape(selected_day_title)}</h3>
                    </div>
                    <div class="fv-workout-duration">
                        <span>◷</span>
                        ~ 28 min
                    </div>
                </div>
                <div class="fv-exercise-list">
                    {''.join(exercise_html)}
                </div>
            </section>

            <section class="fv-strength-card">
                <img src="{strength_uri}" alt="" />
                <div class="fv-strength-stats">
                    <div>
                        <b>✓</b>
                        <strong>{completed_days}</strong>
                        <span>Days Completed</span>
                    </div>
                    <div>
                        <b>▥</b>
                        <strong>{remaining_days}</strong>
                        <span>Days Remaining</span>
                    </div>
                </div>
            </section>

            <aside class="fv-dashboard-side">
                <div class="fv-week-card">
                    <div class="fv-side-card-title">
                        <span>🔥</span>
                        THIS WEEK
                    </div>
                    <div class="fv-side-stat-grid">
                        <div>
                            <span>🔥</span>
                            <strong>{weekly_workouts}</strong>
                            <small>Workouts</small>
                        </div>
                        <div>
                            <span>▥</span>
                            <strong>{weekly_exercises}</strong>
                            <small>Exercises</small>
                        </div>
                        <div>
                            <span>↗</span>
                            <strong>{streak_days}</strong>
                            <small>Day Streak</small>
                        </div>
                    </div>
                </div>

                <div class="fv-quote-card">
                    <div class="fv-quote-mark">“</div>
                    <p>A little progress each day adds up to big results.</p>
                    <div class="fv-quote-line"></div>
                </div>
            </aside>
        </div>
        """
    )

    current_exercise = next(
        (
            exercise
            for exercise in selected_day.get("exercises", [])
            if str(exercise.get("status") or "").strip().lower() != "completed"
        ),
        None,
    )

    if current_exercise is None:
        render_html(
            """
            <div class="fv-complete-banner">
                <span>✓</span>
                <div>
                    <strong>Workout complete</strong>
                    <small>Great work. Your progress has been saved.</small>
                </div>
            </div>
            """
        )
    elif selected_state != "locked":
        current_exercise_name = exercise_names.get(
            current_exercise["exercise_id"],
            current_exercise["exercise_id"],
        )

        action_left, action_right = st.columns(
            [2.2, 1],
            gap="medium",
            vertical_alignment="center",
        )

        with action_left:
            render_html(
                f"""
                <div class="fv-next-up-card">
                    <div class="fv-next-up-image">
                        <img
                            src="{exercise_image_uri(current_exercise['exercise_id'])}"
                            alt=""
                        />
                    </div>
                    <div>
                        <span>NEXT UP</span>
                        <strong>{escape(current_exercise_name)}</strong>
                        <small>Ready when you are.</small>
                    </div>
                </div>
                """
            )

        with action_right:
            if st.button(
                "START WORKOUT →",
                type="primary",
                use_container_width=True,
                key=f"start_workout_{current_exercise['id']}",
            ):
                if ui_action_is_locked("start_workout"):
                    return

                try:
                    command = build_execution_command(current_exercise)
                    st.session_state["active_workout_command"] = command
                    st.session_state["active_workout_exercise_id"] = current_exercise["id"]
                    st.session_state["active_workout_exercise"] = dict(current_exercise)
                    st.session_state["workout_started"] = True
                    st.session_state["sidebar_page"] = "Workout Plan"

                    request_workout_transition(
                        screen="trainer",
                        message="Preparing your workout...",
                    )
                    return
                except Exception as exc:
                    st.error(
                        "This exercise cannot be started: "
                        f"{exc}"
                    )

    warmup_col, signout_col = st.columns([2.2, 1], gap="medium")

    with warmup_col:
        if st.button(
            "TRY WARM-UP / EXPLORE EXERCISES",
            use_container_width=True,
            key="open_warmup",
        ):
            if ui_action_is_locked("open_warmup"):
                return

            st.session_state["sidebar_page"] = "Warm-up"
            request_workout_transition(
                screen="warmup",
                message="Preparing your warm-up...",
            )
            return 
    with signout_col:
        if st.button(
            "SIGN OUT",
            use_container_width=True,
            key="dashboard_sign_out",
        ):
            if ui_action_is_locked("sign_out"):
                return

            sign_out_user()


def render_onboarding() -> None:

    onboarding_step = st.session_state.get(
        "onboarding_step",
        1,
    )

    if onboarding_step == 2:
        render_limitations()
        return

    if onboarding_step == 3:
        render_onboarding_complete()
        return

    profile_service = FitnessProfileService()

    render_html(
        """
        <div class="fv-eyebrow">
            FITVISION / PROFILE
        </div>

        <h1 class="fv-onboarding-title">
            Let's build your
            <span class="fv-auth-title-accent">
                training profile.
            </span>
        </h1>

        <div class="fv-accent-line"></div>

        <p class="fv-muted">
            Tell us about yourself so we can personalize your training.
        </p>
        """
    )

    st.write("")

    today = date.today()

    date_of_birth = st.date_input(
        "Date of birth",
        value=today.replace(year=today.year - 22),
        min_value=date(today.year - 100, today.month, today.day),
        max_value=date(today.year - 10, today.month, today.day),
        key="onboarding_date_of_birth",
    )

    sex = st.selectbox(
        "Sex",
        options=[
            "Male",
            "Female",
            "Other",
            "Prefer not to say",
        ],
        key="onboarding_sex",
    )

    height_cm = st.number_input(
        "Height (cm)",
        min_value=100.0,
        max_value=250.0,
        value=170.0,
        step=0.5,
        key="onboarding_height_cm",
    )

    weight_kg = st.number_input(
        "Weight (kg)",
        min_value=30.0,
        max_value=300.0,
        value=70.0,
        step=0.5,
        key="onboarding_weight_kg",
    )

    # -----------------------------------------------------
    # Fitness level
    # -----------------------------------------------------

    fitness_level_labels = {
        1: "Beginner",
        2: "Lightly trained",
        3: "Moderate",
        4: "Well trained",
        5: "Highly trained",
    }

    render_html(
        """
        <div class="fv-profile-field-label">
            <span class="fv-profile-field-title">
                Fitness level
            </span>

            <span class="fv-profile-field-help">
                (How comfortable you are with exercise right now —
                1 = beginner, 5 = highly trained.)
            </span>
        </div>
        """
    )

    fitness_level = st.select_slider(
        "Fitness level",
        options=[1, 2, 3, 4, 5],
        value=3,
        key="onboarding_fitness_level",
        label_visibility="collapsed",
        format_func=lambda value: (
            f"{value} ({fitness_level_labels[value]})"
        ),
    )

    # -----------------------------------------------------
    # Activity level
    # -----------------------------------------------------

    activity_level_labels = {
        1: "Mostly inactive",
        2: "Lightly active",
        3: "Moderately active",
        4: "Very active",
        5: "Highly active",
    }

    render_html(
        """
        <div class="fv-profile-field-label">
            <span class="fv-profile-field-title">
                Activity level
            </span>

            <span class="fv-profile-field-help">
                (How active you are in your normal daily life —
                1 = mostly inactive, 5 = very active.)
            </span>
        </div>
        """
    )

    activity_level = st.select_slider(
        "Activity level",
        options=[1, 2, 3, 4, 5],
        value=3,
        key="onboarding_activity_level",
        label_visibility="collapsed",
        format_func=lambda value: (
            f"{value} ({activity_level_labels[value]})"
        ),
    )

    # -----------------------------------------------------
    # Primary goal
    # -----------------------------------------------------

    render_html(
        """
        <div class="fv-profile-field-label">
            <span class="fv-profile-field-title">
                Primary goal
            </span>

            <span class="fv-profile-field-help">
                (The main outcome you want your training plan
                to focus on.)
            </span>
        </div>
        """
    )

    goal_options = {
        "General fitness": "general_fitness",
        "Weight management": "weight_management",
        "Strength": "strength",
        "Endurance": "endurance",
    }

    goal_label = st.selectbox(
        "Goal",
        options=list(goal_options.keys()),
        key="onboarding_goal",
        label_visibility="collapsed",
    )

    goal = goal_options[goal_label]

    # -----------------------------------------------------
    # Preferred workout time
    # -----------------------------------------------------

    render_html(
        """
        <div class="fv-profile-field-label">
            <span class="fv-profile-field-title">
                Preferred workout time
            </span>

            <span class="fv-profile-field-help">
                (How much time you can comfortably dedicate
                to each workout.)
            </span>
        </div>
        """
    )

    workout_time_min = st.slider(
        "Workout time",
        min_value=10,
        max_value=120,
        value=30,
        step=5,
        key="onboarding_workout_time",
        label_visibility="collapsed",
        format="%d min",
    )

    st.write("")

    if st.button(
        "CONTINUE →",
        type="primary",
        use_container_width=True,
        key="onboarding_continue",
    ):
        try:
            user_id = st.session_state.get("user_id")

            if not user_id:
                raise RuntimeError(
                    "Your session has expired. Please sign in again."
                )

            profile_service.create_profile(
                user_id=user_id,
                date_of_birth=date_of_birth,
                sex=sex,
                height_cm=height_cm,
                weight_kg=weight_kg,
                fitness_level=fitness_level,
                activity_level=activity_level,
                goal=goal,
                workout_time_min=workout_time_min,
            )

            st.session_state["onboarding_step"] = 2
            st.rerun()

        except Exception as exc:
            st.error(str(exc))


def render_limitations() -> None:
    body_parts = {
        "Knee": "knee",
        "Hip": "hip",
        "Shoulder": "shoulder",
        "Wrist": "wrist",
        "Back": "back",
        "Ankle": "ankle",
    }

    concern_options = [
        "Good",
        "Slight concern",
        "Moderate concern",
        "Significant concern",
    ]

    render_html(
        """
        <div class="fv-eyebrow">
            FITVISION / SAFETY
        </div>

        <h1 class="fv-onboarding-title fv-safety-title">
            Let's understand your
            <span class="fv-auth-title-accent">
                movement needs.
            </span>
        </h1>

        <div class="fv-accent-line"></div>

        <p class="fv-muted">
            Your body matters. Tell us how each area feels so we can
            make your training more appropriate.
        </p>

        <div class="fv-assessment-guide">
            <div class="fv-assessment-guide-title">
                HOW TO ANSWER
            </div>

            <div class="fv-assessment-guide-grid">
                <div>
                    <strong>Good</strong>
                    <span>
                        No pain, discomfort, or movement difficulty.
                    </span>
                </div>

                <div>
                    <strong>Slight concern</strong>
                    <span>
                        Occasional or minor discomfort, but normal
                        movement is mostly unaffected.
                    </span>
                </div>

                <div>
                    <strong>Moderate concern</strong>
                    <span>
                        Noticeable discomfort or some movements feel
                        limited.
                    </span>
                </div>

                <div>
                    <strong>Significant concern</strong>
                    <span>
                        Clear pain, restriction, or difficulty that
                        should influence exercise selection.
                    </span>
                </div>
            </div>
        </div>
        """
    )

    selections = {}

    for label, limitation_value in body_parts.items():

        render_html(
            f"""
            <div class="fv-assessment-question-title">
                {label}
            </div>
            """
        )

        selections[limitation_value] = st.radio(
            label,
            options=concern_options,
            horizontal=True,
            index=0,
            key=f"onboarding_{limitation_value}_concern",
            label_visibility="collapsed",
        )

        st.write("")

    if st.button(
        "CONTINUE →",
        type="primary",
        use_container_width=True,
        key="limitations_continue",
    ):
        try:
            user_id = st.session_state.get("user_id")

            if not user_id:
                raise RuntimeError(
                    "Your session has expired. Please sign in again."
                )

            significant_limitations = [
                limitation_value
                for limitation_value, concern in selections.items()
                if concern == "Significant concern"
            ]

            limitation_service = UserLimitationService()

            limitation_service.set_limitations(
                user_id=user_id,
                limitations=significant_limitations,
            )

            st.session_state["onboarding_step"] = 3
            st.rerun()

        except Exception as exc:
            st.error(str(exc))

def render_onboarding_complete() -> None:
    render_html(
        """
        <div class="fv-eyebrow">
            FITVISION / PROFILE READY
        </div>

        <h1 class="fv-onboarding-title">
            Your profile is
            <span class="fv-auth-title-accent">
                ready.
            </span>
        </h1>

        <div class="fv-accent-line"></div>

        <p class="fv-muted">
            Your fitness information and movement assessment have been
            saved. The personalized training plan is the next step.
        </p>
        """
    )

    st.write("")

    is_generating_plan = st.session_state.get(
        "generating_plan",
        False,
    )

    if not is_generating_plan:

        if st.button(
            "CONTINUE TO DASHBOARD →",
            type="primary",
            use_container_width=True,
            key="onboarding_complete_continue",
        ):
            st.session_state["generating_plan"] = True
            st.rerun()

    else:

        try:
            user_id = st.session_state.get("user_id")

            if not user_id:
                raise RuntimeError(
                    "Your session has expired. Please sign in again."
                )

            with st.status(
                "BUILDING YOUR PERSONALIZED PLAN...",
                expanded=True,
            ) as status:

                status.write(
                    "Analyzing your fitness profile..."
                )

                status.write(
                    "Selecting eligible exercises..."
                )

                status.write(
                    "Generating personalized training dosage..."
                )

                status.write(
                    "Building your 28-day progression..."
                )

                generate_and_save_plan(user_id)

                st.session_state.pop(
                    "dashboard_plan_cache",
                    None,
                )

                status.update(
                    label="YOUR 28-DAY PLAN IS READY ✓",
                    state="complete",
                    expanded=False,
                )

            st.session_state.pop(
                "generating_plan",
                None,
            )

            st.session_state.pop(
                "onboarding_step",
                None,
            )

            st.rerun()

        except Exception as exc:

            st.session_state["generating_plan"] = False

            st.error(
                f"Your training plan could not be created: {exc}"
            )



# ---------------------------------------------------------
# App entry point
# ---------------------------------------------------------

def main() -> None:

    st.set_page_config(
        page_title="FitVision",
        page_icon="🏋️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    load_theme()

    # Purely visual transition layer for workout/warm-up
    # screen changes.
    render_transition_layer()

    # ---------------------------------------------------------
    # SINGLE MAIN SCREEN SLOT
    #
    # st.empty() is intentionally used here instead of
    # st.container().
    #
    # Dashboard / Trainer / Warm-up all occupy this same
    # placeholder. When the screen changes, the previous
    # screen content is replaced instead of leaving multiple
    # screen trees behind.
    # ---------------------------------------------------------
    screen_host = st.empty()

    if st.session_state.get("authenticated", False):

        with screen_host.container():

            # -------------------------------------------------
            # RETURNING FROM WORKOUT / WARM-UP
            # -------------------------------------------------
            if st.session_state.get(
                "returning_from_workout",
                False,
            ):
                render_dashboard()
                return

            # -------------------------------------------------
            # TRAINER
            # -------------------------------------------------
            if st.session_state.get("screen") == "trainer":
                render_trainer()
                return

            # -------------------------------------------------
            # WARM-UP
            # -------------------------------------------------
            if st.session_state.get("screen") == "warmup":
                render_warmup()
                return

            # -------------------------------------------------
            # NORMAL AUTHENTICATED FLOW
            # -------------------------------------------------
            user_id = st.session_state.get("user_id")

            if st.session_state.get(
                "onboarding_step"
            ) in {1, 2, 3}:
                render_onboarding()
                return

            if user_id:

                has_profile = user_has_fitness_profile(
                    user_id
                )

                if not has_profile:
                    st.session_state["onboarding_step"] = 1
                    render_onboarding()
                    return

                has_plan = user_has_workout_plan(
                    user_id
                )

                if not has_plan:
                    st.session_state["onboarding_step"] = 2
                    render_onboarding()
                    return

                # Profile + safety + plan completed.
                render_dashboard()
                return

            # -------------------------------------------------
            # No user_id
            # -------------------------------------------------
            st.session_state["onboarding_step"] = 1
            render_onboarding()
            return

    # ---------------------------------------------------------
    # EMAIL CONFIRMATION
    # ---------------------------------------------------------
    if st.session_state.get(
        "screen"
    ) == "email_confirmation":

        with screen_host.container():
            render_email_confirmation()

        return

    # ---------------------------------------------------------
    # AUTHENTICATION HOME
    # ---------------------------------------------------------
    with screen_host.container():
        render_auth_home()


if __name__ == "__main__":
    main()