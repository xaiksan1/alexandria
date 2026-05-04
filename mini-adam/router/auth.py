import os
import time
import jwt

_SECRET = os.environ["JWT_SECRET"]
_EXPIRY_SECONDS = 30


def sign_token(agent_id: str, command: str) -> str:
    """Sign a JWT token with agent_id and command claims.

    Token expires in _EXPIRY_SECONDS (30 seconds).
    """
    now = int(time.time())
    return jwt.encode(
        {"agent_id": agent_id, "command": command, "iat": now, "exp": now + _EXPIRY_SECONDS},
        _SECRET,
        algorithm="HS256",
    )
