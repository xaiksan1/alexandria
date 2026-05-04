import json
from pathlib import Path
from typing import TypedDict


SYSTEM_EMOJIS: dict[str, str] = {
    "🤖": "spawn",
    "📡": "route",
    "📊": "state",
}


class ParsedCommand(TypedDict):
    system_action: str | None
    custom_action: str | None
    emoji_key: str
    model: str
    timeout: int
    payload: str


def parse_emoji(emoji_str: str, commands_path: Path) -> ParsedCommand:
    """
    Parse emoji commands, with system emojis taking priority over custom ones.

    System emojis:
      - 🤖 → spawn (spawn new agent)
      - 📡 → route (route command)
      - 📊 → state (query state)

    Custom emojis are loaded from commands_path (JSON file).
    """
    # Check system emojis first (they take priority)
    for emoji, action in SYSTEM_EMOJIS.items():
        if emoji_str.startswith(emoji):
            return ParsedCommand(
                system_action=action,
                custom_action=None,
                emoji_key=emoji,
                model="claude-sonnet-4-6",
                timeout=30,
                payload=emoji_str[len(emoji):].strip(),
            )

    # Check custom emojis from file
    commands = _load_commands(commands_path)
    if emoji_str in commands:
        entry = commands[emoji_str]
        return ParsedCommand(
            system_action=None,
            custom_action=entry["action"],
            emoji_key=emoji_str,
            model=entry.get("model", "claude-sonnet-4-6"),
            timeout=entry.get("timeout", 30),
            payload="",
        )

    raise ValueError(f"Unknown emoji command: {emoji_str!r}")


def _load_commands(commands_path: Path) -> dict:
    """Load custom emoji commands from JSON file. Returns empty dict if file missing."""
    if not commands_path.exists():
        return {}
    return json.loads(commands_path.read_text(encoding="utf-8"))
