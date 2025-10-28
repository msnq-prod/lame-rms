from __future__ import annotations

import time

import pytest

from app.auth.mfa import MFAVerifier


def test_mfa_secret_generation_unique() -> None:
    verifier = MFAVerifier()
    secret1 = verifier.generate_secret()
    secret2 = verifier.generate_secret()
    assert secret1 != secret2
    assert len(secret1) >= 16


def test_mfa_code_validation() -> None:
    verifier = MFAVerifier(interval=30, digits=6)
    secret = verifier.generate_secret()
    code = verifier.generate_code(secret)
    assert verifier.verify(secret, code)
    # Expired code should fail after window
    time.sleep(1)
    assert verifier.verify(secret, code, window=1)
    assert not verifier.verify(secret, "000000")


def test_invalid_digits_raise() -> None:
    with pytest.raises(ValueError):
        MFAVerifier(digits=5)
