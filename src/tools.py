"""工具系统 — Agent 可调用的外部工具（从 JSON 加载数据）"""

from __future__ import annotations

import base64
import json
import logging
import time
from pathlib import Path
from typing import Any

import requests
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# 数据文件路径
_DATA_DIR = Path(__file__).resolve().parent / "data"


@dataclass
class ToolResult:
    """工具调用结果"""
    success: bool
    content: str
    metadata: dict = field(default_factory=dict)


# ── 文化知识库加载 ──────────────────────────────────────

def _load_culture_db() -> dict[str, dict]:
    """从 JSON 文件加载文化知识库"""
    path = _DATA_DIR / "wuhan_culture.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"加载文化知识库失败: {e}")
        return {}


def _load_design_rules() -> dict[str, dict]:
    """从 JSON 文件加载设计规范"""
    path = _DATA_DIR / "design_rules.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"加载设计规范失败: {e}")
        return {}


# 模块级加载（首次 import 时读取，后续复用）
WUHAN_CULTURE_DB: dict[str, dict] = _load_culture_db()
DESIGN_RULES: dict[str, dict] = _load_design_rules()


def search_culture(element_name: str) -> ToolResult:
    """从文化知识库中检索武汉文化元素信息

    Args:
        element_name: 文化元素名称，如 黄鹤楼、热干面

    Returns:
        ToolResult with success flag and JSON content
    """
    if not element_name:
        return ToolResult(success=False, content="请提供要搜索的文化元素名称")

    if element_name in WUHAN_CULTURE_DB:
        return ToolResult(
            success=True,
            content=json.dumps(WUHAN_CULTURE_DB[element_name], ensure_ascii=False, indent=2),
            metadata={"source": "本地文化知识库", "match_type": "exact"},
        )

    # 模糊匹配
    for key, info in WUHAN_CULTURE_DB.items():
        if element_name in key or key in element_name:
            return ToolResult(
                success=True,
                content=json.dumps(info, ensure_ascii=False, indent=2),
                metadata={"source": "本地文化知识库", "match_type": "fuzzy"},
            )

    return ToolResult(
        success=False,
        content=f"未找到「{element_name}」的文化资料，请尝试使用 LLM 自有知识",
    )


def check_design_rules(product: str) -> ToolResult:
    """查询产品设计规范

    Args:
        product: 产品类型，如 T恤、帆布包

    Returns:
        ToolResult with design rules
    """
    if product in DESIGN_RULES:
        rules = DESIGN_RULES[product]
        return ToolResult(
            success=True,
            content=json.dumps(rules, ensure_ascii=False, indent=2),
            metadata={"product": product},
        )
    return ToolResult(
        success=True,
        content=json.dumps(
            {"注意": "请根据产品实际形态灵活设计构图和比例"}, ensure_ascii=False
        ),
    )


# ── 图片生成 ──────────────────────────────────────────


def _build_image_prompt(prompt: str, style: str, product: str) -> str:
    """构建专业的图片生成 Prompt"""
    product_nouns = {
        "T恤": "一件T恤（平铺展示，正面朝上）",
        "冰箱贴": "一个冰箱贴（微距特写，金属/亚克力质感）",
        "帆布包": "一个帆布托特包（正面展示）",
        "手机壳": "一个手机壳（背面朝上，展示图案面）",
        "马克杯": "一个马克杯（正面展示，圆柱曲面展开）",
        "明信片": "一张明信片（平面展示，印刷质感）",
    }
    product_desc = product_nouns.get(product, f"一个{product}产品（商业产品摄影风格）")

    return f"""商业产品设计效果图：{product_desc}。
设计风格：{style}。
设计要求与视觉描述：{prompt}

画面要求：
- 产品主体占据画面主要位置，清晰展示设计图案
- 光线明亮均匀，产品材质和印刷细节清晰可见
- 背景为纯色或极简布景，不抢夺产品视觉焦点
- 构图专业，适合电商主图或产品画册使用"""


def generate_design_image(
    prompt: str,
    style: str,
    product: str,
    api_key: str,
    progress_callback: callable | None = None,
) -> ToolResult:
    """调用通义万相生成产品设计图

    Args:
        prompt: 视觉描述文本（完整，不再截断）
        style: 设计风格
        product: 产品类型
        api_key: 百炼 API Key
        progress_callback: 可选进度回调，签名为 callback(phase: str, detail: str)

    Returns:
        ToolResult with base64 image in metadata
    """
    if not api_key or api_key.startswith("sk-your"):
        return ToolResult(success=False, content="未配置有效的通义万相 API Key")

    try:
        full_prompt = _build_image_prompt(prompt, style, product)

        if progress_callback:
            progress_callback("submitting", "正在提交图片生成任务...")

        submit_response = requests.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/image-generation/generation",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable",
            },
            json={
                "model": "wan2.7-image-pro",
                "input": {
                    "messages": [{"role": "user", "content": [{"text": full_prompt}]}]
                },
                "parameters": {"size": "1024*1024", "n": 1},
            },
            timeout=30,
        )

        submit_result = submit_response.json()

        # 检查 API 返回错误
        if "code" in submit_result and submit_result.get("code") != "":
            code = submit_result.get("code", "")
            message = submit_result.get("message", "未知错误")
            return ToolResult(success=False, content=f"API 错误 [{code}]：{message}")

        task_id = submit_result.get("output", {}).get("task_id", "")

        if not task_id:
            error_msg = submit_result.get("message", str(submit_result))
            logger.error(f"图片生成任务提交失败: {error_msg}")
            return ToolResult(success=False, content=f"提交任务失败：{error_msg}（请检查 API Key 是否有效且有余额）")

        if progress_callback:
            progress_callback("polling", f"任务已提交 (ID: {task_id[:12]}...)，等待生成...")

        # 轮询等待结果（最多 60 秒）
        poll_interval = 2  # 秒
        max_attempts = 30

        for attempt in range(1, max_attempts + 1):
            time.sleep(poll_interval)

            if progress_callback:
                progress_callback(
                    "polling",
                    f"等待渲染完成... ({attempt}/{max_attempts})",
                )

            try:
                poll_response = requests.get(
                    f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10,
                )
                poll_result = poll_response.json()
            except Exception:
                continue  # 网络抖动，继续轮询

            status = poll_result.get("output", {}).get("task_status", "")

            if status == "SUCCEEDED":
                choices = poll_result.get("output", {}).get("choices", [])
                for choice in choices:
                    for item in choice.get("message", {}).get("content", []):
                        image_url = item.get("image", "")
                        if image_url:
                            if progress_callback:
                                progress_callback("downloading", "正在下载生成图片...")
                            img_data = requests.get(image_url, timeout=30).content
                            b64 = base64.b64encode(img_data).decode()
                            return ToolResult(
                                success=True,
                                content="图片生成成功",
                                metadata={"base64": b64, "image_url": image_url},
                            )
                return ToolResult(success=False, content="图片生成成功但未获取到 URL")

            elif status == "FAILED":
                err = poll_result.get("output", {}).get("message", "未知错误")
                return ToolResult(success=False, content=f"图片生成失败：{err}")

        return ToolResult(success=False, content="图片生成超时（60秒），请重试")

    except Exception as e:
        return ToolResult(success=False, content=f"图片生成异常：{e}")


# ── 工具注册表 ────────────────────────────────────────

TOOL_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_culture",
            "description": (
                "搜索武汉文化元素的背景资料，包括历史渊源、视觉符号、配色方案和关键词。"
                "在生成设计前必须先调研文化元素。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "element_name": {
                        "type": "string",
                        "description": "要搜索的文化元素名称，如 黄鹤楼、热干面、樱花 等",
                    }
                },
                "required": ["element_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_design_rules",
            "description": (
                "查询指定产品类型的设计规范，包括尺寸、构图建议和注意事项。"
                "在设计前必须了解产品约束。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product": {
                        "type": "string",
                        "description": "产品类型，如 T恤、冰箱贴、帆布包、手机壳、马克杯、明信片",
                    }
                },
                "required": ["product"],
            },
        },
    },
]


def execute_tool(name: str, arguments: dict[str, Any]) -> ToolResult:
    """执行工具调用（Agent 引擎调用入口）

    Args:
        name: 工具名 (search_culture / check_design_rules)
        arguments: 参数 dict

    Returns:
        ToolResult
    """
    if name == "search_culture":
        return search_culture(arguments.get("element_name", ""))
    elif name == "check_design_rules":
        return check_design_rules(arguments.get("product", ""))
    else:
        return ToolResult(success=False, content=f"未知工具：{name}")
