"""LLM 调用封装（基于 DashScope 百炼 / Qwen，OpenAI 兼容接口）。

直接用 requests 调 DashScope 的 OpenAI 兼容接口，不依赖 langchain_openai，
避免环境依赖问题。
"""

import json

import requests

from app.core.config import settings


def get_llm_config() -> dict:
    """返回 LLM 配置信息。"""
    return {
        "base_url": settings.dashscope_base_url,
        "api_key": settings.dashscope_api_key,
        "model": settings.dashscope_model,
    }


def chat(prompt: str, temperature: float = 0.3, timeout: int = 30) -> str:
    """调用 DashScope（百炼）的 OpenAI 兼容接口，返回模型响应文本。

    Args:
        prompt: 用户输入 prompt
        temperature: 采样温度
        timeout: 超时秒数

    Returns:
        模型响应的文本内容

    Raises:
        RuntimeError: API Key 未配置或调用失败
    """
    if not settings.dashscope_api_key:
        raise RuntimeError("DASHSCOPE_API_KEY 未配置，请在 .env 文件中设置")

    url = f"{settings.dashscope_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.dashscope_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.dashscope_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    # OpenAI 兼容响应格式：choices[0].message.content
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError(f"LLM 返回无 choices：{data}")
    return choices[0].get("message", {}).get("content", "")


def generate_observations(profile_data: dict) -> list[str]:
    """基于数据集画像统计结果，用 LLM 生成 5-8 条观察。

    Args:
        profile_data: 5 个 Tool（scan/annotation/quality/image_analysis）的合并统计结果

    Returns:
        观察字符串列表（5-8 条）
    """
    # 把统计数据压缩给 LLM（去掉过长的字段，避免 token 超限）
    compact = _compact_profile(profile_data)

    prompt = f"""你是一个数据集分析专家。基于以下数据集统计结果，生成 5-8 条有数据支撑的观察（observations）。

数据集画像统计：
{json.dumps(compact, ensure_ascii=False, indent=2, default=str)}

要求：
1. 每条观察一句话，必须引用具体数字（如"共 287 张图像"，不能说"数据集较小"）
2. 关注：数据规模、类别分布、标注质量、图像质量、潜在问题
3. 用中文输出
4. 只输出 JSON 数组，格式：["观察1", "观察2", ...]
5. 不要输出任何其他内容
"""
    content = chat(prompt)
    content = content.strip()

    # 去掉可能的 markdown 代码块包裹
    if content.startswith("```"):
        content = content.split("\n", 1)[-1]
        if content.endswith("```"):
            content = content.rsplit("```", 1)[0]
        content = content.strip()

    # 解析 JSON
    try:
        observations = json.loads(content)
        if isinstance(observations, list):
            return [str(o) for o in observations][:8]
    except json.JSONDecodeError:
        # 兜底：按行分割
        lines = [
            line.strip().lstrip("0123456789.-) ").strip('"').strip("「」""")
            for line in content.split("\n")
            if line.strip()
        ]
        return lines[:8]

    return []


def _compact_profile(profile_data: dict) -> dict:
    """压缩 profile 数据，去掉过长的字段（如 sample_images、file_tree），避免 token 超限。"""
    compact = {}
    for key, value in profile_data.items():
        if key in ("scan", "annotation", "quality", "image_analysis"):
            sub = {}
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    # 跳过过长的列表和嵌套结构
                    if isinstance(sub_value, (list, dict)) and len(str(sub_value)) > 500:
                        continue
                    sub[sub_key] = sub_value
            compact[key] = sub
        else:
            compact[key] = value
    return compact
