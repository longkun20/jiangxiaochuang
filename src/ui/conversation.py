"""对话面板 — 纯聊天视图，干净简洁"""

from __future__ import annotations

import base64

import streamlit as st

from ..state import K


def render_welcome() -> None:
    """欢迎页，在没有任何消息时展示"""
    st.markdown("""
        <div class="welcome">
            <div class="icon">🏯</div>
            <h2>你好，我是江小创</h2>
            <p>武汉文创 AI 设计师。选好左边的文化元素和产品类型，<br/>或者直接告诉我你的想法，我来帮你设计。</p>
            <div class="hints">
                <span class="hint-chip">💬 做一个黄鹤楼主题冰箱贴</span>
                <span class="hint-chip">🌸 樱花帆布包，极简风</span>
                <span class="hint-chip">🍜 热干面T恤，要有江湖气</span>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_messages() -> None:
    """渲染对话消息流（含工具调用卡片和图片）"""
    messages: list[dict] = st.session_state.get(K.MESSAGES, [])

    if not messages:
        render_welcome()
        return

    for i, msg in enumerate(messages):
        role: str = msg["role"]

        with st.chat_message(role):
            # 工具调用卡片（如果是 assistant 且有 tool_calls）
            if msg.get("tool_calls"):
                _render_tool_call_strip(msg["tool_calls"])

            # 正文
            content: str = msg.get("content", "")
            if content:
                st.markdown(content)

            # 图片
            if msg.get("image"):
                st.image(
                    base64.b64decode(msg["image"]),
                    caption=msg.get("image_caption", ""),
                    use_container_width=True,
                )


def _render_tool_call_strip(tool_calls: list[dict]) -> None:
    """渲染工具调用小标签条"""
    icons = {
        "search_culture": "📚",
        "check_design_rules": "📐",
        "generate_image": "🎨",
    }
    labels = {
        "search_culture": "查文化资料",
        "check_design_rules": "查设计规范",
        "generate_image": "生成效果图",
    }

    chips = []
    for tc in tool_calls:
        name = tc.get("function", {}).get("name", "")
        icon = icons.get(name, "🔧")
        label = labels.get(name, name)
        chips.append(
            f"<span class='tool-call-card'>"
            f"<span class='icon'>{icon}</span>"
            f"<span class='label'>{label}</span>"
            f"</span>"
        )

    if chips:
        st.markdown(
            "<div style='display:flex;flex-wrap:wrap;gap:0.4rem;margin-bottom:0.4rem;'>"
            + "".join(chips)
            + "</div>",
            unsafe_allow_html=True,
        )


def show_running_indicator() -> None:
    """Agent 正在运行时的指示"""
    if st.session_state.get(K.RUNNING):
        with st.chat_message("assistant"):
            st.markdown("*正在思考…*")
