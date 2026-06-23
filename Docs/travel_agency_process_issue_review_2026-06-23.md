# travel_agency_agent process issue review

Date: 2026-06-23

## Question

Is the repo-root `app.py` the old Streamlit app rather than the current B2B app?

## Verdict

Yes. The root `app.py` was the legacy Streamlit workbench, and it has now been removed from the repo.

## Evidence

- The deleted repo-root `app.py` was a Streamlit app and imported `streamlit as st`.
- [`README.md`](../README.md#L112) lists `spine_api/server.py` and `frontend/` as the runtime surfaces and now treats the Streamlit prototype as retired.
- [`dev.sh`](../dev.sh#L3) starts `spine_api` and the Next.js frontend; it does not launch `app.py`.
- [`Docs/FRONTEND_PRODUCT_SPEC_FULL_2026-04-15.md`](./FRONTEND_PRODUCT_SPEC_FULL_2026-04-15.md#L349) says there is `No Streamlit layer in the implementation path`.
- [`Docs/status/NEXTJS_IMPLEMENTATION_TRACK_2026-04-15.md`](./status/NEXTJS_IMPLEMENTATION_TRACK_2026-04-15.md#L9) says the implementation path is `Next.js App Router only` and that no Streamlit runtime path is active.

## Supersession Analysis

- Candidate: repo-root `app.py`
- Replacement/canonical path: `spine_api/server.py` + `frontend/`
- Supersession status: product-path superseded and deleted

The legacy Streamlit workbench is no longer part of the repository, so the product docs and runtime entrypoints now agree on the FastAPI + Next.js path.

## Practical Conclusion

- The current B2B app is not `app.py`.
- The current B2B app is the FastAPI backend plus the Next.js frontend.
- `app.py` has been retired; no remaining runtime path should reference it.
