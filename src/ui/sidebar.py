"""侧边栏 — 配置面板 + 历史对话"""

from __future__ import annotations

import streamlit as st

from ..state import (
    K,
    ELEMENT_OPTIONS,
    STYLE_OPTIONS,
    PRODUCT_OPTIONS,
    current_elements,
    reset_session,
)
from ..storage import (
    list_conversations,
    load_conversation,
    delete_conversation,
)


def render_sidebar() -> None:
    """渲染 Streamlit 原生侧边栏"""
    # ── 品牌 ──
    st.markdown("""
        <div style="display:flex;align-items:center;gap:0.5rem;padding:0.3rem 0 0.6rem 0;">
            <div style="font-size:1.4rem;">🏯</div>
            <div>
                <div style="font-size:0.95rem;font-weight:700;color:#1a1a2e;">江小创</div>
                <div style="font-size:0.65rem;color:#999;">武汉文创 AI 设计师</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ── 新对话 ──
    if st.button("🆕 新对话", use_container_width=True):
        _save_current()
        reset_session()
        st.rerun()

    st.divider()

    # ── 历史对话 ──
    _render_conversation_list()

    st.divider()

    # ── 设计配置 ──
    with st.expander("⚙️ 设计配置", expanded=not bool(st.session_state.get(K.MESSAGES))):
        st.caption("文化元素")
        st.multiselect(
            "选择文化元素",
            options=[label for label, _ in ELEMENT_OPTIONS],
            key=K.SELECTED_ELEMENTS,
            placeholder="选 1-3 个元素",
            label_visibility="collapsed",
        )
        st.text_input(
            "自定义元素",
            key=K.CUSTOM_ELEMENT,
            placeholder="例如汉绣、里份、江滩…",
            label_visibility="collapsed",
        )

        st.caption("设计风格")
        st.selectbox(
            "设计风格", STYLE_OPTIONS,
            key=K.STYLE_CHOICE, label_visibility="collapsed",
        )
        if st.session_state.get(K.STYLE_CHOICE) == "🎨 自定义…":
            st.text_input(
                "自定义风格", key=K.CUSTOM_STYLE,
                placeholder="例如蒸汽波、未来民艺…",
                label_visibility="collapsed",
            )

        st.caption("产品类型")
        st.selectbox(
            "产品类型", PRODUCT_OPTIONS,
            key=K.PRODUCT_CHOICE, label_visibility="collapsed",
        )
        if st.session_state.get(K.PRODUCT_CHOICE) == "🛍️ 自定义…":
            st.text_input(
                "自定义产品", key=K.CUSTOM_PRODUCT,
                placeholder="例如徽章、滑板…",
                label_visibility="collapsed",
            )

    # ── 设计要求 ──
    st.text_area(
        "补充要求（可选）",
        key=K.DESIGN_REQUIREMENT,
        placeholder="例如：配色要暖色系、字体要大…",
        label_visibility="collapsed",
        height=68,
    )

    # ── 启动按钮 ──
    has_input = bool(current_elements())

    def _start():
        st.session_state[K.QUICK_START_TRIGGER] = True

    st.button(
        "🚀 开始设计",
        use_container_width=True,
        disabled=not has_input,
        on_click=_start,
    )

    # ── API 配置 ──
    st.divider()
    _render_api_config()


_LLM_MODELS = ["qwen-plus", "qwen-max", "qwen-turbo", "qwen-plus-latest", "qwen-max-latest"]


def _render_api_config() -> None:
    """侧边栏内联 API 配置（百炼 Key + 模型）"""
    has_key = _check_key(K.API_DASHSCOPE_KEY)

    # 没配 Key 时默认展开，引导用户填写
    with st.expander("🔐 API 配置", expanded=not has_key):
        st.text_input(
            "百炼 API Key",
            key=K.API_DASHSCOPE_KEY,
            type="password",
            placeholder="sk-...",
            help="通义千问（文本）+ 通义万相（出图）共用。获取：bailian.console.aliyun.com",
        )
        st.selectbox(
            "文本模型",
            _LLM_MODELS,
            key="api_llm_model",
            help="qwen-plus 性价比 | qwen-max 最强 | qwen-turbo 最快",
        )
        st.caption("图片固定用 通义万相 wan2.7-image-pro")

        # 状态指示
        c1, c2 = st.columns(2)
        with c1:
            st.caption(f"{'🟢' if has_key else '⚪'} 千问文本")
        with c2:
            st.caption(f"{'🟢' if has_key else '⚪'} 万相出图")
        if not has_key:
            st.caption("⚠️ 未配置有效 Key，无法对话/出图")


def _render_conversation_list() -> None:
    current_id = st.session_state.get(K.CONVERSATION_ID, "")
    conversations = list_conversations()
    current_messages = st.session_state.get(K.MESSAGES, [])
    current_title = _get_current_title(current_messages)

    with st.container():
        st.caption(f"📌 {current_title}")
        st.caption(f"共 {len(current_messages)} 条消息")

    if not conversations:
        return

    st.markdown("**历史对话**")

    for conv in conversations:
        sid = conv["id"]
        is_active = sid == current_id

        col1, col2 = st.columns([5, 1])
        with col1:
            prefix = "🔹" if is_active else "💬"
            title = conv["title"][:20] + ("…" if len(conv["title"]) > 20 else "")
            if st.button(
                f"{prefix} {title}",
                key=f"load_{sid}",
                use_container_width=True,
                disabled=is_active,
                help=f"{conv['message_count']} 条 · {conv['updated_at']}",
            ):
                _save_current()
                data = load_conversation(sid)
                if data:
                    st.session_state[K.CONVERSATION_ID] = sid
                    st.session_state[K.MESSAGES] = data.get("messages", [])
                    st.session_state[K.TOOL_LOG] = []
                    st.session_state[K.LATEST_RESULT] = None
                    st.session_state[K.LATEST_IMAGE] = None
                    st.session_state[K.ACTIVE_PHASE] = 0
                    st.session_state[K.LAST_ERROR] = ""
                    st.rerun()
        with col2:
            if st.button("🗑", key=f"del_{sid}", help="删除"):
                delete_conversation(sid)
                if sid == current_id:
                    reset_session()
                st.rerun()


def _get_current_title(messages: list[dict]) -> str:
    for m in messages:
        if m.get("role") == "user":
            content = m.get("content", "").split("\n")[0].strip()
            return content[:20] + ("…" if len(content) > 20 else "")
    return "新对话"


def _save_current() -> None:
    conv_id = st.session_state.get(K.CONVERSATION_ID, "")
    messages = st.session_state.get(K.MESSAGES, [])
    if conv_id and messages:
        from ..storage import save_conversation
        save_conversation(conv_id, messages)


def _check_key(key_name: str) -> bool:
    val = st.session_state.get(key_name, "")
    return bool(val) and "sk-your" not in val
