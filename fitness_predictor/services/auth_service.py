from typing import Any
from database.client import set_authenticated_session
from database.client import get_supabase_client


class AuthService:
    """
    Handles user authentication through Supabase Auth.

    This service is intentionally separate from the frontend.
    """

    def __init__(self):
        self.supabase = get_supabase_client()

    def sign_up(
        self,
        email: str,
        password: str,
        full_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new Supabase Auth account.

        The Supabase database trigger will automatically create
        the corresponding row in public.profiles.
        """

        email = email.strip().lower()

        if not email:
            raise ValueError("Email cannot be empty.")

        if not password:
            raise ValueError("Password cannot be empty.")

        if len(password) < 6:
            raise ValueError(
                "Password must contain at least 6 characters."
            )

        metadata = {}

        if full_name:
            metadata["full_name"] = full_name.strip()

        try:
            response = self.supabase.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {
                        "data": metadata
                    },
                }
            )
        except Exception as exc:
            raise RuntimeError(
                f"Signup failed: {exc}"
            ) from exc

        if response.user is None:
            raise RuntimeError(
                "Signup did not return a user."
            )

        return {
            "user_id": str(response.user.id),
            "email": response.user.email,
            "session": response.session,
        }
    
    def resend_signup_confirmation(
        self,
        email: str,
    ) -> None:
        """
        Resend the Supabase signup confirmation email.
        """

        email = email.strip().lower()

        if not email:
            raise ValueError(
                "Email cannot be empty."
            )

        try:
            self.supabase.auth.resend(
                {
                    "type": "signup",
                    "email": email,
                }
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to resend confirmation email: {exc}"
            ) from exc

    def sign_in(
        self,
        email: str,
        password: str,
    ) -> dict[str, Any]:
        """
        Sign in an existing user and attach the authenticated
        session to the application's Supabase client.
        """

        email = email.strip().lower()

        if not email:
            raise ValueError("Email cannot be empty.")

        if not password:
            raise ValueError("Password cannot be empty.")

        try:
            response = self.supabase.auth.sign_in_with_password(
                {
                    "email": email,
                    "password": password,
                }
            )
        except Exception as exc:
            raise RuntimeError(
                f"Login failed: {exc}"
            ) from exc

        if response.user is None:
            raise RuntimeError(
                "Login failed: no user returned."
            )

        if response.session is None:
            raise RuntimeError(
                "Login succeeded but no authenticated session was returned."
            )

        set_authenticated_session(
            response.session.access_token,
            response.session.refresh_token,
        )

        return {
            "user_id": str(response.user.id),
            "email": response.user.email,
            "session": response.session,
        }

    def sign_out(self) -> None:
        """
        Sign out the currently authenticated user.
        """

        try:
            self.supabase.auth.sign_out()
        except Exception as exc:
            raise RuntimeError(
                f"Logout failed: {exc}"
            ) from exc

    def get_current_user(self) -> dict[str, Any] | None:
        """
        Return the currently authenticated user.

        Returns None when there is no authenticated user.
        """

        try:
            user = self.supabase.auth.get_user().user
        except Exception:
            return None

        if user is None:
            return None

        return {
            "user_id": str(user.id),
            "email": user.email,
        }