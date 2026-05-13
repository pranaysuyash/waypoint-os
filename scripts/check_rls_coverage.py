#!/usr/bin/env python3
"""
CI guard: verify every SQLAlchemy model with agency_id is RLS-protected or exempted.

Exit 0 if coverage is complete.
Exit 1 if any model with agency_id is missing from both RLS_TENANT_TABLES
       and RLS_EXCLUDED_AGENCY_TABLES.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> None:
    # Import all model modules so every mapper registers with Base
    import spine_api.models.tenant  # noqa: F401
    import spine_api.models.audit  # noqa: F401
    import spine_api.models.frontier  # noqa: F401
    from spine_api.models.tenant import Base
    from spine_api.core.rls import RLS_TENANT_TABLES, RLS_EXCLUDED_AGENCY_TABLES

    # Discover all models with agency_id columns
    all_tables = set()
    for mapper in Base.registry.mappers:
        table = mapper.local_table
        if table is not None and "agency_id" in table.c:
            all_tables.add(table.name)

    protected = set(RLS_TENANT_TABLES)
    exempted = set(RLS_EXCLUDED_AGENCY_TABLES.keys())

    unprotected = all_tables - protected - exempted
    extra_protected = protected - all_tables - {"trip_routing_states"}
    extra_exempted = exempted - all_tables

    errors = []

    if unprotected:
        errors.append(
            f"Tables with agency_id but no RLS coverage: {sorted(unprotected)}.\n"
            "  Add to RLS_TENANT_TABLES (for RLS policies) or "
            "RLS_EXCLUDED_AGENCY_TABLES (with rationale)."
        )

    if extra_exempted:
        errors.append(
            f"Tables in RLS_EXCLUDED_AGENCY_TABLES but no agency_id column: "
            f"{sorted(extra_exempted)}.\n"
            "  Remove from RLS_EXCLUDED_AGENCY_TABLES."
        )

    if errors:
        print("RLS coverage check FAILED:\n")
        for error in errors:
            print(f"  {error}\n")
        sys.exit(1)

    print(f"RLS coverage check passed: {len(protected)} protected, {len(exempted)} exempted, {len(all_tables)} total with agency_id")


if __name__ == "__main__":
    main()
