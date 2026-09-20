import os
from functools import lru_cache

import httpx
from dotenv import load_dotenv
from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions


load_dotenv()


def _get_required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"{name} is missing. "
            f"Add {name} to your .env file."
        )

    return value


def _create_http_client() -> httpx.Client:
    """
    Shared HTTP client configured for HTTP/1.1.

    This avoids the HTTP/2 transport that was producing
    WinError 10035 during Supabase requests on Windows.
    """
    return httpx.Client(
        http2=False,
        follow_redirects=True,
    )


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """
    Regular application Supabase client.

    Uses the publishable key and is subject to RLS.
    """

    supabase_url = _get_required_env("SUPABASE_URL")
    supabase_key = _get_required_env("SUPABASE_PUBLISHABLE_KEY")

    options = ClientOptions(
        httpx_client=_create_http_client(),
    )

    return create_client(
        supabase_url,
        supabase_key,
        options=options,
    )


@lru_cache(maxsize=1)
def get_supabase_admin_client() -> Client:
    """
    Trusted backend/admin client.

    Uses the secret key and must never be exposed to the frontend.
    """

    supabase_url = _get_required_env("SUPABASE_URL")
    supabase_secret_key = _get_required_env("SUPABASE_SECRET_KEY")

    options = ClientOptions(
        httpx_client=_create_http_client(),
    )

    return create_client(
        supabase_url,
        supabase_secret_key,
        options=options,
    )


def set_authenticated_session(
    access_token: str,
    refresh_token: str,
) -> Client:
    """
    Attach a user's authenticated session to the regular Supabase client.

    After this, requests made through this client carry the user's
    authentication context, so Row Level Security can evaluate
    auth.uid().
    """

    if not access_token:
        raise ValueError("access_token cannot be empty.")

    if not refresh_token:
        raise ValueError("refresh_token cannot be empty.")

    client = get_supabase_client()

    client.auth.set_session(
        access_token,
        refresh_token,
    )

    return client