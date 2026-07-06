from typing import Any, Literal, TypedDict


class ScientistState(TypedDict, total=False):
    run_id: str
    user_query: str
    domain: str
    task_type: str
    constraints: list[str]

    paper_pool: list[dict[str, Any]]
    fact_pool: list[dict[str, Any]]
    literature_graph: dict[str, Any]
    dataset_profile: dict[str, Any]
    evidence_board: dict[str, Any]

    gap_pool: list[dict[str, Any]]
    hypothesis_pool: list[dict[str, Any]]
    review_pool: list[dict[str, Any]]
    selected_hypothesis: dict[str, Any]

    experiment_plan: dict[str, Any]
    tool_outputs: dict[str, Any]
    final_report: dict[str, Any]

    iteration: int
    max_iteration: int
    route: Literal[
        "parse_problem",
        "retrieve_literature",
        "build_literature_graph",
        "profile_dataset",
        "integrate_evidence",
        "find_gaps",
        "generate_hypotheses",
        "review_hypotheses",
        "design_experiment",
        "run_tools",
        "write_report",
        "human_review",
        "end",
    ]
