"""
spine_api.services.field_merge — Canonical merge precedence + provenance for trip packet fields.

Why this exists (register N-3 / F-27 class): `/optimistic-sync` previously applied
client-supplied field updates as a blind last-write-wins overwrite
(`packet[key] = value`). A customer reply could silently clobber an
operator-corrected field (and vice versa) with no conflict record and no
provenance trail — the same silent-truth-loss class the findings register
tracks for approvals (F-03) and memory (F-13), but at the trip-field level.

Precedence contract:
- Preference fields (what the customer wants): the customer's own voice wins.
  Customer > operator > machines (tool/provider/system never override wants).
- Commercial/structured fields (budget numbers, dates, party, identity):
  provider facts are authoritative (provider > operator > tool/system > customer).
  An operator correction still outranks a customer restatement; a deterministic
  pipeline value outranks a customer restatement but not an operator's.
- Unknown fields: operator > customer (conservative default; conflicts are
  still recorded so the classification can be corrected later).

Actor vocabulary (TS-04, 2026-09-09): operator, customer, system, tool,
provider. Only operator/customer are client-submittable on the
/optimistic-sync surface; system/tool/provider are internal-writer roles
(server-side provider adapters, deterministic tools, platform bookkeeping)
and require ``allow_internal_actors=True`` so a client can never claim
provider rank. Stored provenance is always parsed against the full
vocabulary — a stored 'provider' actor keeps its rank in later merges.

Provenance is stored under the reserved packet key `_field_provenance` as
{field: {actor, actor_id, at, superseded}}. Every applied overwrite records
the value it replaced; every rejected update is returned as a conflict with
the kept value — nothing is ever silently lost on either side.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

ACTOR_OPERATOR = "operator"
ACTOR_CUSTOMER = "customer"
ACTOR_SYSTEM = "system"
ACTOR_TOOL = "tool"
ACTOR_PROVIDER = "provider"

# Canonical vocabulary for recorded/stored provenance actors.
VALID_ACTOR_ROLES = (ACTOR_OPERATOR, ACTOR_CUSTOMER, ACTOR_SYSTEM, ACTOR_TOOL, ACTOR_PROVIDER)

# Roles a client may claim on the /optimistic-sync surface. Everything else
# (system/tool/provider) is an internal-writer role and folds to operator
# when supplied externally — a client must not be able to claim provider rank.
CLIENT_ACTOR_ROLES = (ACTOR_OPERATOR, ACTOR_CUSTOMER)

# Reserved packet metadata key — never accept it from client updates.
PROVENANCE_KEY = "_field_provenance"

# Preference fields: the customer's own stated wants outrank operator edits.
PREFERENCE_FIELDS = frozenset(
    {
        "preferences",
        "hotel_preference",
        "accommodation",
        "room_preference",
        "bed_preference",
        "seat_preference",
        "airline_preference",
        "dietary",
        "dietary_requirements",
        "activity_preferences",
        "pace_preference",
        "special_requests",
        "notes",
        "travel_style",
    }
)

# Commercial/structured fields: operator-corrected values outrank customer restatements.
COMMERCIAL_FIELDS = frozenset(
    {
        "budget",
        "budget_max",
        "budget_min",
        "budget_scope",
        "budget_currency",
        "budget_flexibility",
        "start_date",
        "end_date",
        "dates",
        "duration_nights",
        "date_flexibility",
        "party_size",
        "travelers",
        "adults",
        "children",
        "destination",
        "destination_candidates",
        "origin",
        "customer_name",
        "customer_contact",
    }
)

_PRECEDENCE_RANK = {
    # preference class: customer outranks operator; machines never override wants
    "preference": {ACTOR_CUSTOMER: 3, ACTOR_OPERATOR: 2, ACTOR_PROVIDER: 1, ACTOR_TOOL: 1, ACTOR_SYSTEM: 1},
    # commercial class: provider facts are authoritative, then operator,
    # then deterministic tools/system, then customer restatements
    "commercial": {ACTOR_PROVIDER: 4, ACTOR_OPERATOR: 3, ACTOR_TOOL: 2, ACTOR_SYSTEM: 2, ACTOR_CUSTOMER: 1},
}


def _field_class(field_name: str) -> str:
    if field_name in PREFERENCE_FIELDS:
        return "preference"
    return "commercial"


def normalize_actor_role(actor_role: Optional[str], *, allow_internal: bool = False) -> str:
    """Map a request-supplied actor role onto the canonical vocabulary.

    Unknown/absent roles default to the operator. With ``allow_internal=True``
    (server-side writers only) the full vocabulary — including the
    system/tool/provider internal-writer roles — is accepted; on the client
    surface those roles fold to operator so a client can never claim
    provider precedence.
    """
    role = (actor_role or "").strip().lower()
    valid = VALID_ACTOR_ROLES if allow_internal else CLIENT_ACTOR_ROLES
    if role in valid:
        return role
    return ACTOR_OPERATOR


@dataclass(slots=True)
class MergeConflict:
    """A requested update that was rejected by precedence — value preserved, not lost."""

    field: str
    requested_value: Any
    kept_value: Any
    kept_actor: str
    incoming_actor: str
    field_class: str
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "requested_value": self.requested_value,
            "kept_value": self.kept_value,
            "kept_actor": self.kept_actor,
            "incoming_actor": self.incoming_actor,
            "field_class": self.field_class,
            "reason": self.reason,
        }


@dataclass(slots=True)
class FieldMergeResult:
    merged_packet: Dict[str, Any]
    applied_fields: List[str] = field(default_factory=list)
    conflicts: List[MergeConflict] = field(default_factory=list)
    provenance: Dict[str, Dict[str, Any]] = field(default_factory=dict)


def resolve_field_merge(
    packet: Dict[str, Any],
    updates: Dict[str, Any],
    actor_role: Optional[str],
    actor_id: Optional[str],
    now_iso: str,
    allow_internal_actors: bool = False,
) -> FieldMergeResult:
    """Merge `updates` into `packet` under the precedence contract.

    Returns a new packet dict (input not mutated). Applied overwrites record
    provenance including the superseded value; precedence rejections are
    returned as conflicts with the kept value.

    ``allow_internal_actors=True`` is for server-side writers (provider
    adapters, deterministic tools, platform bookkeeping) that need to write
    under the system/tool/provider roles. Client-facing callers must leave it
    False so claimed internal roles fold to operator.
    """
    role = normalize_actor_role(actor_role, allow_internal=allow_internal_actors)
    merged = dict(packet)
    existing_provenance = dict(packet.get(PROVENANCE_KEY) or {})
    applied: List[str] = []
    conflicts: List[MergeConflict] = []

    for field_name, incoming_value in (updates or {}).items():
        if field_name == PROVENANCE_KEY:
            conflicts.append(
                MergeConflict(
                    field=field_name,
                    requested_value="<reserved>",
                    kept_value=None,
                    kept_actor=ACTOR_SYSTEM,
                    incoming_actor=role,
                    field_class="reserved",
                    reason="provenance metadata key is system-owned",
                )
            )
            continue

        field_class = _field_class(field_name)
        prior = existing_provenance.get(field_name)
        incoming_rank = _PRECEDENCE_RANK[field_class].get(role, 1)
        if prior is not None:
            # Stored actors are parsed against the FULL vocabulary: a stored
            # 'provider'/'tool' actor keeps its rank in later comparisons even
            # when the current writer is a client-restricted caller.
            stored_actor = normalize_actor_role(prior.get("actor"), allow_internal=True)
            stored_rank = _PRECEDENCE_RANK[field_class].get(stored_actor, 1)
            if incoming_rank < stored_rank:
                conflicts.append(
                    MergeConflict(
                        field=field_name,
                        requested_value=incoming_value,
                        kept_value=merged.get(field_name),
                        kept_actor=stored_actor,
                        incoming_actor=role,
                        field_class=field_class,
                        reason=(
                            f"{field_class} field last set by higher-precedence "
                            f"'{stored_actor}'; '{role}' update rejected"
                        ),
                    )
                )
                continue
        elif (
            field_class == "commercial"
            and merged.get(field_name) not in (None, "", [], {})
            and incoming_rank < _PRECEDENCE_RANK["commercial"][ACTOR_OPERATOR]
        ):
            # Pre-merge-system (unattributed) commercial value: conservative default
            # treats it as operator-owned rather than letting a lower-rank writer
            # (customer restatement, or a tool/system writer — review cycle 1)
            # clobber it. Provider facts (rank above operator) still apply.
            # Blank commercial fields stay fillable by anyone.
            conflicts.append(
                MergeConflict(
                    field=field_name,
                    requested_value=incoming_value,
                    kept_value=merged.get(field_name),
                    kept_actor=ACTOR_OPERATOR,
                    incoming_actor=role,
                    field_class=field_class,
                    reason=(
                        "commercial field has an unattributed stored value; "
                        f"'{role}' update rejected under operator-conservative default"
                    ),
                )
            )
            continue

        superseded = merged.get(field_name) if field_name in merged else None
        merged[field_name] = incoming_value
        applied.append(field_name)
        existing_provenance[field_name] = {
            "actor": role,
            "actor_id": actor_id,
            "at": now_iso,
            "superseded": superseded,
        }

    merged[PROVENANCE_KEY] = existing_provenance
    return FieldMergeResult(
        merged_packet=merged,
        applied_fields=applied,
        conflicts=conflicts,
        provenance=existing_provenance,
    )
