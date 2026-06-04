"""江小创 · 武汉文创 AI 设计助手 — 对话式文创设计"""

from __future__ import annotations

import base64
import sys
import os

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agent import run_agent
from src.config import Config
from src.prompts import SYSTEM_PROMPT, build_first_message
from src.tools import generate_design_image
from src.storage import save_conversation
from src.state import (
    K,
    TOOL_PHASE_MAP,
    current_elements,
    current_style,
    current_product,
    ensure_session_state,
    append_tool_log,
    update_latest_result,
)
from src.ui.styles import STYLES
from src.ui.conversation import render_messages
from src.ui.sidebar import render_sidebar
from src.ui.solution import render_solution_card

# ═════════════════════════════════════════════════════════════
# Page Config
# ═════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="江小创 · 武汉文创 AI 设计师",
    page_icon="🏯",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(STYLES, unsafe_allow_html=True)

ensure_session_state()


# ═════════════════════════════════════════════════════════════
# Helpers
# ═════════════════════════════════════════════════════════════

def _auto_save() -> None:
    """自动保存当前对话"""
    conv_id = st.session_state.get(K.CONVERSATION_ID, "")
    messages = st.session_state.get(K.MESSAGES, [])
    if conv_id and messages:
        save_conversation(conv_id, messages)


def get_api_key() -> str:
    return st.session_state.get(K.API_DASHSCOPE_KEY, "") or Config.LLM_API_KEY


def get_api_model() -> str:
    return st.session_state.get("api_llm_model", "") or Config.LLM_MODEL


def get_dashscope_key() -> str:
    # 百炼 Key 文本和图片共用
    return st.session_state.get(K.API_DASHSCOPE_KEY, "") or Config.DASHSCOPE_API_KEY


# ═════════════════════════════════════════════════════════════
# Agent Runner
# ═════════════════════════════════════════════════════════════

def run_agent_turn() -> None:
    """执行 Agent 主循环，将事件渲染到聊天区"""
    if not st.session_state.get(K.RUNNING):
        return

    st.session_state[K.RUNNING] = False

    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in st.session_state[K.MESSAGES]:
        full_messages.append({"role": m["role"], "content": m["content"]})

    # Sync dashscope key
    dk = get_dashscope_key()
    if dk and dk != Config.DASHSCOPE_API_KEY:
        Config.DASHSCOPE_API_KEY = dk

    full_text = ""
    generated_image: str | None = None
    generated_caption = ""

    # 占位：流式文本容器
    text_placeholder = st.empty()
    # 工具调用收集
    tool_calls_in_turn: list[dict] = []

    try:
        for event in run_agent(
            full_messages, api_key=get_api_key(), model=get_api_model(), max_rounds=8,
        ):
            etype = event["type"]

            if etype == "text":
                full_text += event["content"]
                # 实时渲染流式文本
                with text_placeholder.container():
                    with st.chat_message("assistant"):
                        if tool_calls_in_turn:
                            _render_tool_pills(tool_calls_in_turn)
                        st.markdown(full_text + "▌")

            elif etype == "tool_call":
                name = event["name"]
                args = event.get("args", {})
                tool_calls_in_turn.append({"name": name, "args": args})
                # 更新流式容器中的工具标签
                with text_placeholder.container():
                    with st.chat_message("assistant"):
                        if tool_calls_in_turn:
                            _render_tool_pills(tool_calls_in_turn)
                        if full_text:
                            st.markdown(full_text + "▌")
                        else:
                            st.caption("Agent 正在调用工具…")
                if name == "generate_image":
                    append_tool_log("🎨 开始出图", "正在生成产品效果图…")
                elif name == "search_culture":
                    append_tool_log("📚 文化检索", f"搜索「{args.get('element_name', '')}」")
                elif name == "check_design_rules":
                    append_tool_log("📐 规范校验", f"查询「{args.get('product', '')}」设计规则")

            elif etype == "tool_result":
                append_tool_log(
                    f"{'✅' if event['success'] else '❌'} {event['name']}",
                    event["summary"][:200],
                )

            elif etype == "image":
                generated_image = event["base64"]
                generated_caption = event.get("caption", "AI 生成")
                append_tool_log("🖼️ 出图完成", "效果图已生成")

            elif etype == "error":
                append_tool_log("❌ 出错", event["message"])

    except Exception as exc:
        append_tool_log("❌ 异常", str(exc))

    # 清除流式占位
    text_placeholder.empty()

    # 保存到 messages
    assistant_msg: dict = {
        "role": "assistant",
        "content": full_text,
    }
    if tool_calls_in_turn:
        assistant_msg["tool_calls"] = tool_calls_in_turn
    if generated_image:
        assistant_msg["image"] = generated_image
        assistant_msg["image_caption"] = generated_caption
    st.session_state[K.MESSAGES].append(assistant_msg)

    # 更新最新结果（供方案卡片使用）
    if generated_image:
        update_latest_result(full_text, generated_image, generated_caption)
    elif full_text.strip():
        update_latest_result(full_text)

    _auto_save()
    st.rerun()


def _render_tool_pills(tool_calls: list[dict]) -> None:
    """渲染工具调用标签条"""
    icons = {"search_culture": "📚", "check_design_rules": "📐", "generate_image": "🎨"}
    labels = {"search_culture": "查资料", "check_design_rules": "查规范", "generate_image": "出图"}
    chips = []
    for tc in tool_calls:
        name = tc.get("name", "")
        icon = icons.get(name, "🔧")
        label = labels.get(name, name)
        chips.append(
            f"<span class='tool-call-card'>"
            f"<span class='icon'>{icon}</span> <span class='label'>{label}</span>"
            f"</span>"
        )
    if chips:
        st.markdown(
            "<div style='display:flex;flex-wrap:wrap;gap:0.4rem;margin-bottom:0.4rem;'>"
            + "".join(chips) + "</div>",
            unsafe_allow_html=True,
        )


def run_manual_image_gen() -> None:
    """手动出图"""
    req = st.session_state.get(K.MANUAL_IMAGE_REQUEST)
    if not req:
        return

    st.session_state[K.MANUAL_IMAGE_REQUEST] = None
    prompt = req.get("prompt", "").strip()
    style = req.get("style", "").strip()
    product = req.get("product", "").strip()
    dk = get_dashscope_key()

    if not prompt:
        st.toast("视觉描述为空", icon="⚠️")
        st.rerun()
        return
    if not dk or dk.startswith("sk-your"):
        st.toast("未配置图片生成 API Key", icon="🔐")
        st.rerun()
        return

    with st.spinner("正在生成效果图…"):
        result = generate_design_image(prompt, style, product, dk)

    if result.success and "base64" in result.metadata:
        caption = f"{product} · {style}风格"
        st.session_state[K.LATEST_IMAGE] = {
            "base64": result.metadata["base64"],
            "caption": caption,
        }
        if st.session_state[K.MESSAGES] and st.session_state[K.MESSAGES][-1]["role"] == "assistant":
            st.session_state[K.MESSAGES][-1]["image"] = result.metadata["base64"]
            st.session_state[K.MESSAGES][-1]["image_caption"] = caption
        st.toast("效果图已生成！", icon="✅")
    else:
        st.toast(f"出图失败：{result.content[:100]}", icon="❌")

    st.rerun()


def handle_quick_start() -> None:
    """侧边栏「开始设计」按钮的处理"""
    if not st.session_state.get(K.QUICK_START_TRIGGER):
        return

    st.session_state[K.QUICK_START_TRIGGER] = False
    elements = current_elements()
    if not elements:
        return

    requirement = st.session_state.get(K.DESIGN_REQUIREMENT, "")
    user_msg = build_first_message(elements, current_style(), current_product(), requirement)
    st.session_state[K.MESSAGES].append({"role": "user", "content": user_msg})
    st.session_state[K.RUNNING] = True
    st.session_state[K.TOOL_LOG] = []
    st.session_state[K.LATEST_RESULT] = None
    st.session_state[K.LATEST_IMAGE] = None
    st.session_state[K.LAST_ERROR] = ""
    _auto_save()
    st.rerun()


# ═════════════════════════════════════════════════════════════
# Main Layout — 双栏：左面板 + 聊天区
# ═════════════════════════════════════════════════════════════

left_col, right_col = st.columns([1, 2.5], gap="medium")

# 左右两栏各自包在固定高度容器里 → 独立滚动 + 自带边框分隔
# 高度按笔记本屏幕调的，想更高/更矮改这两个数字即可
_PANEL_HEIGHT = 760   # 左侧配置面板
_CHAT_HEIGHT = 680    # 右侧对话流（留出底部输入框的空间）

with left_col:
    with st.container(height=_PANEL_HEIGHT):
        render_sidebar()

with right_col:
    handle_quick_start()
    # 对话历史 + 流式输出都放进滚动容器，长对话只在这里滚
    with st.container(height=_CHAT_HEIGHT):
        render_messages()
        if st.session_state.get(K.LATEST_RESULT):
            render_solution_card()
        run_agent_turn()
        run_manual_image_gen()

    # 输入框留在容器外 → 固定在右栏底部，不随对话滚走
    if prompt := st.chat_input("告诉江小创你想设计什么…"):
        st.session_state[K.MESSAGES].append({"role": "user", "content": prompt})
        st.session_state[K.RUNNING] = True
        st.session_state[K.LATEST_RESULT] = None
        _auto_save()
        st.rerun()
