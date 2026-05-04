# tests/test_auth.py
import time
import pytest
import jwt as pyjwt
from router.auth import sign_token
from runner.auth import verify_token


def test_sign_produces_valid_jwt():
    token = sign_token("agent-abc", "spawn")
    raw = pyjwt.decode(token, options={"verify_signature": False})
    assert raw["agent_id"] == "agent-abc"
    assert raw["command"] == "spawn"
    assert "iat" in raw
    assert "exp" in raw


def test_sign_and_verify_roundtrip():
    token = sign_token("agent-xyz", "route")
    claims = verify_token(token)
    assert claims["agent_id"] == "agent-xyz"
    assert claims["command"] == "route"


def test_expired_token_rejected():
    expired = pyjwt.encode(
        {"agent_id": "x", "command": "y", "iat": 1, "exp": 1},
        "test-secret-mini-adam",
        algorithm="HS256",
    )
    with pytest.raises(pyjwt.InvalidTokenError):
        verify_token(expired)


def test_wrong_secret_rejected():
    forged = pyjwt.encode(
        {"agent_id": "x", "command": "y", "iat": int(time.time()), "exp": int(time.time()) + 30},
        "WRONG-SECRET",
        algorithm="HS256",
    )
    with pytest.raises(pyjwt.InvalidTokenError):
        verify_token(forged)


def test_tampered_token_rejected():
    token = sign_token("agent-abc", "spawn")
    tampered = token[:-4] + "XXXX"
    with pytest.raises(pyjwt.InvalidTokenError):
        verify_token(tampered)
