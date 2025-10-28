from __future__ import annotations

import base64
import os
import struct
import time
from dataclasses import dataclass
from hashlib import sha1
import hmac


@dataclass(slots=True)
class MFADevice:
    """Registered MFA device containing shared secret."""

    user_id: str
    secret: str
    issuer: str
    label: str


class MFAVerifier:
    """Implements Time-based One-Time Password (TOTP) verification."""

    def __init__(self, *, interval: int = 30, digits: int = 6) -> None:
        if digits not in (6, 7, 8):
            raise ValueError("digits must be 6, 7 or 8")
        self._interval = interval
        self._digits = digits

    def generate_secret(self, length: int = 20) -> str:
        """Return a Base32 encoded secret."""

        random_bytes = os.urandom(length)
        return base64.b32encode(random_bytes).decode("utf-8").rstrip("=")

    def provisioning_uri(self, device: MFADevice) -> str:
        """Return otpauth URI for QR code generators."""

        label = device.label.replace(" ", "%20")
        issuer = device.issuer.replace(" ", "%20")
        return (
            f"otpauth://totp/{issuer}:{label}?secret={device.secret}&issuer={issuer}&period={self._interval}&digits={self._digits}"
        )

    def _time_counter(self, for_time: float | None = None) -> int:
        return int((for_time or time.time()) // self._interval)

    def generate_code(self, secret: str, for_time: float | None = None) -> str:
        """Generate a code for the provided secret."""

        counter = self._time_counter(for_time)
        key = base64.b32decode(self._normalize_secret(secret), casefold=True)
        msg = struct.pack(">Q", counter)
        h = hmac.new(key, msg, sha1).digest()
        offset = h[-1] & 0x0F
        truncated = h[offset : offset + 4]
        code_int = struct.unpack(">I", truncated)[0] & 0x7FFFFFFF
        code = code_int % (10**self._digits)
        return f"{code:0{self._digits}d}"

    def verify(self, secret: str, code: str, *, window: int = 1, at_time: float | None = None) -> bool:
        """Verify ``code`` allowing +/- ``window`` intervals."""

        if not code.isdigit() or len(code) != self._digits:
            return False
        counter = self._time_counter(at_time)
        for offset in range(-window, window + 1):
            calculated = self.generate_code(secret, for_time=((counter + offset) * self._interval))
            if hmac.compare_digest(calculated, code):
                return True
        return False

    @staticmethod
    def _normalize_secret(secret: str) -> str:
        padding = '=' * ((8 - len(secret) % 8) % 8)
        return secret.upper() + padding


__all__ = ["MFAVerifier", "MFADevice"]
