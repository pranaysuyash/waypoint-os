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
