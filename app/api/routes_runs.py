from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class RunCreateRequest(BaseModel):
    query: str
    domain: str | None = None
    task_type: str | None = None
    dataset_path: str | None = None
    max_iterations: int = 3


@router.post("")
async def create_run(payload: RunCreateRequest) -> dict[str, str]:
    run_id = f"run_{uuid4().hex[:12]}"
    return {
        "run_id": run_id,
        "status": "created",
        "query": payload.query,
    }


@router.get("/{run_id}")
async def get_run(run_id: str) -> dict[str, str]:
    return {
        "run_id": run_id,
        "status": "mock",
        "current_node": "not_started",
    }
