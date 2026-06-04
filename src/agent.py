"""Agent 引擎 — 流式输出 + 工具调用"""

from __future__ import annotations

import json
import logging
from typing import Generator

from openai import OpenAI

from .config import Config
from .tools import execute_tool, TOOL_DEFINITIONS, generate_design_image

logger = logging.getLogger(__name__)

# 图片生成工具定义
_IMAGE_TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "generate_image",
        "description": (
            "根据视觉描述生成产品设计效果图。"
            "必须在用户明确同意出图后调用。"
            "visual_description 参数必须是你之前输出的「视觉描述」章节的完整原文，不得缩写。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "visual_description": {
                    "type": "string",
                    "description": (
                        "「视觉描述」章节的完整原文。必须包含：画面构图（主体位置、大小比例、"
                        "前后层次）、配色方案（主色辅色点缀色的具体色号或描述）、元素排列方式"
                        "（重叠/穿插/对称/散点）、纹理材质建议、留白比例和整体氛围。"
                        "字数不少于 150 字，越详细图片越精准。"
                    ),
                },
                "style": {
                    "type": "string",
                    "description": "设计风格名称，如 国潮、极简、赛博朋克、水墨风 等",
                },
                "product": {
                    "type": "string",
                    "description": "产品类型，如 T恤、冰箱贴、帆布包、手机壳、马克杯、明信片",
                },
            },
            "required": ["visual_description", "style", "product"],
        },
    },
}

ALL_TOOLS: list[dict] = TOOL_DEFINITIONS + [_IMAGE_TOOL_DEF]


def run_agent(
    messages: list[dict],
    api_key: str = "",
    model: str = "",
    max_rounds: int = 8,
) -> Generator[dict, None, None]:
    """
    Agent 主循环，流式执行 ReAct 架构。

    yield 事件类型:
        {"type": "text", "content": "..."}              — 流式文本片段
        {"type": "tool_call", "name": "...", "args": {}} — 开始调用工具
        {"type": "tool_result", "name": "...", "success": True, "summary": "..."}
        {"type": "image", "base64": "...", "caption": "..."}  — 生成的图片
        {"type": "done"}                                  — 本轮结束
        {"type": "error", "message": "..."}              — 出错
    """
    client = OpenAI(
        api_key=api_key or Config.LLM_API_KEY,
        base_url=Config.LLM_BASE_URL,
    )
    model = model or Config.LLM_MODEL

    # 备份 messages，出错时回滚避免丢失
    messages_snapshot = [m.copy() for m in messages]

    for round_idx in range(max_rounds):
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=Config.TEMPERATURE,
                max_tokens=Config.MAX_TOKENS,
                tools=ALL_TOOLS,
                tool_choice="auto",
                stream=True,
                stream_options={"include_usage": True},
            )
        except Exception as exc:
            logger.error(f"LLM 调用失败 (round {round_idx + 1}): {exc}")
            # 回滚到快照，保留之前生成的文本
            messages[:] = messages_snapshot
            yield {"type": "error", "message": f"LLM 调用失败：{exc}"}
            yield {"type": "done"}
            return

        # 收集流式响应
        full_text = ""
        tool_calls: dict[int, dict] = {}

        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta is None:
                continue

            # 文本片段 → 实时 yield
            if delta.content:
                full_text += delta.content
                yield {"type": "text", "content": delta.content}

            # 工具调用片段（分片到达）
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls:
                        tool_calls[idx] = {"id": "", "name": "", "arguments": ""}
                    if tc.id:
                        tool_calls[idx]["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            tool_calls[idx]["name"] += tc.function.name
                        if tc.function.arguments:
                            tool_calls[idx]["arguments"] += tc.function.arguments

        # 如果没有工具调用，本轮结束
        if not tool_calls:
            if full_text:
                messages.append({"role": "assistant", "content": full_text})
            yield {"type": "done"}
            return

        # 构建 assistant message（含 tool_calls）
        tc_list = []
        for idx in sorted(tool_calls.keys()):
            tc = tool_calls[idx]
            tc_list.append({
                "id": tc["id"],
                "type": "function",
                "function": {"name": tc["name"], "arguments": tc["arguments"]},
            })

        assistant_msg: dict = {"role": "assistant", "content": full_text or None}
        if tc_list:
            assistant_msg["tool_calls"] = tc_list
        messages.append(assistant_msg)

        # 执行每个工具
        for idx in sorted(tool_calls.keys()):
            tc = tool_calls[idx]
            name = tc["name"]
            try:
                args = json.loads(tc["arguments"])
            except json.JSONDecodeError:
                args = {}

            yield {"type": "tool_call", "name": name, "args": args}

            if name == "generate_image":
                dashscope_key = Config.DASHSCOPE_API_KEY
                visual = args.get("visual_description", "")
                style = args.get("style", "")
                product = args.get("product", "")

                result = generate_design_image(visual, style, product, dashscope_key)

                if result.success and "base64" in result.metadata:
                    yield {
                        "type": "tool_result",
                        "name": name,
                        "success": True,
                        "summary": "图片生成成功",
                    }
                    yield {
                        "type": "image",
                        "base64": result.metadata["base64"],
                        "caption": f"{product} · {style}风格",
                    }
                    tool_content = "图片已成功生成并展示给用户。"
                else:
                    yield {
                        "type": "tool_result",
                        "name": name,
                        "success": False,
                        "summary": result.content,
                    }
                    tool_content = f"图片生成失败：{result.content}"
            else:
                result = execute_tool(name, args)
                yield {
                    "type": "tool_result",
                    "name": name,
                    "success": result.success,
                    "summary": result.content[:300],
                }
                tool_content = result.content

            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": tool_content,
            })

        # 继续下一轮轮
        continue

    yield {"type": "error", "message": f"达到最大轮次限制（{max_rounds}轮）"}
