import asyncio
import json
from typing import Literal

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.llm import chat_messages
from app.db.redis import redis_client

router = APIRouter(tags=["chat"])


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    messages: list[ConversationMessage] = Field(min_length=1, max_length=20)
    run_id: str | None = Field(default=None, max_length=80)


def _compact_run_context(run_data: dict) -> dict:
    result = run_data.get("result") or {}
    return {
        "run_id": run_data.get("run_id"),
        "status": run_data.get("status"),
        "current_node": run_data.get("current_node"),
        "progress": run_data.get("progress"),
        "query": run_data.get("query"),
        "task_type": run_data.get("task_type"),
        "dataset_path": run_data.get("dataset_path"),
        "dataset_profile": {
            "dataset_name": result.get("dataset_name"),
            "image_count": result.get("image_count"),
            "splits": result.get("splits"),
            "image_extensions": result.get("image_extensions"),
            "annotation_format": result.get("annotation_format"),
            "annotation_file_count": result.get("annotation_file_count"),
            "valid_annotation_count": result.get("valid_annotation_count"),
            "class_distribution": result.get("class_distribution"),
            "bbox_statistics": result.get("bbox_statistics"),
            "small_object_ratio": result.get("small_object_ratio"),
            "distribution_difference": result.get("distribution_difference"),
            "observations": (result.get("observations") or [])[:8],
        },
    }


async def _load_run_context(run_id: str | None) -> dict | None:
    if not run_id:
        return None
    data = await redis_client.get(f"run:{run_id}")
    if not data:
        return None
    try:
        return _compact_run_context(json.loads(data))
    except (TypeError, json.JSONDecodeError):
        return None


@router.post("")
async def create_chat_response(payload: ChatRequest) -> dict[str, str | bool]:
    context = await _load_run_context(payload.run_id)
    system_prompt = (
        "你是 CV AI Scientist 项目中的研究助手。请使用中文回答，保持准确、简洁、可执行。"
        "用户询问当前任务时，只能依据提供的任务上下文，不得编造不存在的统计数据。"
        "如果上下文不足，请明确指出缺少什么信息。"
        "你可以解释数据集画像、质量指标、标注问题、实验设计和研究报告。"
    )
    model_messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    if context:
        context_text = json.dumps(context, ensure_ascii=False, default=str)
        model_messages.append(
            {
                "role": "system",
                "content": f"当前任务上下文如下：\n{context_text[:12000]}",
            }
        )
    model_messages.extend(
        {"role": message.role, "content": message.content.strip()}
        for message in payload.messages[-12:]
    )

    try:
        answer = await asyncio.to_thread(chat_messages, model_messages)
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="大模型服务暂时不可用，请稍后重试") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if not answer.strip():
        raise HTTPException(status_code=502, detail="大模型未返回有效内容")

    return {
        "answer": answer.strip(),
        "model": settings.dashscope_model,
        "has_run_context": bool(context),
    }
