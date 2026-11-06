"""Local API client for Rosières / Candy Simply-Fi dishwashers."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

import aiohttp

from .const import (
    MIN_REQUEST_INTERVAL_SECONDS,
    PROGRAMS,
    REQUEST_TIMEOUT_SECONDS,
)


class RosieresApiError(Exception):
    """Base local API error."""


class RosieresCannotConnect(RosieresApiError):
    """Raised when the dishwasher cannot be contacted."""


class RosieresInvalidResponse(RosieresApiError):
    """Raised when the dishwasher response cannot be decoded."""


class RosieresCommandError(RosieresApiError):
    """Raised when the dishwasher rejects a command."""


class RosieresLocalApi:
    """Async client for the local Simply-Fi HTTP API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        encryption_key: str,
    ) -> None:
        self._session = session
        self.host = host.strip()
        self._key = encryption_key.encode("utf-8")
        self._lock = asyncio.Lock()
        self._last_request = 0.0

        if len(self._key) != 16:
            raise ValueError("The Simply-Fi XOR key must contain exactly 16 bytes")

    @staticmethod
    def _xor(data: bytes, key: bytes) -> bytes:
        return bytes(value ^ key[index % len(key)] for index, value in enumerate(data))

    def _encrypt(self, plaintext: str) -> str:
        encrypted = self._xor(plaintext.encode("utf-8"), self._key)
        return encrypted.hex().upper()

    def _decrypt(self, body: str) -> dict[str, Any]:
        body = body.strip()

        # A few firmwares may answer with plain JSON even when encrypted=1.
        if body.startswith("{"):
            try:
                decoded = json.loads(body)
            except json.JSONDecodeError as err:
                raise RosieresInvalidResponse("Invalid plaintext JSON response") from err
            if not isinstance(decoded, dict):
                raise RosieresInvalidResponse("Unexpected JSON response type")
            return decoded

        try:
            encrypted = bytes.fromhex(body)
        except ValueError as err:
            raise RosieresInvalidResponse("Response is not hexadecimal") from err

        plaintext = self._xor(encrypted, self._key)
        try:
            decoded = json.loads(plaintext.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as err:
            raise RosieresInvalidResponse(
                "Unable to decrypt the response; check the XOR key"
            ) from err

        if not isinstance(decoded, dict):
            raise RosieresInvalidResponse("Unexpected JSON response type")
        return decoded

    async def _request(
        self,
        path: str,
        params: dict[str, str],
    ) -> dict[str, Any]:
        """Perform one throttled HTTP request and decode the encrypted body."""

        async with self._lock:
            elapsed = time.monotonic() - self._last_request
            wait_time = MIN_REQUEST_INTERVAL_SECONDS - elapsed
            if wait_time > 0:
                await asyncio.sleep(wait_time)

            url = f"http://{self.host}{path}"
            timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)

            try:
                async with self._session.get(
                    url,
                    params=params,
                    timeout=timeout,
                ) as response:
                    body = await response.text()
                    if response.status >= 400:
                        raise RosieresCannotConnect(
                            f"HTTP {response.status} returned by {self.host}"
                        )
            except (aiohttp.ClientError, TimeoutError) as err:
                raise RosieresCannotConnect(
                    f"Unable to reach dishwasher at {self.host}"
                ) from err
            finally:
                self._last_request = time.monotonic()

        return self._decrypt(body)

    async def async_get_status(self) -> dict[str, Any]:
        """Read dishwasher status.

        A retry is performed when the device temporarily answers BAD REQUEST,
        which is known to happen when Simply-Fi firmwares are queried too fast.
        """

        for attempt in range(2):
            data = await self._request(
                "/http-read.json",
                {"encrypted": "1"},
            )

            if isinstance(data.get("statusDWash"), dict):
                return data

            if data.get("response") == "BAD REQUEST" and attempt == 0:
                continue

            raise RosieresInvalidResponse(
                f"Unexpected status response: {data!r}"
            )

        raise RosieresInvalidResponse("Unable to obtain dishwasher status")

    async def async_write_plaintext(self, plaintext: str) -> None:
        """Send one local write command."""

        encrypted = self._encrypt(plaintext)
        data = await self._request(
            "/http-write.json",
            {
                "encrypted": "1",
                "data": encrypted,
            },
        )

        if data.get("response") != "SUCCESS":
            raise RosieresCommandError(
                f"Dishwasher rejected command: {data!r}"
            )

    async def async_start_program(
        self,
        program_name: str,
        *,
        extra_dry: bool = False,
        open_door: bool = False,
        half_load: bool = False,
        three_in_one: bool = False,
        eco: bool = False,
        delay_start: int = 0,
    ) -> None:
        """Start a program with the options selected in Home Assistant."""

        if program_name not in PROGRAMS:
            raise RosieresCommandError(f"Unknown program: {program_name}")

        if delay_start < 0 or delay_start > 23:
            raise RosieresCommandError("DelayStart must be between 0 and 23 hours")

        program = PROGRAMS[program_name]
        command = (
            f"DelayStart={delay_start}"
            f"&ExtraDry={1 if extra_dry else 0}"
            f"&OpenDoorOpt={1 if open_door else 0}"
            f"&TreinUno={1 if three_in_one else 0}"
            # Eco is only sent when requested, so the validated command
            # stays byte-for-byte identical when the option is off.
            f"{'&Eco=1' if eco else ''}"
            f"&Program={program['code']}"
            f"&MetaCarico={1 if half_load else 0}"
            "&OpzProg=0"
            f"&w1={program['w1']}"
            "&StartStop=1"
        )
        await self.async_write_plaintext(command)

    async def async_stop(self) -> None:
        """Reset/stop the current program."""

        await self.async_write_plaintext("Reset=1")
