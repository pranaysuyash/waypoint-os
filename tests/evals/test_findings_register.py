"""Tests for the canonical findings-register lifecycle gate."""

from pathlib import Path
import datetime as dt

import pytest

from scripts.check_findings_register import check, parse_register


@pytest.fixture(autouse=True)
def fixed_review_date(monkeypatch):
    class ReviewDate(dt.date):
        @classmethod
        def today(cls):
            return cls(2026, 9, 5)

    monkeypatch.setattr("scripts.check_findings_register.dt.date", ReviewDate)


def _write_register(path: Path, role: str, finding_id: str = "E-01") -> None:
    path.write_text(
        "\n".join(
            [
                "# Findings",
                "**Date:** 2026-09-03",
                f"**Role:** {role}",
                "",
                "| ID | Status |",
                "|---|---|",
                f"| {finding_id} | open; last verified 2026-09-03 |",
            ]
        )
    )


def test_companion_registers_may_repeat_ids(tmp_path: Path):
    canonical = tmp_path / "canonical.md"
    companion = tmp_path / "companion.md"
    _write_register(canonical, "canonical lifecycle register")
    _write_register(companion, "historical planning companion")

    errors, warnings, counts = check([canonical, companion], max_age_days=45)

    assert errors == []
    assert warnings == []
    assert counts["open"] == 1  # Historical aliases are not current lifecycle rows.


def test_multiple_canonical_registers_are_rejected(tmp_path: Path):
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    _write_register(first, "canonical lifecycle register")
    _write_register(second, "canonical lifecycle register")

    errors, _, _ = check([first, second], max_age_days=45)

    assert any("multiple canonical findings registers" in error for error in errors)
    assert any("appears in multiple canonical registers" in error for error in errors)


def test_undeclared_register_is_fail_safe_canonical(tmp_path: Path):
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    _write_register(first, "canonical lifecycle register")
    second.write_text(first.read_text().replace("**Role:** canonical lifecycle register\n", ""))

    errors, _, _ = check([first, second], max_age_days=45)

    assert any("multiple canonical findings registers" in error for error in errors)


def test_formatted_ids_and_status_column_are_authoritative(tmp_path: Path):
    path = tmp_path / "canonical.md"
    path.write_text(
        "# Findings\n**Date:** 2026-09-05\n"
        "| ID | Finding | Live status |\n|---|---|---|\n"
        "| **NEW-01** | fail-closed code is fixed | **OPEN** |\n"
        "| `NEW-02` | formerly open, references 2030-01-01 | ✅ **CLOSED** 2026-09-04 |\n"
        "| NEW-03 | fixed subtask | ⚠️ **PARTIAL** — still open |\n"
    )
    rows, _ = parse_register(path)
    assert [(row["id"], row["status"]) for row in rows] == [
        ("NEW-01", "open"), ("NEW-02", "closed"), ("NEW-03", "open")
    ]
    assert str(rows[1]["last_verified"]) == "2026-09-04"


def test_missing_or_unknown_canonical_status_fails_closed(tmp_path: Path):
    path = tmp_path / "canonical.md"
    path.write_text(
        "# Findings\n**Date:** 2026-09-05\n"
        "| ID | Finding |\n|---|---|\n| **NEW-01** | already fixed? |\n\n"
        "| ID | Status |\n|---|---|\n| NEW-02 | banana |\n"
    )
    errors, _, counts = check([path], max_age_days=45)
    assert counts["open"] == 2
    assert sum("status" in error.lower() for error in errors) == 2


def test_closed_words_do_not_hide_deferred_or_partial_status(tmp_path: Path):
    path = tmp_path / "canonical.md"
    path.write_text(
        "# Findings\n**Date:** 2026-09-05\n"
        "| ID | Status |\n|---|---|\n"
        "| NG-01 | no-go-for-now; fixed prerequisite |\n"
        "| A-01 | partially fixed; implementation still open |\n"
        "| A-02 | open; fail-closed implemented |\n"
        "| A-03 | deferred; earlier bug resolved |\n"
    )
    rows, _ = parse_register(path)
    assert [row["status"] for row in rows] == ["deferred", "open", "open", "deferred"]


def test_formatted_duplicate_ids_report_actual_line(tmp_path: Path):
    path = tmp_path / "canonical.md"
    path.write_text(
        "# Findings\n**Date:** 2026-09-05\n"
        "| ID | Status |\n|---|---|\n"
        "| **A-01** | open |\n| A-01 | open |\n"
    )
    errors, _, _ = check([path], max_age_days=45)
    assert any(":6 duplicate finding ID A-01 (first at line 5)" in error for error in errors)


def test_explicit_verification_date_is_not_refreshed_by_doc_or_evidence(tmp_path: Path):
    path = tmp_path / "canonical.md"
    path.write_text(
        "# Findings\n**Date:** 2026-09-05\n"
        "| ID | Finding | Status | Last verified |\n|---|---|---|---|\n"
        "| A-01 | evidence planned 2030-01-01 | open | 2020-01-01 |\n"
    )
    errors, _, _ = check([path], max_age_days=45)
    assert any("last verified 2020-01-01" in error for error in errors)


def test_historical_missing_status_is_preserved_but_not_counted(tmp_path: Path):
    path = tmp_path / "historical.md"
    path.write_text(
        "# Archive\n**Role:** historical planning companion\n"
        "| ID | Task |\n|---|---|\n| A-01 | fix it |\n"
    )
    errors, warnings, counts = check([path], max_age_days=45)
    assert errors == []
    assert warnings == []
    assert sum(counts.values()) == 0


def test_escaped_pipe_does_not_shift_status_column(tmp_path: Path):
    path = tmp_path / "canonical.md"
    path.write_text(
        "# Findings\n**Date:** 2026-09-05\n"
        "| ID | Finding | Status |\n|---|---|---|\n"
        "| A-01 | old \\| closed | open |\n"
    )
    rows, _ = parse_register(path)
    assert rows[0]["status"] == "open"


def test_empty_canonical_register_cannot_pass(tmp_path: Path):
    path = tmp_path / "empty.md"
    path.write_text("# Findings\n**Role:** canonical lifecycle register\n")
    errors, _, _ = check([path], max_age_days=45)
    assert any("no finding rows" in error for error in errors)


def test_unknown_role_cannot_silently_remove_rows_from_counts(tmp_path: Path):
    path = tmp_path / "bad_role.md"
    _write_register(path, "canoncal lifecycle register")
    errors, _, _ = check([path], max_age_days=45)
    assert any("unrecognized register role" in error for error in errors)


def test_fenced_examples_do_not_become_findings(tmp_path: Path):
    path = tmp_path / "examples.md"
    path.write_text(
        "# Findings\n**Date:** 2026-09-05\n"
        "```markdown\n| ID | Status |\n|---|---|\n| A-01 | closed |\n```\n\n"
        "| ID | Status |\n|---|---|\n| A-01 | open |\n"
    )
    rows, _ = parse_register(path)
    assert [(r["id"], r["status"]) for r in rows] == [("A-01", "open")]


@pytest.mark.parametrize("date", ["2026-99-99", "2030-01-01"])
def test_invalid_or_future_verification_dates_fail_actionably(tmp_path: Path, date: str):
    path = tmp_path / "date.md"
    path.write_text(
        "# Findings\n**Date:** 2026-09-05\n"
        f"| ID | Status | Last verified |\n|---|---|---|\n| A-01 | open | {date} |\n"
    )
    errors, _, _ = check([path], max_age_days=45)
    assert any("date" in error.lower() for error in errors)


def test_canonical_composite_id_requires_one_identity_per_row(tmp_path: Path):
    path = tmp_path / "canonical.md"
    _write_register(path, "canonical lifecycle register", "A-01 / A-02")
    errors, _, _ = check([path], max_age_days=45)
    assert any("single finding ID" in error for error in errors)


@pytest.mark.parametrize("identity", ["a-02", "ABCDE-03", "A-12345", ""])
def test_every_row_in_canonical_id_table_is_validated(tmp_path: Path, identity: str):
    path = tmp_path / "canonical.md"
    _write_register(path, "canonical lifecycle register")
    path.write_text(path.read_text() + f"\n| {identity} | open |\n")
    errors, _, counts = check([path], max_age_days=45)
    assert counts["open"] == 2
    assert any("single finding ID" in error for error in errors)


def test_fenced_role_cannot_demote_canonical_document(tmp_path: Path):
    path = tmp_path / "canonical.md"
    path.write_text(
        "# Findings\n**Date:** 2026-09-05\n"
        "```markdown\n**Role:** historical planning companion\n```\n"
        "| ID | Status |\n|---|---|\n| A-01 | open |\n"
    )
    errors, _, counts = check([path], max_age_days=45)
    assert not errors
    assert counts["open"] == 1


def test_later_status_prose_date_does_not_renew_explicit_verification(tmp_path: Path):
    path = tmp_path / "canonical.md"
    _write_register(path, "canonical lifecycle register")
    path.write_text(path.read_text().replace(
        "open; last verified 2026-09-03",
        "open; last verified 2020-01-01; plan updated 2026-09-05",
    ))
    errors, _, _ = check([path], max_age_days=45)
    assert any("last verified 2020-01-01" in error for error in errors)


def test_empty_explicit_verification_date_is_not_silently_refreshed(tmp_path: Path):
    path = tmp_path / "canonical.md"
    path.write_text(
        "# Findings\n**Date:** 2026-09-05\n"
        "| ID | Status | Last verified |\n|---|---|---|\n"
        "| A-01 | open; last verified 2020-01-01 | |\n"
    )
    errors, _, _ = check([path], max_age_days=45)
    assert any("verification date" in error for error in errors)


@pytest.mark.parametrize("value", ["yesterday", "2020-01-01 / 2026-09-05"])
def test_invalid_explicit_date_does_not_fall_back(tmp_path: Path, value: str):
    path = tmp_path / "canonical.md"
    path.write_text(
        "# Findings\n**Date:** 2026-09-05\n"
        "| ID | Status | Last verified |\n|---|---|---|\n"
        f"| A-01 | open | {value} |\n"
    )
    errors, _, _ = check([path], max_age_days=45)
    assert any("verification date" in error for error in errors)


def test_status_explanation_is_not_a_status_column(tmp_path: Path):
    path = tmp_path / "canonical.md"
    path.write_text(
        "# Findings\n**Date:** 2026-09-05\n"
        "| ID | Status explanation | Live status (2026-08-31) |\n|---|---|---|\n"
        "| A-01 | fixed bug explanation | open |\n"
    )
    errors, _, counts = check([path], max_age_days=45)
    assert not errors
    assert counts["open"] == 1


def test_duplicate_status_headers_fail(tmp_path: Path):
    path = tmp_path / "canonical.md"
    path.write_text(
        "# Findings\n**Date:** 2026-09-05\n"
        "| ID | Status | Status |\n|---|---|---|\n"
        "| A-01 | closed | open |\n"
    )
    errors, _, _ = check([path], max_age_days=45)
    assert any("Status column" in error for error in errors)


@pytest.mark.parametrize("metadata", [
    "```markdown\n**Date:** 2026-09-05\n```",
    "See planned work 2026-09-05",
    "> **Date:** 2026-09-05",
])
def test_examples_and_prose_do_not_supply_document_date(tmp_path: Path, metadata: str):
    path = tmp_path / "canonical.md"
    path.write_text(
        f"# Findings\n{metadata}\n"
        "| ID | Status |\n|---|---|\n| A-01 | open |\n"
    )
    errors, warnings, counts = check([path], max_age_days=45)
    assert not errors
    assert counts["open"] == 1
    assert any("no verifiable date" in warning for warning in warnings)


@pytest.mark.parametrize("metadata", [
    "**Role:** canonical\n**Role:** historical",
    "**Date:** 2026-09-05\n**Date:** 2020-01-01",
])
def test_duplicate_metadata_is_rejected(tmp_path: Path, metadata: str):
    path = tmp_path / "canonical.md"
    path.write_text(
        f"# Findings\n{metadata}\n"
        "| ID | Status |\n|---|---|\n| A-01 | open |\n"
    )
    errors, _, _ = check([path], max_age_days=45)
    assert any("duplicate" in error.lower() for error in errors)


def test_unrelated_table_after_blank_is_not_a_findings_table(tmp_path: Path):
    path = tmp_path / "canonical.md"
    _write_register(path, "canonical lifecycle register")
    path.write_text(path.read_text() + "\n\n| Dimension | Meaning |\n|---|---|\n| Owner | team |\n")
    errors, _, counts = check([path], max_age_days=45)
    assert not errors
    assert counts["open"] == 1


def test_status_planning_prose_without_delimiter_cannot_supply_verification(tmp_path: Path):
    path = tmp_path / "canonical.md"
    path.write_text(
        "# Findings\n**Date:** 2020-01-01\n"
        "| ID | Status |\n|---|---|\n| A-01 | open pending planned work 2026-09-05 |\n"
    )
    errors, _, _ = check([path], max_age_days=45)
    assert any("last verified 2020-01-01" in error for error in errors)


@pytest.mark.parametrize("identity", ["-", "ID"])
def test_body_identity_cannot_masquerade_as_table_structure(tmp_path: Path, identity: str):
    path = tmp_path / "canonical.md"
    _write_register(path, "canonical lifecycle register")
    path.write_text(path.read_text() + f"\n| {identity} | open |\n")
    errors, _, counts = check([path], max_age_days=45)
    assert counts["open"] == 2
    assert any("single finding ID" in error for error in errors)


def test_html_comment_cannot_demote_document(tmp_path: Path):
    path = tmp_path / "canonical.md"
    path.write_text(
        "# Findings\n<!--\n**Role:** historical\n-->\n**Date:** 2026-09-05\n"
        "| ID | Status |\n|---|---|\n| A-01 | open |\n"
    )
    errors, _, counts = check([path], max_age_days=45)
    assert not errors
    assert counts["open"] == 1


def test_id_header_requires_complete_separator(tmp_path: Path):
    path = tmp_path / "canonical.md"
    path.write_text("# Findings\n| ID | Status |\n|---|open|\n| A-01 | open |\n")
    errors, _, _ = check([path], max_age_days=45)
    assert any("separator" in error for error in errors)


def test_inline_comments_preserve_visible_rows_and_following_rows(tmp_path: Path):
    path = tmp_path / "canonical.md"
    _write_register(path, "canonical lifecycle register")
    path.write_text(path.read_text() + "\n| A-02 | open <!-- note --> |\n| A-03 | open |\n")
    errors, _, counts = check([path], max_age_days=45)
    assert not errors
    assert counts["open"] == 3


def test_inline_comments_preserve_visible_metadata(tmp_path: Path):
    path = tmp_path / "historical.md"
    _write_register(path, "historical planning companion <!-- archive -->")
    errors, _, counts = check([path], max_age_days=45)
    assert not errors
    assert sum(counts.values()) == 0
