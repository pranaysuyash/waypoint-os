#!/usr/bin/env python3
"""Build a lightweight living graph for autoresearch, memory, and learning docs.

The goal is to turn the repo's scattered research and feedback-loop documents into
one navigable, additive artifact that agents can read before planning changes.

Outputs:
  - Markdown graph summary for humans/agents
  - JSON graph data for downstream tooling
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


KEYWORD_CLUSTERS: dict[str, list[str]] = {
    "autoresearch": [
        "autoresearch",
        "eval harness",
        "mutation loop",
        "offline optimization",
        "prompt registry",
        "composite score",
    ],
    "feedback_learning": [
        "feedback",
        "learning",
        "override",
        "post-trip",
        "improvement",
        "retention",
        "memory",
    ],
    "graph_memory": [
        "graph",
        "lineage",
        "taste graph",
        "knowledge graph",
        "semantic map",
    ],
    "live_intelligence": [
        "live intel",
        "toolcalling",
        "weather",
        "safety",
        "pricing",
        "fresh",
    ],
    "agent_governance": [
        "governance",
        "policy",
        "routing",
        "assignment",
        "autonomy",
        "operator",
    ],
}

CLUSTER_TO_CONCEPT_ID: dict[str, str] = {
    "autoresearch": "concept:autoresearch",
    "feedback_learning": "concept:feedback",
    "graph_memory": "concept:graph",
    "live_intelligence": "concept:live",
    "agent_governance": "concept:governance",
}


DEFAULT_SEED_DOCS = [
    "Docs/INDEX.md",
    "Docs/TECHNICAL_SCAFFOLD_AND_AUTORESEARCH.md",
    "Docs/ROUTING_STRATEGY.md",
    "Docs/FEEDBACK_LOOPS_AND_IMPROVEMENT.md",
    "Docs/EXPLORATION_FRONTIER.md",
    "Docs/CROSS_PROJECT_AGENTIC_PATTERNS_2026-04-20.md",
    "Docs/AGENT_FEEDBACK_LOOP_SPEC_2026-04-22.md",
    "Docs/ARCHITECTURE_DECISION_D5_OVERRIDE_LEARNING_2026-04-18.md",
    "Docs/AI_WORKFORCE_REGISTRY_CONTRACT_2026-04-22.md",
    "Docs/product_features/SEMANTIC_TASTE_GRAPH_DISCOVERY.md",
    "Docs/research/AGENT_GRAPH_AND_GLOBAL_ADMIN_EXPLORATION_2026-05-04.md",
    "Docs/research/LIVE_INTEL_TOOLCALLING_EXPLORATION_2026-05-05.md",
    "Docs/research/FLW_SPEC_FEEDBACK_LEARNING.md",
]


@dataclass(slots=True)
class Node:
    id: str
    label: str
    kind: str
    path: str | None = None
    score: int = 0


@dataclass(slots=True)
class Edge:
    source: str
    target: str
    relation: str
    weight: int = 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="/Users/pranay/Projects/travel_agency_agent", help="Repository root")
    parser.add_argument(
        "--output-md",
        default="/Users/pranay/Projects/travel_agency_agent/Docs/context/AGENT_INTELLIGENCE_GRAPH.md",
        help="Markdown output path",
    )
    parser.add_argument(
        "--output-json",
        default="/Users/pranay/Projects/travel_agency_agent/Docs/context/agent_intelligence_graph.json",
        help="JSON output path",
    )
    parser.add_argument("--seed-doc", action="append", default=[], help="Additional seed doc relative to repo root")
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return fallback


def extract_links(text: str) -> list[str]:
    links: list[str] = []
    for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text):
        target = match.group(1).strip()
        if target.endswith(".md") or target.endswith(".json"):
            links.append(target)
    return links


def extract_keywords(text: str) -> list[str]:
    lowered = text.lower()
    hits: list[str] = []
    for cluster, terms in KEYWORD_CLUSTERS.items():
        if any(term in lowered for term in terms):
            hits.append(cluster)
    return hits


def normalize_doc_path(root: Path, raw: str) -> str | None:
    if raw.startswith(("http://", "https://", "file://")):
        return None
    candidate = (root / raw).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    if candidate.exists():
        return str(candidate.relative_to(root))
    return None


def unique_in_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def build_graph(root: Path, seed_docs: list[str]) -> tuple[list[Node], list[Edge], dict[str, list[str]]]:
    nodes: dict[str, Node] = {}
    edges: list[Edge] = []
    doc_clusters: dict[str, list[str]] = {}

    concept_nodes = {
        "concept:autoresearch": Node(id="concept:autoresearch", label="Autoresearch Loop", kind="concept"),
        "concept:feedback": Node(id="concept:feedback", label="Feedback / Learning Loop", kind="concept"),
        "concept:graph": Node(id="concept:graph", label="Graph / Lineage Memory", kind="concept"),
        "concept:live": Node(id="concept:live", label="Live Intelligence", kind="concept"),
        "concept:governance": Node(id="concept:governance", label="Governance / Routing", kind="concept"),
    }
    nodes.update(concept_nodes)

    for rel in unique_in_order(seed_docs):
        path = root / rel
        if not path.exists():
            continue
        text = read_text(path)
        label = first_heading(text, rel.rsplit("/", 1)[-1])
        node_id = f"doc:{rel}"
        nodes[node_id] = Node(id=node_id, label=label, kind="doc", path=rel)

        clusters = extract_keywords(text)
        doc_clusters[rel] = clusters
        for cluster in clusters:
            concept_id = CLUSTER_TO_CONCEPT_ID.get(cluster, f"concept:{cluster}")
            if concept_id not in nodes:
                nodes[concept_id] = Node(id=concept_id, label=cluster.replace("_", " ").title(), kind="concept")
            edges.append(Edge(source=node_id, target=concept_id, relation="supports"))

        for raw_link in extract_links(text):
            linked = normalize_doc_path(root, raw_link)
            if linked is None:
                continue
            linked_id = f"doc:{linked}"
            if linked_id not in nodes:
                linked_text = read_text(root / linked)
                nodes[linked_id] = Node(
                    id=linked_id,
                    label=first_heading(linked_text, linked.rsplit("/", 1)[-1]),
                    kind="doc",
                    path=linked,
                )
            edges.append(Edge(source=node_id, target=linked_id, relation="references"))

    # Add a few canonical cross-links to express the intended system architecture.
    if "doc:Docs/TECHNICAL_SCAFFOLD_AND_AUTORESEARCH.md" in nodes:
        edges.append(Edge("doc:Docs/TECHNICAL_SCAFFOLD_AND_AUTORESEARCH.md", "concept:autoresearch", "anchors"))
    if "doc:Docs/FEEDBACK_LOOPS_AND_IMPROVEMENT.md" in nodes:
        edges.append(Edge("doc:Docs/FEEDBACK_LOOPS_AND_IMPROVEMENT.md", "concept:feedback", "anchors"))
    if "doc:Docs/product_features/SEMANTIC_TASTE_GRAPH_DISCOVERY.md" in nodes:
        edges.append(Edge("doc:Docs/product_features/SEMANTIC_TASTE_GRAPH_DISCOVERY.md", "concept:graph", "anchors"))
    if "doc:Docs/research/LIVE_INTEL_TOOLCALLING_EXPLORATION_2026-05-05.md" in nodes:
        edges.append(Edge("doc:Docs/research/LIVE_INTEL_TOOLCALLING_EXPLORATION_2026-05-05.md", "concept:live", "anchors"))
    if "doc:Docs/AGENT_FEEDBACK_LOOP_SPEC_2026-04-22.md" in nodes:
        edges.append(Edge("doc:Docs/AGENT_FEEDBACK_LOOP_SPEC_2026-04-22.md", "concept:governance", "anchors"))

    ordered_nodes = sorted(nodes.values(), key=lambda n: (n.kind, n.label.lower(), n.id))
    deduped_edges = []
    seen_edges: set[tuple[str, str, str]] = set()
    for edge in edges:
        key = (edge.source, edge.target, edge.relation)
        if key in seen_edges:
            continue
        seen_edges.add(key)
        deduped_edges.append(edge)
    deduped_edges.sort(key=lambda e: (e.source, e.target, e.relation))
    return ordered_nodes, deduped_edges, doc_clusters


def render_markdown(nodes: list[Node], edges: list[Edge], clusters: dict[str, list[str]], root: Path) -> str:
    outgoing: dict[str, list[Edge]] = defaultdict(list)
    for edge in edges:
        outgoing[edge.source].append(edge)

    concept_names = {
        "concept:autoresearch": "Autoresearch Loop",
        "concept:feedback": "Feedback / Learning Loop",
        "concept:graph": "Graph / Lineage Memory",
        "concept:live": "Live Intelligence",
        "concept:governance": "Governance / Routing",
    }

    doc_nodes = [n for n in nodes if n.kind == "doc"]
    concept_nodes = [n for n in nodes if n.kind == "concept"]

    lines = [
        "# Agent Intelligence Graph",
        "",
        "This graph turns the repo's research, feedback, graph, and learning docs into a living navigation layer.",
        "",
        "## Core Concepts",
    ]
    for node in concept_nodes:
        lines.append(f"- `{node.id}` - {concept_names.get(node.id, node.label)}")

    lines.extend(["", "## Seed Docs"])
    for node in doc_nodes:
        rel = node.path or node.id.removeprefix("doc:")
        cluster_list = ", ".join(clusters.get(rel, [])) or "none"
        lines.append(f"- `{rel}` - {node.label} | themes: {cluster_list}")
        for edge in outgoing.get(node.id, []):
            lines.append(f"  - {edge.relation} -> `{edge.target}`")

    lines.extend(
        [
            "",
            "## Operating Model",
            "- Live path stays deterministic and bounded.",
            "- Autoresearch is offline only: mutate, evaluate, persist only if evidence improves.",
            "- Feedback loops convert overrides, outcomes, and recurring corrections into future policy.",
            "- Graph memory links docs, decisions, and learning signals so the next agent can start from a better map.",
            "",
            "## Suggested Reading Order",
            "1. `Docs/INDEX.md`",
            "2. `Docs/TECHNICAL_SCAFFOLD_AND_AUTORESEARCH.md`",
            "3. `Docs/FEEDBACK_LOOPS_AND_IMPROVEMENT.md`",
            "4. `Docs/product_features/SEMANTIC_TASTE_GRAPH_DISCOVERY.md`",
            "5. `Docs/research/LIVE_INTEL_TOOLCALLING_EXPLORATION_2026-05-05.md`",
            "6. `Docs/CROSS_PROJECT_AGENTIC_PATTERNS_2026-04-20.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()

    seed_docs = DEFAULT_SEED_DOCS + args.seed_doc
    nodes, edges, clusters = build_graph(root, seed_docs)
    graph = {
        "root": str(root),
        "nodes": [asdict(node) for node in nodes],
        "edges": [asdict(edge) for edge in edges],
        "cluster_map": clusters,
    }

    output_md = Path(args.output_md)
    output_json = Path(args.output_json)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(graph, indent=2, sort_keys=True), encoding="utf-8")
    output_md.write_text(render_markdown(nodes, edges, clusters, root), encoding="utf-8")


if __name__ == "__main__":
    main()
