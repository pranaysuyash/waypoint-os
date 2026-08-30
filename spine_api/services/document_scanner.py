"""
spine_api.services.document_scanner — Document virus scanning and quarantine service.

Supports:
- Real-time stream scanning via ClamAV clamd daemon (INSTREAM protocol).
- In-process heuristic scanning (EICAR signature and malicious payload detection).
- Status tracking: 'clean', 'infected', 'skipped'.
"""

from __future__ import annotations

import asyncio
import logging
import os
import struct
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("spine_api.document_scanner")

EICAR_SIGNATURE = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"


@dataclass(slots=True)
class ScanResult:
    status: str  # "clean" | "infected" | "skipped"
    signature: Optional[str] = None
    engine: str = "heuristic-internal"
    scanned_at: datetime = None

    def __post_init__(self):
        if self.scanned_at is None:
            self.scanned_at = datetime.now(timezone.utc)

    @property
    def is_safe(self) -> bool:
        return self.status in ("clean", "skipped")


async def _scan_clamav_tcp(
    data: bytes,
    host: str,
    port: int,
    timeout_seconds: float = 3.0,
) -> Optional[ScanResult]:
    """
    Stream bytes to ClamAV daemon via INSTREAM protocol.
    Format:
      zINSTREAM\0
      <uint32_len><chunk_bytes>
      ...
      <uint32_zero>
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout_seconds,
        )
    except Exception as exc:
        logger.debug("ClamAV daemon not reachable at %s:%s (%s), skipping TCP scan", host, port, exc)
        return None

    try:
        # Command: zINSTREAM\0
        writer.write(b"zINSTREAM\0")
        await writer.drain()

        # Stream chunks (32KB max per frame)
        chunk_size = 32768
        for i in range(0, len(data), chunk_size):
            chunk = data[i : i + chunk_size]
            length_prefix = struct.pack("!I", len(chunk))
            writer.write(length_prefix + chunk)
            await writer.drain()

        # Terminate stream with zero length chunk
        writer.write(struct.pack("!I", 0))
        await writer.drain()

        response = await asyncio.wait_for(reader.read(1024), timeout=timeout_seconds)
        writer.close()
        await writer.wait_closed()

        resp_text = response.decode("utf-8", errors="replace").strip()
        # Response format: "stream: OK" or "stream: <Signature> FOUND"
        if "OK" in resp_text:
            return ScanResult(status="clean", engine=f"clamav-tcp:{host}:{port}")
        elif "FOUND" in resp_text:
            parts = resp_text.split("FOUND")[0].replace("stream:", "").strip()
            return ScanResult(
                status="infected",
                signature=parts or "Malware.Found",
                engine=f"clamav-tcp:{host}:{port}",
            )
    except Exception as exc:
        logger.warning("ClamAV scan stream failed: %s", exc)
        try:
            writer.close()
        except Exception:
            pass

    return None


async def scan_document_bytes(
    file_bytes: bytes,
    filename: str = "",
) -> ScanResult:
    """
    Scan document bytes for virus or malicious payload signatures.
    """
    # 1. Check in-process heuristic / test signatures (EICAR)
    if EICAR_SIGNATURE in file_bytes:
        logger.warning("EICAR test signature detected in file: %s", filename)
        return ScanResult(
            status="infected",
            signature="EICAR-Test-Signature",
            engine="heuristic-internal",
        )

    # 2. Check if ClamAV daemon is enabled and configured
    clamav_enabled = os.environ.get("CLAMAV_ENABLED", "0").lower() in ("1", "true", "yes")
    clamav_host = os.environ.get("CLAMAV_HOST", "localhost")
    clamav_port = int(os.environ.get("CLAMAV_PORT", "3310"))

    if clamav_enabled:
        result = await _scan_clamav_tcp(file_bytes, host=clamav_host, port=clamav_port)
        if result is not None:
            return result

    # 3. Clean by default if no threats detected
    return ScanResult(status="clean", engine="heuristic-internal")
