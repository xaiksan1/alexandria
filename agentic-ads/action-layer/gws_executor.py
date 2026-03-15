"""GWS Recipe Executor — executes Google Workspace action recipes.

Reads recipe JSON from action-layer/gws_recipes/, substitutes template vars,
and calls the appropriate Google API. Raises on any failure — no silent fallback.

Required env vars:
  GOOGLE_APPLICATION_CREDENTIALS  path to service account JSON
  GWS_REVENUE_SHEET_ID            Google Sheets spreadsheet ID for revenue log
"""
import json
import os
import re
import sys
from pathlib import Path

RECIPES_DIR = Path(__file__).parent / "gws_recipes"


class GWSConfigError(Exception):
    """Raised when required credentials or config are missing."""


class GWSExecutor:
    """Execute GWS recipe JSON files against live Google APIs."""

    def __init__(self) -> None:
        creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not creds_path:
            raise GWSConfigError(
                "GOOGLE_APPLICATION_CREDENTIALS not set — "
                "provide path to service account JSON"
            )
        if not Path(creds_path).exists():
            raise GWSConfigError(
                f"Service account file not found: {creds_path}"
            )

        # Lazy imports so the module is importable without google libs installed
        # (tests mock at the method level)
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise GWSConfigError(
                "google-api-python-client not installed — "
                "run: pip install google-api-python-client google-auth"
            ) from exc

        scopes = [
            "https://www.googleapis.com/auth/chat.messages",
            "https://www.googleapis.com/auth/spreadsheets",
        ]
        credentials = service_account.Credentials.from_service_account_file(
            creds_path, scopes=scopes
        )
        self._chat   = build("chat",   "v1",    credentials=credentials)
        self._sheets = build("sheets", "v4",    credentials=credentials)

    def execute(self, recipe_name: str, context: dict) -> None:
        """Load and execute a named recipe, substituting context vars.

        Args:
            recipe_name: name matching a file in gws_recipes/ (without .json)
            context: dict of template variable values, e.g. {"vertical": "crypto"}

        Raises:
            FileNotFoundError: recipe JSON not found
            GWSConfigError: missing required env var (e.g. GWS_REVENUE_SHEET_ID)
            googleapiclient.errors.HttpError: API call failed
        """
        recipe_path = RECIPES_DIR / f"{recipe_name}.json"
        recipe = json.loads(recipe_path.read_text())

        # Inject env-sourced vars into context
        context = dict(context)
        context.setdefault("REVENUE_SHEET_ID", self._revenue_sheet_id())

        for step in recipe["steps"]:
            tool   = step["tool"]
            params = self._resolve(step["params"], context)

            if tool == "gws-chat-send":
                self._chat_send(params)
            elif tool == "gws-sheets-append":
                self._sheets_append(params)
            else:
                raise GWSConfigError(f"Unknown GWS tool: {tool!r}")

    # ── private ───────────────────────────────────────────────────────────────

    def _revenue_sheet_id(self) -> str:
        val = os.environ.get("GWS_REVENUE_SHEET_ID")
        if not val:
            raise GWSConfigError(
                "GWS_REVENUE_SHEET_ID not set — "
                "export the Google Sheets spreadsheet ID"
            )
        return val

    def _resolve(self, obj, context: dict):
        """Recursively substitute {var} placeholders in strings/lists/dicts."""
        if isinstance(obj, str):
            def _replace(m):
                key = m.group(1)
                if key not in context:
                    raise GWSConfigError(
                        f"Template variable {{{key}}} not provided in context"
                    )
                return str(context[key])
            return re.sub(r"\{(\w+)\}", _replace, obj)
        if isinstance(obj, list):
            return [self._resolve(item, context) for item in obj]
        if isinstance(obj, dict):
            return {k: self._resolve(v, context) for k, v in obj.items()}
        return obj

    def _chat_send(self, params: dict) -> None:
        space   = params["space"]
        message = params["message"]
        self._chat.spaces().messages().create(
            parent=f"spaces/{space}",
            body={"text": message},
        ).execute()
        print(f"[gws] Chat → {space}: {message[:60]}...", flush=True)

    def _sheets_append(self, params: dict) -> None:
        sheet_id = params["spreadsheet_id"]
        range_   = params["range"]
        values   = params["values"]
        self._sheets.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=range_,
            valueInputOption="USER_ENTERED",
            body={"values": [values]},
        ).execute()
        print(f"[gws] Sheets → {sheet_id} / {range_}: {values}", flush=True)
