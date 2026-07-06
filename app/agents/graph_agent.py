from collections import defaultdict
from typing import Any

from app.graph.state import ScientistState


def _paper_id(paper: dict[str, Any], index: int) -> str:
    return str(paper.get("paper_id") or paper.get("id") or f"paper_{index:03d}")


async def build_literature_graph_node(state: ScientistState) -> dict[str, Any]:
    """Build a lightweight paper relationship graph from Paper Pool metadata."""
    papers = state.get("paper_pool", [])
    nodes = []
    edges = []
    inverted: dict[tuple[str, str], list[str]] = defaultdict(list)

    for index, paper in enumerate(papers, start=1):
        paper_id = _paper_id(paper, index)
        nodes.append(
            {
                "id": paper_id,
                "title": paper.get("title", ""),
                "year": paper.get("year"),
                "venue": paper.get("venue") or paper.get("source"),
            }
        )
        for relation_type in ("datasets", "tasks", "keywords", "citations"):
            for value in paper.get(relation_type, []) or []:
                inverted[(relation_type, str(value).lower())].append(paper_id)

    edge_index = 0
    seen = set()
    for (relation_type, value), paper_ids in inverted.items():
        if len(paper_ids) < 2:
            continue
        for source in paper_ids:
            for target in paper_ids:
                if source >= target:
                    continue
                key = (source, target, relation_type, value)
                if key in seen:
                    continue
                seen.add(key)
                edge_index += 1
                edges.append(
                    {
                        "id": f"edge_{edge_index:04d}",
                        "source": source,
                        "target": target,
                        "relation_type": relation_type,
                        "evidence": value,
                        "weight": 1.0,
                    }
                )

    return {
        "literature_graph": {
            "nodes": nodes,
            "edges": edges,
            "summary": {
                "num_papers": len(nodes),
                "num_relations": len(edges),
            },
        },
        "route": "write_report",
    }
