"""Extraction quality report CLI.

Runs provider smoke tests and prints per-provider status/latency metrics.
Does NOT print field values — only match counts and metadata.

Usage:
    python tools/extraction_quality_report.py
    python tools/extraction_quality_report.py --smoke-test
    python tools/extraction_quality_report.py --model-chain "gemini-2.5-flash,gpt-5.4-nano"
    python tools/extraction_quality_report.py --json --output report.json
"""

import argparse
import json
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _ensure_env():
    """Set required env flags if not already set."""
    os.environ.setdefault("EXTRACTION_SMOKE_TEST", "1")
    app_env = os.environ.get("APP_ENV", "production")
    if app_env == "production":
        print("Error: APP_ENV=production — smoke test blocked", file=sys.stderr)
        sys.exit(1)
    os.environ.setdefault("APP_ENV", "test")


def run_smoke(args):
    """Run provider smoke test and return results."""
    from src.extraction.smoke_test import run_smoke_test_sync

    model_chain = args.model_chain
    if model_chain:
        os.environ["EXTRACTION_MODEL_CHAIN"] = model_chain

    result = run_smoke_test_sync()

    if "error" in result and not result.get("results"):
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {result['error']}")
        return result

    if not args.json:
        _print_smoke_report(result)
    else:
        output = json.dumps(result, indent=2, default=str)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Report written to {args.output}")
        else:
            print(output)

    return result


def _print_smoke_report(result: dict):
    """Print human-readable smoke test report."""
    results = result.get("results", [])
    chain = result.get("chain", [])

    print("Extraction Smoke Test Report")
    print("=" * 40)
    if chain:
        print(f"Chain: {' -> '.join(chain)}")
    print(f"Date: {_today()}")
    print()

    if not results:
        print("No providers tested.")
        return

    print("Provider Results:")
    for r in results:
        status_marker = "PASS" if r.status == "ok" else "FAIL"
        line = f"  {r.provider:20s} {r.model:25s} [{status_marker}]"
        if r.latency_ms is not None:
            line += f"  latency: {r.latency_ms}ms"
        if r.fields_found is not None:
            line += f"  fields: {r.fields_found}"
        if r.error_code:
            line += f"  error: {r.error_code}"
        print(line)

    total = result.get("total", len(results))
    passed = result.get("passed", sum(1 for r in results if r.status == "ok"))
    failed = result.get("failed", sum(1 for r in results if r.status == "error"))
    print()
    print(f"Overall: {passed}/{total} passed, {failed} failed")


def _today() -> str:
    from datetime import date
    return date.today().isoformat()


def main():
    parser = argparse.ArgumentParser(description="Extraction quality report")
    parser.add_argument("--smoke-test", action="store_true", help="Run smoke test only (default)")
    parser.add_argument("--model-chain", type=str, help="Override EXTRACTION_MODEL_CHAIN")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--output", type=str, help="Write JSON report to file")
    args = parser.parse_args()

    _ensure_env()
    result = run_smoke(args)

    if result.get("failed", 0) > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
