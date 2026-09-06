from __future__ import annotations

import json
import asyncio
import os

import pytest

from tools import status_vocabulary_report as report_tool
from tools.status_vocabulary_report import scan_file_store


def test_scan_file_store_separates_missing_null_and_tokens(tmp_path):
    (tmp_path / "a.json").write_text(
        json.dumps({"status": " Active "}), encoding="utf-8"
    )
    (tmp_path / "b.json").write_text(json.dumps({"status": None}), encoding="utf-8")
    (tmp_path / "c.json").write_text(
        json.dumps({"trip_id": "missing"}), encoding="utf-8"
    )
    (tmp_path / "d.json").write_text("not-json", encoding="utf-8")

    result = scan_file_store(tmp_path)

    assert result["files_scanned"] == 4
    assert result["missing_status_key"] == 1
    assert result["explicit_null_status"] == 1
    assert result["malformed_files"] == 1
    assert result["tokens"][0] == {
        "raw": " Active ",
        "count": 1,
        "normalized": "active",
        "canonical": "active",
        "alias_covered": True,
        "writer_provenance": "not_evaluated",
    }


def test_scan_file_store_preserves_unmapped_token_without_guessing_writer(tmp_path):
    (tmp_path / "a.json").write_text(
        json.dumps({"status": "escalated"}), encoding="utf-8"
    )
    result = scan_file_store(tmp_path)
    token = result["tokens"][0]
    assert token["canonical"] == "escalated"
    assert token["alias_covered"] is False
    assert token["writer_provenance"] == "not_evaluated"
    assert "known_trip_status_writer" not in token
    assert "foreign_vocabulary_candidate" not in token


def test_missing_root_is_unavailable_not_empty(tmp_path):
    with pytest.raises(ValueError, match="file_root_unavailable"):
        scan_file_store(tmp_path / "absent")


def test_empty_directory_is_successfully_observed(tmp_path):
    result = scan_file_store(tmp_path)
    assert result["observation_status"] == "complete"
    assert result["rows_counted"] == 0
    assert result["tokens"] == []


def test_invalid_values_are_not_string_coerced_into_vocabulary(tmp_path):
    payloads = [
        [],
        {"status": []},
        {"status": {}},
        {"status": True},
        {"status": 3},
        {"status": ""},
        {"status": "   "},
    ]
    for number, payload in enumerate(payloads):
        (tmp_path / f"{number}.json").write_text(json.dumps(payload), encoding="utf-8")
    result = scan_file_store(tmp_path)
    assert result["invalid_record_shape"] == 1
    assert result["invalid_status_type"] == 4
    assert result["missing_status_key"] == 0
    assert result["blank_status"] == 2
    assert result["rows_counted"] == 6
    assert [token["raw"] for token in result["tokens"]] == ["", "   "]


def test_symlinked_json_is_not_read_outside_scanned_directory(tmp_path):
    root = tmp_path / "trips"
    root.mkdir()
    outside = tmp_path / "private.json"
    outside.write_text('{"status": "private-marker"}', encoding="utf-8")
    (root / "link.json").symlink_to(outside)
    result = scan_file_store(root)
    assert result["unsafe_files_skipped"] == 1
    assert result["observation_status"] == "partial"
    assert result["tokens"] == []


AGENCY_ID = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows

    def mappings(self):
        return self

    def one(self):
        return self.rows[0]


class RlsSession:
    """Small driver-boundary fake; real report/query/RLS helper remain exercised."""

    def __init__(self):
        self.statements = []
        self.agency = None
        self.read_only = False
        self.rolled_back = False
        self.block_query = False
        self.bypass_rls = False
        self.query_count = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def begin(self):
        self.statements.append(("BEGIN", {}))

    async def rollback(self):
        self.rolled_back = True
        self.agency = None

    async def execute(self, statement, parameters=None):
        sql = str(statement)
        self.statements.append((sql, parameters or {}))
        if sql == "SET TRANSACTION READ ONLY":
            self.read_only = True
        elif "set_config('app.current_agency_id'" in sql:
            assert ", true)" in sql
            self.agency = parameters["agency_id"]
        elif "FROM pg_roles" in sql:
            return FakeResult(
                [
                    {
                        "current_user": "runtime",
                        "is_superuser": False,
                        "bypasses_rls": self.bypass_rls,
                    }
                ]
            )
        elif "FROM pg_class" in sql:
            return FakeResult(
                [
                    {
                        "table_name": "trips",
                        "owner": "runtime",
                        "rls_enabled": True,
                        "force_rls": True,
                    }
                ]
            )
        elif "FROM trips" in sql:
            self.query_count += 1
            if self.block_query:
                await asyncio.Event().wait()
            assert statement.compile().params.get("agency_id_1") == AGENCY_ID
            # Matches FORCE RLS's empty visibility when context was forgotten.
            return FakeResult(
                [("active", 3), (None, 2)] if self.agency == AGENCY_ID else []
            )
        return FakeResult([])


@pytest.fixture
def sql_session(monkeypatch):
    from spine_api.core import database

    session = RlsSession()
    monkeypatch.setattr(database, "async_session_maker", lambda: session)
    return session


@pytest.mark.asyncio
async def test_sql_sets_transaction_local_tenant_before_read_and_rolls_back(
    sql_session,
):
    result = await report_tool.scan_sql_store(AGENCY_ID)
    assert result["rows_counted"] == 5
    assert result["explicit_null_status"] == 2
    assert result["status_values_counted"] == 3
    assert result["rls_enforced_for_runtime_role"] is True
    assert sql_session.statements[0][0] == "BEGIN"
    assert sql_session.statements[1][0] == "SET TRANSACTION READ ONLY"
    assert any("statement_timeout" in sql for sql, _ in sql_session.statements)
    assert sql_session.read_only and sql_session.rolled_back
    assert sql_session.agency is None


@pytest.mark.asyncio
@pytest.mark.parametrize("agency", [None, "", "not-a-uuid"])
async def test_sql_requires_explicit_valid_tenant_before_access(sql_session, agency):
    with pytest.raises(ValueError, match="agency_id_required_or_invalid"):
        await report_tool.scan_sql_store(agency)
    assert sql_session.statements == []


@pytest.mark.asyncio
async def test_sql_refuses_bypass_role_without_reading_trips(sql_session):
    sql_session.bypass_rls = True
    with pytest.raises(ValueError, match="sql_rls_not_enforced"):
        await report_tool.scan_sql_store(AGENCY_ID)
    assert sql_session.query_count == 0
    assert sql_session.rolled_back


@pytest.mark.asyncio
async def test_sql_deadline_cancels_and_rolls_back(sql_session):
    sql_session.block_query = True
    with pytest.raises(ValueError, match="sql_timeout"):
        await report_tool.scan_sql_store(AGENCY_ID, timeout_seconds=0.02)
    assert sql_session.rolled_back


@pytest.mark.asyncio
async def test_report_sanitizes_failure_and_preserves_successful_source(
    monkeypatch, tmp_path
):
    async def fail(*_args, **_kwargs):
        raise RuntimeError("postgresql://operator:SECRET@private-db/customer")

    monkeypatch.setattr(report_tool, "scan_sql_store", fail)
    args = report_tool.build_parser().parse_args(
        ["--backend", "both", "--agency-id", AGENCY_ID, "--file-root", str(tmp_path)]
    )
    result = await report_tool._build_report(args)
    assert result["schema_version"] == 2
    assert result["observation_status"] == "partial"
    assert result["sources"][0]["observation_status"] == "complete"
    assert result["errors"] == [{"source": "sql_store", "code": "sql_unavailable"}]
    serialized = json.dumps(result)
    assert "SECRET" not in serialized
    assert "private-db" not in serialized
    assert "command" not in result


def test_cli_rejects_unscoped_sql_before_running(monkeypatch, capsys, sql_session):
    monkeypatch.setattr("sys.argv", ["status_vocabulary_report", "--backend", "sql"])
    with pytest.raises(SystemExit) as exc:
        report_tool.main()
    assert exc.value.code == 2
    assert "--agency-id is required" in capsys.readouterr().err


def test_cli_missing_file_root_is_structured_failure(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(
        "sys.argv",
        [
            "status_vocabulary_report",
            "--backend",
            "file",
            "--file-root",
            str(tmp_path / "absent"),
        ],
    )
    assert report_tool.main() == 2
    result = json.loads(capsys.readouterr().out)
    assert result["observation_status"] == "unavailable"
    assert result["errors"] == [
        {"source": "file_store", "code": "file_root_unavailable"}
    ]


@pytest.mark.parametrize("kind", ["file", "symlink"])
def test_root_must_be_real_directory(tmp_path, kind):
    root = tmp_path / "not-a-directory"
    if kind == "file":
        root.write_text("private data", encoding="utf-8")
    else:
        target = tmp_path / "target"
        target.mkdir()
        root.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="file_root_unavailable"):
        scan_file_store(root)


def test_fifo_is_skipped_without_blocking(tmp_path):
    os.mkfifo(tmp_path / "queue.json")
    result = scan_file_store(tmp_path)
    assert result["unsafe_files_skipped"] == 1
    assert result["observation_status"] == "partial"


def test_json_named_directory_is_skipped_and_all_descriptors_closed(
    tmp_path, monkeypatch
):
    (tmp_path / "nested.json").mkdir()
    descriptors = []
    original_open = os.open

    def recording_open(*args, **kwargs):
        fd = original_open(*args, **kwargs)
        descriptors.append(fd)
        return fd

    monkeypatch.setattr(os, "open", recording_open)
    result = scan_file_store(tmp_path)
    for fd in descriptors:
        with pytest.raises(OSError):
            os.fstat(fd)
    assert result["unsafe_files_skipped"] == 1
    assert result["observation_status"] == "partial"


def test_source_files_are_preserved_byte_for_byte(tmp_path):
    original = {
        "ok.json": b'{"status":"  Active ", "private":"preserve"}',
        "bad.json": b"\xff",
        "missing.json": b"{}",
    }
    for name, data in original.items():
        (tmp_path / name).write_bytes(data)
    result = scan_file_store(tmp_path)
    assert result["malformed_files"] == 1
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == original


@pytest.mark.asyncio
@pytest.mark.parametrize("timeout", [0, -1, 121, float("nan"), float("inf")])
async def test_invalid_sql_deadline_never_accesses_database(sql_session, timeout):
    with pytest.raises(ValueError, match="sql_timeout_invalid"):
        await report_tool.scan_sql_store(AGENCY_ID, timeout_seconds=timeout)
    assert sql_session.statements == []


@pytest.mark.asyncio
async def test_sql_query_failure_rolls_back(sql_session, monkeypatch):
    execute = sql_session.execute

    async def failing_execute(statement, parameters=None):
        if "FROM trips" in str(statement):
            raise RuntimeError("query rejected")
        return await execute(statement, parameters)

    monkeypatch.setattr(sql_session, "execute", failing_execute)
    with pytest.raises(RuntimeError, match="query rejected"):
        await report_tool.scan_sql_store(AGENCY_ID)
    assert sql_session.rolled_back
    assert sql_session.agency is None


def test_cli_partial_file_scan_has_nonzero_exit(monkeypatch, capsys, tmp_path):
    (tmp_path / "invalid.json").write_text('{"status":false}', encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        ["status_vocabulary_report", "--backend", "file", "--file-root", str(tmp_path)],
    )
    assert report_tool.main() == 2
    result = json.loads(capsys.readouterr().out)
    assert result["observation_status"] == "partial"


@pytest.mark.asyncio
async def test_sql_survives_unavailable_file_source(sql_session, tmp_path):
    args = report_tool.build_parser().parse_args(
        [
            "--backend",
            "both",
            "--agency-id",
            AGENCY_ID,
            "--file-root",
            str(tmp_path / "absent"),
        ]
    )
    result = await report_tool._build_report(args)
    assert result["observation_status"] == "partial"
    assert result["sources"][0]["source"] == "sql_store"
    assert result["sources"][0]["rows_counted"] == 5
