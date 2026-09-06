"""Regression tests for loop-affine asyncpg pool checkouts."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import DisconnectionError

from spine_api.core.database import _reject_asyncpg_connection_from_other_loop


def test_checkout_accepts_connection_owned_by_running_loop() -> None:
    running_loop = asyncio.new_event_loop()
    try:
        async def exercise() -> None:
            driver = SimpleNamespace(_loop=asyncio.get_running_loop())
            dbapi_connection = SimpleNamespace(driver_connection=driver)
            _reject_asyncpg_connection_from_other_loop(dbapi_connection, object(), object())

        running_loop.run_until_complete(exercise())
    finally:
        running_loop.close()


def test_checkout_rejects_connection_owned_by_another_loop() -> None:
    stale_loop = asyncio.new_event_loop()
    current_loop = asyncio.new_event_loop()
    try:
        async def exercise() -> None:
            driver = SimpleNamespace(_loop=stale_loop)
            dbapi_connection = SimpleNamespace(driver_connection=driver)
            with pytest.raises(DisconnectionError, match="different event loop"):
                _reject_asyncpg_connection_from_other_loop(dbapi_connection, object(), object())

        current_loop.run_until_complete(exercise())
    finally:
        current_loop.close()
        stale_loop.close()


def test_checkout_ignores_non_loop_bound_driver() -> None:
    running_loop = asyncio.new_event_loop()
    try:
        async def exercise() -> None:
            dbapi_connection = SimpleNamespace(driver_connection=object())
            _reject_asyncpg_connection_from_other_loop(dbapi_connection, object(), object())

        running_loop.run_until_complete(exercise())
    finally:
        running_loop.close()
