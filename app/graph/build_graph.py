from langgraph.graph import END, START, StateGraph

from app.agents.graph_agent import build_literature_graph_node
from app.graph.state import ScientistState


async def parse_problem_node(state: ScientistState) -> dict:
    return {
        "domain": state.get("domain") or "computer_vision",
        "task_type": state.get("task_type") or "unknown",
        "route": "build_literature_graph",
    }


async def write_report_node(state: ScientistState) -> dict:
    return {
        "final_report": {
            "title": "Mock CV AI Scientist Report",
            "query": state.get("user_query", ""),
            "literature_graph": state.get("literature_graph", {}),
        },
        "route": "end",
    }


def build_graph():
    graph = StateGraph(ScientistState)
    graph.add_node("parse_problem", parse_problem_node)
    graph.add_node("build_literature_graph", build_literature_graph_node)
    graph.add_node("write_report", write_report_node)

    graph.add_edge(START, "parse_problem")
    graph.add_edge("parse_problem", "build_literature_graph")
    graph.add_edge("build_literature_graph", "write_report")
    graph.add_edge("write_report", END)
    return graph.compile()
