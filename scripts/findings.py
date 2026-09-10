#!/usr/bin/env python3
"""findings.py — canonical findings lifecycle store and CLI (EX-06 completion).

Replaces hand-maintained markdown registers as the source of truth for finding
identity and lifecycle state. Doctrine-aligned design:

  - **Append-only event log** (`FINDINGS_STORE.jsonl`, JSONL). Nothing is ever
    rewritten; current state is a projection of events (doctrine §14: append
    updates, never rewrite history).
  - **IDs are minted by the store** (`FND-NNNN`, monotonic, never reused).
    Legacy register IDs (A-18, F-01, …) become *aliases* — collisions are
    structurally impossible.
  - **Fail-closed writes**: `closed` requires evidence; `deferred`/`no_go`
    require a reason; unknown finding IDs are rejected. Invalid state cannot
    enter the store.
  - **Multi-agent safe**: writes take an exclusive file lock on the store.
  - **Markdown is a generated view**, never the source (`render` →
    `Docs/review/FINDINGS_LIVE.md`, marked GENERATED — DO NOT EDIT).

Usage:
  python3 scripts/findings.py open --title "..." --priority P1 --actor agent-x
  python3 scripts/findings.py close FND-0003 --evidence "review/x.md#L10" --actor agent-x
  python3 scripts/findings.py defer FND-0005 --reason "..." --reopen-condition "..." --actor a
  python3 scripts/findings.py reverify FND-0005 --evidence "..." --actor a
  python3 scripts/findings.py import --alias A-18 --title "..." --source-register F --actor a
  python3 scripts/findings.py list [--status open] [--json]
  python3 scripts/findings.py show FND-0003            # ID or alias
  python3 scripts/findings.py render                   # regenerate FINDINGS_LIVE.md
  python3 scripts/findings.py validate [--max-age 45]  # CI gate: exits non-zero on violations

Store path: $FINDINGS_STORE_PATH, default Docs/review/FINDINGS_STORE.jsonl.
"""

from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import json
import re
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STORE = PROJECT_ROOT / "Docs" / "review" / "FINDINGS_STORE.jsonl"
DEFAULT_VIEW = PROJECT_ROOT / "Docs" / "review" / "FINDINGS_LIVE.md"

STATUS_TYPES = {"finding.imported", "finding.opened", "finding.closed", "finding.deferred", "finding.reopened"}
DISPOSITIONS = {"fixed", "wontfix", "superseded", "no_go"}
VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}
DATE_PATTERN_LENGTH = 10


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def store_path() -> Path:
    return Path(os.environ.get("FINDINGS_STORE_PATH", str(DEFAULT_STORE)))


class StoreError(RuntimeError):
    """Fail-closed validation error: the event is rejected, not written."""


# ---------------------------------------------------------------------------
# Event log I/O
# ---------------------------------------------------------------------------

def _read_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    events: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise StoreError(f"{path.name}:{lineno} corrupt JSONL: {exc}") from exc
    return events


def _append_event(path: Path, event: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def _validate_event(event: dict, prior_ids: set[str], prior_event_ids: set[int]) -> None:
    etype = event.get("type", "")
    fid = event.get("finding_id")
    required = {
        "finding.imported": ("title", "source_register"),
        "finding.opened": ("title",),
        "finding.closed": ("evidence", "disposition"),
        "finding.deferred": ("reason", "reopen_condition"),
        "finding.reopened": ("reason",),
        "finding.re_verified": ("evidence",),
        "finding.noted": ("text",),
        "alias.added": ("alias",),
    }
    if etype not in required:
        raise StoreError(f"unknown event type: {etype!r}")
    for field in required[etype]:
        if not str(event.get(field) or "").strip():
            raise StoreError(f"{etype}: missing required field '{field}'")
    if etype not in ("finding.imported", "finding.opened") and fid not in prior_ids:
        raise StoreError(f"{etype}: unknown finding_id {fid!r}")
    if event.get("disposition") and event["disposition"] not in DISPOSITIONS:
        raise StoreError(f"invalid disposition {event['disposition']!r}; use one of {sorted(DISPOSITIONS)}")
    if event.get("priority") and event["priority"] not in VALID_PRIORITIES:
        raise StoreError(f"invalid priority {event['priority']!r}; use one of {sorted(VALID_PRIORITIES)}")
    if "event_id" in event:
        if prior_event_ids and event["event_id"] != max(prior_event_ids) + 1:
            raise StoreError(f"event_id {event['event_id']} is not the next monotonic id")


# ---------------------------------------------------------------------------
# Projection
# ---------------------------------------------------------------------------

def _parse_date(value: str | None) -> dt.date | None:
    if not value:
        return None
    try:
        return dt.date.fromisoformat(str(value)[:DATE_PATTERN_LENGTH])
    except ValueError:
        return None


def project(events: list[dict]) -> dict[str, dict]:
    """Replay the event log into current per-finding state."""
    findings: dict[str, dict] = {}
    alias_map: dict[str, str] = {}
    for event in events:
        etype = event["type"]
        if etype in ("finding.imported", "finding.opened"):
            fid = event["finding_id"]
            findings[fid] = {
                "id": fid,
                "title": event.get("title", ""),
                "status": event.get("status", "open"),
                "disposition": event.get("disposition"),
                "priority": event.get("priority", "P2"),
                "aliases": [event["finding_id"]] + list(event.get("aliases", [])),
                "source_register": event.get("source_register", ""),
                "evidence": event.get("evidence", ""),
                "reopen_condition": event.get("reopen_condition", ""),
                "last_verified": event.get("last_verified") or event.get("ts", "")[:DATE_PATTERN_LENGTH],
                "notes": [event["text"]] if event.get("text") else [],
                "history": [(event["ts"], etype, event.get("evidence") or event.get("reason") or "")],
            }
            for alias in findings[fid]["aliases"]:
                alias_map[alias] = fid
            continue
        fid = event.get("finding_id")
        if fid not in findings:
            continue  # validated at write time; tolerated here for robustness
        state = findings[fid]
        state["history"].append((event["ts"], etype, event.get("evidence") or event.get("reason") or event.get("text") or ""))
        if etype in ("finding.closed", "finding.deferred", "finding.reopened"):
            state["status"] = "closed" if etype == "finding.closed" else ("deferred" if etype == "finding.deferred" else "open")
            if etype == "finding.closed":
                state["disposition"] = event.get("disposition")
            state["evidence"] = event.get("evidence") or state["evidence"]
            state["reopen_condition"] = event.get("reopen_condition") or state["reopen_condition"]
            state["last_verified"] = event["ts"][:DATE_PATTERN_LENGTH]
        elif etype == "finding.re_verified":
            state["last_verified"] = event["ts"][:DATE_PATTERN_LENGTH]
            state["evidence"] = event.get("evidence") or state["evidence"]
        elif etype == "finding.noted":
            state["notes"].append(event.get("text", ""))
        elif etype == "alias.added":
            alias = event.get("alias", "")
            if alias and alias not in state["aliases"]:
                state["aliases"].append(alias)
                alias_map[alias] = fid
    return findings


def resolve(findings: dict[str, dict], alias_map: dict[str, str], ref: str) -> str | None:
    if ref in findings:
        return ref
    return alias_map.get(ref)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def _mint_id(events: list[dict]) -> str:
    max_num = 0
    for event in events:
        fid = event.get("finding_id", "")
        if fid.startswith("FND-"):
            try:
                max_num = max(max_num, int(fid[4:]))
            except ValueError:
                continue
    return f"FND-{max_num + 1:04d}"


def cmd_open(args: argparse.Namespace) -> int:
    path = store_path()
    with _locked(path):
        events = _read_events(path)
        fid = _mint_id(events)
        event = {
            "event_id": len(events) + 1,
            "ts": _now(),
            "actor": args.actor,
            "type": "finding.opened",
            "finding_id": fid,
            "title": args.title,
            "priority": args.priority,
            "evidence": args.evidence or "",
        }
        _validate_event(event, {e.get("finding_id") for e in events}, {e.get("event_id", 0) for e in events})
        _append_event(path, event)
    print(f"opened {fid}: {args.title}")
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    path = store_path()
    with _locked(path):
        events = _read_events(path)
        known_ids = {e.get("finding_id") for e in events}
        known_aliases = {a for e in events for a in ([e.get("finding_id")] + e.get("aliases", []))}
        if args.alias in known_ids or args.alias in known_aliases:
            print(f"skip {args.alias}: already in store", file=sys.stderr)
            return 0
        fid = _mint_id(events)
        event = {
            "event_id": len(events) + 1,
            "ts": _now(),
            "actor": args.actor,
            "type": "finding.imported",
            "finding_id": fid,
            "alias": args.alias,
            "aliases": [args.alias],
            "title": args.title,
            "status": args.status,
            "priority": args.priority,
            "source_register": args.source_register,
            "evidence": args.evidence or "",
            "last_verified": args.last_verified or _now()[:DATE_PATTERN_LENGTH],
        }
        _validate_event(event, known_ids, {e.get("event_id", 0) for e in events})
        _append_event(path, event)
    print(f"imported {args.alias} -> {fid} [{args.status}]")
    return 0


def _status_change(args: argparse.Namespace, etype: str, extra: dict) -> int:
    path = store_path()
    with _locked(path):
        events = _read_events(path)
        findings = project(events)
        alias_map = {a: f["id"] for f in findings.values() for a in f["aliases"]}
        fid = resolve(findings, alias_map, args.finding_ref)
        if fid is None:
            print(f"ERROR: unknown finding {args.finding_ref!r}", file=sys.stderr)
            return 1
        event = {
            "event_id": len(events) + 1,
            "ts": _now(),
            "actor": args.actor,
            "type": etype,
            "finding_id": fid,
            **extra,
        }
        _validate_event(event, set(findings), {e.get("event_id", 0) for e in events})
        _append_event(path, event)
    print(f"{etype} -> {fid}")
    return 0


def cmd_close(args: argparse.Namespace) -> int:
    return _status_change(args, "finding.closed", {"evidence": args.evidence, "disposition": args.disposition})


def cmd_defer(args: argparse.Namespace) -> int:
    return _status_change(args, "finding.deferred", {"reason": args.reason, "reopen_condition": args.reopen_condition})


def cmd_reopen(args: argparse.Namespace) -> int:
    return _status_change(args, "finding.reopened", {"reason": args.reason})


def cmd_reverify(args: argparse.Namespace) -> int:
    return _status_change(args, "finding.re_verified", {"evidence": args.evidence})


def cmd_note(args: argparse.Namespace) -> int:
    return _status_change(args, "finding.noted", {"text": args.text})


def cmd_alias(args: argparse.Namespace) -> int:
    return _status_change(args, "alias.added", {"alias": args.alias})


def cmd_list(args: argparse.Namespace) -> int:
    findings = project(_read_events(store_path()))
    rows = sorted(findings.values(), key=lambda f: f["id"])
    if args.status:
        rows = [f for f in rows if f["status"] == args.status]
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    for f in rows:
        aliases = ",".join(a for a in f["aliases"] if a != f["id"])
        alias_str = f" (alias {aliases})" if aliases else ""
        print(f"{f['id']}{alias_str} [{f['status']}/{f['priority']}] verified {f['last_verified']} — {f['title'][:90]}")
    print(f"-- {len(rows)} finding(s)", file=sys.stderr)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    findings = project(_read_events(store_path()))
    alias_map = {a: f["id"] for f in findings.values() for a in f["aliases"]}
    fid = resolve(findings, alias_map, args.finding_ref)
    if fid is None:
        print(f"ERROR: unknown finding {args.finding_ref!r}", file=sys.stderr)
        return 1
    print(json.dumps(findings[fid], ensure_ascii=False, indent=2))
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    findings = project(_read_events(store_path()))
    rows = sorted(findings.values(), key=lambda f: f["id"])
    today = dt.date.today()
    stale = [
        f for f in rows
        if f["status"] == "open"
        and (today - (_parse_date(f["last_verified"]) or today)).days > args.max_age
    ]
    counts: dict[str, int] = {}
    for f in rows:
        counts[f["status"]] = counts.get(f["status"], 0) + 1

    lines = [
        "# Findings — Live View (GENERATED — DO NOT EDIT)",
        "",
        f"**Generated:** {_now()} by `scripts/findings.py render` — this file is a projection of the",
        f"append-only event store `{os.path.relpath(store_path(), PROJECT_ROOT)}`. **The store is canonical;**",
        "edit state only through the CLI (`open` / `close` / `defer` / `reverify` / `import`).",
        "",
        f"**Counts:** {len(rows)} findings — " + " · ".join(f"{k} {v}" for k, v in sorted(counts.items())) +
        f" · stale open (> {args.max_age}d): {len(stale)}",
        "",
        "## Open",
        "",
        "| ID | Aliases | Pri | Title | Last verified |",
        "|----|---------|-----|-------|---------------|",
    ]
    for f in rows:
        if f["status"] != "open":
            continue
        aliases = ", ".join(a for a in f["aliases"] if a != f["id"]) or "—"
        lines.append(f"| {f['id']} | {aliases} | {f['priority']} | {f['title'][:110]} | {f['last_verified']} |")
    lines += ["", "## Deferred", ""]
    deferred = [f for f in rows if f["status"] == "deferred"]
    if not deferred:
        lines.append("*(none)*")
    for f in deferred:
        lines.append(f"- **{f['id']}** {f['title'][:100]} — reopen when: {f['reopen_condition'] or '—'}")
    lines += ["", "## Closed (recent 25)", ""]
    closed = [f for f in rows if f["status"] == "closed"][-25:]
    if not closed:
        lines.append("*(none)*")
    for f in closed:
        lines.append(f"- **{f['id']}** [{f['disposition'] or 'closed'}] {f['title'][:100]} — evidence: {f['evidence'] or '—'}")
    if stale:
        lines += ["", "## Stale open findings (re-verify or close)", ""]
        for f in stale:
            lines.append(f"- **{f['id']}** last verified {f['last_verified']} — {f['title'][:90]}")
    lines.append("")
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"rendered {args.output} ({len(rows)} findings)")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """CI gate: fail-closed structural validation + staleness enforcement."""
    path = store_path()
    errors: list[str] = []
    warnings: list[str] = []
    try:
        events = _read_events(path)
    except StoreError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    seen_event_ids: set[int] = set()
    known_ids: set[str] = set()
    known_aliases: set[str] = set()
    for event in events:
        eid = event.get("event_id")
        if eid in seen_event_ids:
            errors.append(f"event {eid}: duplicate event_id")
        seen_event_ids.add(eid)
        try:
            _validate_event(event, set(known_ids), seen_event_ids - {eid})
        except StoreError as exc:
            errors.append(f"event {eid}: {exc}")
            continue
        known_ids.add(event.get("finding_id"))
        # `alias` and `aliases` may repeat the same value — dedupe per event
        # so an event is never its own duplicate.
        for alias in {a for a in [event.get("alias", "")] + event.get("aliases", []) if a}:
            if alias in known_aliases:
                errors.append(f"event {eid}: duplicate alias {alias!r}")
            known_aliases.add(alias)
    findings = project(events)
    today = dt.date.today()
    for f in findings.values():
        if f["status"] != "open":
            continue
        verified = _parse_date(f["last_verified"])
        if verified is None:
            warnings.append(f"{f['id']}: open with no parseable verification date")
        elif (today - verified).days > args.max_age:
            errors.append(f"{f['id']}: open finding stale ({(today - verified).days}d > {args.max_age}d) — re-verify or close")
    print(f"findings store: {len(events)} events, {len(findings)} findings — "
          + " · ".join(f"{k} {v}" for k, v in sorted((s, sum(1 for f in findings.values() if f['status'] == s)) for s in ('open', 'deferred', 'closed'))))
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    if errors:
        print(f"FAILED: {len(errors)} violation(s), {len(warnings)} warning(s)")
        return 1
    print(f"OK ({len(warnings)} warning(s))")
    return 0


class _locked:
    """Exclusive lock on a sentinel file next to the store (multi-agent writes)."""

    def __init__(self, path: Path):
        self._lock_path = path.with_suffix(path.suffix + ".lock")

    def __enter__(self):
        self._fh = self._lock_path.open("w")
        fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
        self._fh.close()
        return False




CLEAN_CHARS = ("~~", "**")

def _clean_cell(cell: str) -> str:
    text = cell
    for ch in CLEAN_CHARS:
        text = text.replace(ch, "")
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)  # [label](link) -> label
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _row_status(row_text: str) -> str:
    lowered = row_text.lower()
    if "no-go-for-now" in lowered or "deferred" in lowered or "conditional" in lowered:
        return "deferred"
    for marker in ("resolved", "fixed", "closed", "wontfix", "superseded", "no-go", "rejected", "solved", "executed", "delivered"):
        if marker in lowered:
            return "closed"
    return "open"


def _title_from_cells(cells: list[str]) -> str:
    for cell in cells[2:]:
        cleaned = _clean_cell(cell)
        if len(cleaned) >= 15 and not re.fullmatch(r"P[0-3]|—|closed", cleaned):
            return cleaned[:140]
    cleaned = _clean_cell(cells[1]) if len(cells) > 1 else "imported register row"
    return cleaned[:140] or "imported register row"


def cmd_migrate_registers(args: argparse.Namespace) -> int:
    """One-time bootstrap: import every table row from the given registers.

    All rows are imported (closed rows too, as terminal identities). Aliases
    keep their legacy IDs; on a cross-register collision the later row is
    namespaced `<alias>@<tag>` so no identity is lost. Open state is never
    dropped in favour of a terminal duplicate.
    """
    path = store_path()
    tag_by_register = {str(Path(r).name): args.tag or Path(r).stem for r in args.registers}
    imported = skipped = 0
    with _locked(path):
        events = _read_events(path)
        known_aliases: set[str] = {
            a for e in events for a in ([e.get("finding_id")] + e.get("aliases", []))
        }
        for register in args.registers:
            reg_path = Path(register)
            reg_name = reg_path.name
            doc_date_match = re.search(r"\d{4}-\d{2}-\d{2}", reg_path.read_text(encoding="utf-8")[:2000])
            doc_date = doc_date_match.group(0) if doc_date_match else _now()[:DATE_PATTERN_LENGTH]
            for line in reg_path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped.startswith("|"):
                    continue
                cells = [c.strip() for c in stripped.strip("|").split("|")]
                if not cells or set(cells[0]) <= {"-", ":", " "}:
                    continue
                id_match = re.match(r"^([A-Z]{1,6}-[0-9]{1,4}[a-z]?)\b", cells[0])
                if not id_match:
                    continue
                alias = id_match.group(1)
                row_text = stripped
                status = _row_status(row_text)
                title = _title_from_cells(cells)
                dates = re.findall(r"\d{4}-\d{2}-\d{2}", row_text)
                last_verified = max(dates) if dates else doc_date
                last_verified = max(last_verified, doc_date)
                pri_match = re.search(r"\bP([0-3])\b", row_text)
                priority = f"P{pri_match.group(1)}" if pri_match else "P2"
                if alias in known_aliases:
                    if status == "open":
                        alias = f"{alias}@{tag_by_register[reg_name]}"
                    else:
                        skipped += 1
                        continue
                fid = _mint_id(events)
                event = {
                    "event_id": len(events) + 1,
                    "ts": _now(),
                    "actor": args.actor,
                    "type": "finding.imported",
                    "finding_id": fid,
                    "alias": alias,
                    "aliases": [alias],
                    "title": title,
                    "status": status,
                    "priority": priority,
                    "source_register": reg_name,
                    "evidence": f"{reg_name} (frozen historical view)",
                    "last_verified": last_verified,
                }
                try:
                    _validate_event(event, set(), set())
                except StoreError as exc:
                    print(f"WARN skip {alias}: {exc}", file=sys.stderr)
                    continue
                events.append(event)
                known_aliases.add(alias)
                imported += 1
        for event in events:
            _append_event(path, event)
    print(f"migration complete: {imported} imported, {skipped} terminal duplicates skipped")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p_open = sub.add_parser("open", help="open a new finding (mints FND-NNNN)")
    p_open.add_argument("--title", required=True)
    p_open.add_argument("--priority", default="P2", choices=sorted(VALID_PRIORITIES))
    p_open.add_argument("--evidence", default="")
    p_open.add_argument("--actor", default=os.environ.get("USER", "unknown"))
    p_open.set_defaults(fn=cmd_open)

    p_imp = sub.add_parser("import", help="import a legacy register row (alias keeps the old ID)")
    p_imp.add_argument("--alias", required=True, help="legacy ID, e.g. A-18")
    p_imp.add_argument("--title", required=True)
    p_imp.add_argument("--status", default="open", choices=["open", "deferred", "closed"])
    p_imp.add_argument("--priority", default="P2", choices=sorted(VALID_PRIORITIES))
    p_imp.add_argument("--source-register", required=True)
    p_imp.add_argument("--evidence", default="")
    p_imp.add_argument("--last-verified", default="")
    p_imp.add_argument("--actor", default=os.environ.get("USER", "unknown"))
    p_imp.set_defaults(fn=cmd_import)

    for name, fn, extra in (
        ("close", cmd_close, [("--evidence", {"required": True}), ("--disposition", {"default": "fixed", "choices": sorted(DISPOSITIONS)})]),
        ("defer", cmd_defer, [("--reason", {"required": True}), ("--reopen-condition", {"required": True})]),
        ("reopen", cmd_reopen, [("--reason", {"required": True})]),
        ("reverify", cmd_reverify, [("--evidence", {"required": True})]),
        ("note", cmd_note, [("--text", {"required": True})]),
        ("alias", cmd_alias, [("--alias", {"required": True})]),
    ):
        p = sub.add_parser(name)
        p.add_argument("finding_ref")
        p.add_argument("--actor", default=os.environ.get("USER", "unknown"))
        for flag, kwargs in extra:
            p.add_argument(flag, **kwargs)
        p.set_defaults(fn=fn)

    p_list = sub.add_parser("list")
    p_list.add_argument("--status", choices=["open", "deferred", "closed"])
    p_list.add_argument("--json", action="store_true")
    p_list.set_defaults(fn=cmd_list)

    p_show = sub.add_parser("show")
    p_show.add_argument("finding_ref")
    p_show.set_defaults(fn=cmd_show)

    p_render = sub.add_parser("render")
    p_render.add_argument("--output", type=Path, default=DEFAULT_VIEW)
    p_render.add_argument("--max-age", type=int, default=45)
    p_render.set_defaults(fn=cmd_render)

    p_mig = sub.add_parser("migrate-registers", help="one-time bootstrap from markdown registers")
    p_mig.add_argument("registers", nargs="+", type=Path)
    p_mig.add_argument("--tag", default="", help="suffix tag for colliding aliases (default: register stem)")
    p_mig.add_argument("--actor", default=os.environ.get("USER", "unknown"))
    p_mig.set_defaults(fn=cmd_migrate_registers)

    p_val = sub.add_parser("validate")
    p_val.add_argument("--max-age", type=int, default=45)
    p_val.set_defaults(fn=cmd_validate)

    args = parser.parse_args(argv)
    try:
        return args.fn(args)
    except StoreError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
