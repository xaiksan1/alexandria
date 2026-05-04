import os
import jwt

_SECRET = os.environ["JWT_SECRET"]


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token.

    Returns the decoded claims as a dictionary.
    Raises jwt.InvalidTokenError if token is invalid, tampered, or expired.
    """
    return jwt.decode(token, _SECRET, algorithms=["HS256"])
