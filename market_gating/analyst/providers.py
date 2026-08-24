"""Analyst – LLM Provider Abstraction
======================================
Unified interface for calling LLMs from multiple providers:
Anthropic, OpenAI, Google Gemini, OpenRouter, Crof.ai, and local models.

Provider selection is driven by environment variables:

    ANALYST_PROVIDER    – one of: anthropic, openai, gemini, openrouter, crofai, local
    ANALYST_MODEL       – model name override (provider-specific default used if unset)

Authentication:

    ANTHROPIC_API_KEY   – Anthropic API key
    OPENAI_API_KEY      – OpenAI API key
    GEMINI_API_KEY      – Google Gemini API key (or use GOOGLE_APPLICATION_CREDENTIALS for OAuth)
    OPENROUTER_API_KEY  – OpenRouter API key
    CROFAI_API_KEY      – Crof.ai API key
    LOCAL_LLM_URL       – Base URL for local LLM (e.g. http://localhost:1234/v1)
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Lightweight .env loader (avoids needing python-dotenv dependency)
_env_file = Path(".env")
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ[_k.strip()] = _v.strip().strip("'\"")

# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class LLMProvider(ABC):
    """Abstract base for LLM providers."""

    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Send a system + user prompt and return the raw text response."""

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Send a prompt and parse the response as JSON.

        Strips markdown code fences if present.
        """
        raw = self.complete(system_prompt, user_prompt)
        # Strip markdown code fences (```json ... ```)
        text = raw.strip()
        if text.startswith("```"):
            # Remove opening fence
            first_nl = text.index("\n") if "\n" in text else 3
            text = text[first_nl + 1:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
        return json.loads(text)


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------

class AnthropicProvider(LLMProvider):
    """Anthropic (Claude) via the anthropic SDK."""

    def __init__(self, model: str | None = None, api_key: str | None = None):
        try:
            import anthropic
        except ImportError:
            raise ImportError("pip install anthropic  – required for Anthropic provider")
        self._model = model or os.getenv("ANALYST_MODEL", "claude-sonnet-4-20250514")
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        self._client = anthropic.Anthropic(api_key=key)

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return resp.content[0].text


class OpenAIProvider(LLMProvider):
    """OpenAI (GPT) via the openai SDK."""

    def __init__(self, model: str | None = None, api_key: str | None = None,
                 base_url: str | None = None):
        try:
            import openai
        except ImportError:
            raise ImportError("pip install openai  – required for OpenAI provider")
        self._model = model or os.getenv("ANALYST_MODEL", "gpt-4o")
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key and not base_url:
            raise ValueError("OPENAI_API_KEY not set")
        kwargs: dict[str, Any] = {}
        if key:
            kwargs["api_key"] = key
        if base_url:
            kwargs["base_url"] = base_url
        self._client = openai.OpenAI(**kwargs)

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=2048,
        )
        return resp.choices[0].message.content


class GeminiProvider(LLMProvider):
    """Google Gemini via raw REST API (supports API key and custom OAuth).

    Since the official SDK blocks OAuth for AI Studio, this implementation
    makes raw HTTP requests.

    Authentication priority:
        1. Explicit ``api_key`` argument or ``GEMINI_API_KEY`` env var.
        2. **Browser-based OAuth2 flow** using a custom Google Cloud Project.

    To use OAuth, you must provide your own client secrets at:
    ``~/.config/market_gating/client_secret.json``
    """

    _OAUTH_SCOPES = ["https://www.googleapis.com/auth/generative-language"]
    _CONFIG_DIR = Path.home() / ".config" / "market_gating"
    _CLIENT_SECRETS_FILE = _CONFIG_DIR / "client_secret.json"
    _CREDS_FILE = _CONFIG_DIR / "gemini_oauth_creds.json"

    def __init__(self, model: str | None = None, api_key: str | None = None):
        self._model = model or os.getenv("ANALYST_MODEL", "gemini-3.6-flash")
        self._api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._creds = None

        if self._api_key:
            logger.info("Gemini: using API key")
        else:
            logger.info("Gemini: attempting OAuth flow")
            self._creds = self._get_oauth_credentials()

    # ------------------------------------------------------------------
    # OAuth credential management
    # ------------------------------------------------------------------

    @classmethod
    def _get_oauth_credentials(cls):
        """Load cached OAuth creds, refresh if expired, or run browser flow."""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
        except ImportError:
            raise ImportError(
                "pip install google-auth-oauthlib requests  – required for OAuth"
            )

        creds = None
        # 1. Try loading cached credentials
        if cls._CREDS_FILE.exists():
            try:
                with open(cls._CREDS_FILE, "r") as f:
                    creds_data = json.load(f)
                creds = Credentials.from_authorized_user_info(creds_data, cls._OAUTH_SCOPES)
            except Exception as exc:
                logger.warning("Cached OAuth creds invalid: %s", exc)

        if creds and creds.valid:
            logger.info("Gemini OAuth: using cached credentials")
            return creds

        # 2. Try refreshing expired credentials
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                cls._save_credentials(creds)
                logger.info("Gemini OAuth: refreshed expired credentials")
                return creds
            except Exception as exc:
                logger.warning("Could not refresh token: %s", exc)

        # 3. Interactive Browser Flow
        if not cls._CLIENT_SECRETS_FILE.exists():
            raise FileNotFoundError(
                f"\n\n❌ Missing OAuth Client Secrets!\n"
                f"To use OAuth with Gemini AI Studio, you must supply your own Google Cloud credentials.\n\n"
                f"1. Go to Google Cloud Console (console.cloud.google.com)\n"
                f"2. Create a Project and enable the 'Generative Language API'\n"
                f"3. Go to APIs & Services -> OAuth consent screen (configure it as External)\n"
                f"4. Go to Credentials -> Create Credentials -> OAuth client ID (Type: Desktop App)\n"
                f"5. Download the JSON file and save it exactly here:\n"
                f"   {cls._CLIENT_SECRETS_FILE}\n\n"
                f"(Alternatively, just set GEMINI_API_KEY to skip OAuth completely.)\n"
            )

        print("\n🔐 Google OAuth: A browser window will open for you to sign in.")
        print("   (This only needs to happen once – credentials are cached locally.)\n")

        flow = InstalledAppFlow.from_client_secrets_file(
            str(cls._CLIENT_SECRETS_FILE), cls._OAUTH_SCOPES
        )
        try:
            creds = flow.run_local_server(port=0, prompt="consent", open_browser=True)
        except Exception:
            logger.info("Local server flow failed, trying console flow")
            creds = flow.run_console()

        cls._save_credentials(creds)
        print("✅ OAuth credentials saved. You won't need to sign in again.\n")
        return creds

    @classmethod
    def _save_credentials(cls, creds) -> None:
        """Persist OAuth credentials to disk."""
        cls._CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
        }
        cls._CREDS_FILE.write_text(json.dumps(data, indent=2))
        cls._CREDS_FILE.chmod(0o600)  # restrict permissions
        logger.info("OAuth credentials saved to %s", cls._CREDS_FILE)

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Call the Gemini API using raw HTTP requests."""
        import requests

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent"
        headers = {"Content-Type": "application/json"}

        # Inject Auth
        if self._api_key:
            url += f"?key={self._api_key}"
        elif self._creds:
            from google.auth.transport.requests import Request
            if self._creds.expired:
                self._creds.refresh(Request())
                self._save_credentials(self._creds)
            headers["Authorization"] = f"Bearer {self._creds.token}"
        else:
            raise RuntimeError("No authentication method available for Gemini.")

        # Gemini REST payload format
        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 2048,
                "responseMimeType": "application/json",
            }
        }

        resp = requests.post(url, headers=headers, json=payload)

        if resp.status_code != 200:
            raise RuntimeError(f"Gemini API error ({resp.status_code}): {resp.text}")

        data = resp.json()
        try:
            parts = data["candidates"][0]["content"]["parts"]
            # Find the first part that is not a thought
            text = ""
            for p in parts:
                if not p.get("thought", False):
                    text = p["text"]
                    break
            # Fallback to the last part if all else fails
            if not text and parts:
                text = parts[-1]["text"]
            return text
        except (KeyError, IndexError):
            raise RuntimeError(f"Unexpected response format from Gemini: {data}")



class OpenRouterProvider(LLMProvider):
    """OpenRouter – uses OpenAI-compatible API."""

    def __init__(self, model: str | None = None, api_key: str | None = None):
        self._model = model or os.getenv("ANALYST_MODEL", "anthropic/claude-sonnet-4-20250514")
        key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not key:
            raise ValueError("OPENROUTER_API_KEY not set")
        # Re-use OpenAI SDK with OpenRouter base URL
        self._inner = OpenAIProvider(
            model=self._model,
            api_key=key,
            base_url="https://openrouter.ai/api/v1",
        )

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        return self._inner.complete(system_prompt, user_prompt)


class CrofAIProvider(LLMProvider):
    """Crof.ai – uses OpenAI-compatible API."""

    def __init__(self, model: str | None = None, api_key: str | None = None):
        self._model = model or os.getenv("ANALYST_MODEL", "claude-sonnet-4-20250514")
        key = api_key or os.getenv("CROFAI_API_KEY")
        if not key:
            raise ValueError("CROFAI_API_KEY not set")
        self._inner = OpenAIProvider(
            model=self._model,
            api_key=key,
            base_url="https://api.crof.ai/v1",
        )

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        return self._inner.complete(system_prompt, user_prompt)


class LocalLLMProvider(LLMProvider):
    """Local LLM via any OpenAI-compatible server (LM Studio, Ollama, vLLM, etc.)."""

    def __init__(self, model: str | None = None, base_url: str | None = None):
        url = base_url or os.getenv("LOCAL_LLM_URL", "http://localhost:1234/v1")
        self._model = model or os.getenv("ANALYST_MODEL", "local-model")
        self._inner = OpenAIProvider(
            model=self._model,
            api_key="not-needed",
            base_url=url,
        )

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        return self._inner.complete(system_prompt, user_prompt)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_PROVIDERS: dict[str, type[LLMProvider]] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "openrouter": OpenRouterProvider,
    "crofai": CrofAIProvider,
    "local": LocalLLMProvider,
}


def get_provider(
    provider_name: str | None = None,
    model: str | None = None,
    **kwargs: Any,
) -> LLMProvider:
    """Instantiate an LLM provider.

    Parameters
    ----------
    provider_name : str | None
        Provider key (anthropic, openai, gemini, openrouter, crofai, local).
        Falls back to ``ANALYST_PROVIDER`` env var, then auto-detects from
        available API keys.
    model : str | None
        Model name override.
    **kwargs
        Passed through to the provider constructor.
    """
    name = (provider_name or os.getenv("ANALYST_PROVIDER", "")).lower().strip()

    # Auto-detect if not specified
    if not name:
        for env_key, pname in [
            ("ANTHROPIC_API_KEY", "anthropic"),
            ("OPENAI_API_KEY", "openai"),
            ("GEMINI_API_KEY", "gemini"),
            ("GOOGLE_APPLICATION_CREDENTIALS", "gemini"),
            ("OPENROUTER_API_KEY", "openrouter"),
            ("CROFAI_API_KEY", "crofai"),
            ("LOCAL_LLM_URL", "local"),
        ]:
            if os.getenv(env_key):
                name = pname
                logger.info("Auto-detected provider: %s (from %s)", name, env_key)
                break

    if not name:
        raise ValueError(
            "No LLM provider configured. Set ANALYST_PROVIDER or one of: "
            "ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, "
            "OPENROUTER_API_KEY, CROFAI_API_KEY, LOCAL_LLM_URL"
        )

    cls = _PROVIDERS.get(name)
    if cls is None:
        raise ValueError(
            f"Unknown provider '{name}'. Choose from: {', '.join(_PROVIDERS)}"
        )

    if model:
        kwargs["model"] = model
    return cls(**kwargs)
