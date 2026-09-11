#!/bin/bash
# CI gate: fail if bare TripStore.get_trip( or FileTripStore.get_trip( is found in router files
# (excludes get_trip_for_agency, get_trip_for_public_access, _get_trip_internal, and tests)
set -e

results=$(grep -rn 'TripStore\.get_trip(' spine_api/routers/ --include='*.py' | grep -v 'get_trip_for_agency' | grep -v 'get_trip_for_public' | grep -v '_get_trip_internal' || true)

if [ -n "$results" ]; then
  echo "ERROR: Unscoped TripStore.get_trip() found in router files:"
  echo "$results"
  echo "Use get_trip_for_agency() or get_trip_for_public_access() instead."
  exit 1
fi

echo "OK: No unscoped TripStore.get_trip() calls in router files."

# FND-0259 (2026-09-11): routers must derive agency scope via the canonical
# auth dependency (get_current_agency_id), never from a raw client-supplied
# X-Agency-ID Header parameter. The canonical dependency honors the header
# only under pytest/auth-bypass.
header_results=$(grep -rn 'alias="X-Agency-ID"' spine_api/routers/ --include='*.py' || true)

if [ -n "$header_results" ]; then
  echo "ERROR: Raw X-Agency-ID Header parameters found in router files:"
  echo "$header_results"
  echo "Use agency_id: str = Depends(get_current_agency_id) instead (JWT-derived; header honored only under pytest/auth-bypass)."
  exit 1
fi

echo "OK: No raw X-Agency-ID header parameters in router files."
