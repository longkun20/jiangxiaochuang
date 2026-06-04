"""Session state 管理 — 键名常量和读写工具"""

from __future__ import annotations

import re
from html import escape
from textwrap import dedent
from typing import Any

import streamlit as st


# ═════════════════════════════════════════════════════════════
# Session Key 常量
# ═════════════════════════════════════════════════════════════

class K:
    """session_state 键名，避免字符串散落"""

    MESSAGES = "messages"
    RUNNING = "running"
    SELECTED_ELEMENTS = "selected_elements"
    CUSTOM_ELEMENT = "custom_element"
    STYLE_CHOICE = "style_choice"
    CUSTOM_STYLE = "custom_style"
    PRODUCT_CHOICE = "product_choice"
    CUSTOM_PRODUCT = "custom_product"
    TOOL_LOG = "tool_log"
    ACTIVE_PHASE = "active_phase"
    LATEST_RESULT = "latest_result"
    LATEST_IMAGE = "latest_image"
    LAST_ERROR = "last_error"
    MANUAL_IMAGE_REQUEST = "manual_image_request"
    QUICK_START_TRIGGER = "quick_start_trigger"
    DESIGN_REQUIREMENT = "design_requirement"
    CONVERSATION_ID = "conversation_id"

    # API keys (shared across pages)
    API_DASHSCOPE_KEY = "api_dashscope_key"


# ═════════════════════════════════════════════════════════════
# 默认值与元素常量
# ═════════════════════════════════════════════════════════════

ELEMENT_OPTIONS: list[tuple[str, str]] = [
    ("🏯 黄鹤楼", "黄鹤楼"),
    ("🍜 热干面", "热干面"),
    ("🌸 樱花", "樱花"),
    ("🌉 长江大桥", "长江大桥"),
    ("🔔 编钟", "编钟"),
    ("🌊 东湖", "东湖"),
    ("🏛️ 江汉关", "江汉关"),
    ("🚢 知音号", "知音号"),
    ("🥣 藕汤", "藕汤"),
    ("🦞 小龙虾", "小龙虾"),
    ("🏘️ 户部巷", "户部巷"),
    ("💬 武汉话", "武汉话"),
    ("🎵 古琴台", "古琴台"),
    ("⚔️ 楚文化", "楚文化"),
    ("💡 光谷", "光谷"),
]

STYLE_OPTIONS: list[str] = [
    "国潮", "极简", "赛博朋克", "可爱卡通", "水墨风", "复古胶片", "新中式", "🎨 自定义…"
]

PRODUCT_OPTIONS: list[str] = [
    "T恤", "冰箱贴", "帆布包", "手机壳", "马克杯", "明信片", "🛍️ 自定义…"
]

WORKFLOW_STEPS: list[tuple[str, str]] = [
    ("需求装配", "选元素和风格"),
    ("文化检索", "Agent 调资料"),
    ("方案生成", "输出设计与文案"),
    ("效果出图", "确认后生成画面"),
]

TOOL_PHASE_MAP: dict[str, int] = {
    "search_culture": 1,
    "check_design_rules": 2,
    "generate_image": 3,
}


# ═════════════════════════════════════════════════════════════
# Session State 初始化
# ═════════════════════════════════════════════════════════════

def ensure_session_state() -> None:
    """确保所有 session_state key 存在"""
    defaults: dict[str, Any] = {
        K.MESSAGES: [],
        K.RUNNING: False,
        K.SELECTED_ELEMENTS: [],
        K.CUSTOM_ELEMENT: "",
        K.STYLE_CHOICE: "国潮",
        K.CUSTOM_STYLE: "",
        K.PRODUCT_CHOICE: "T恤",
        K.CUSTOM_PRODUCT: "",
        K.TOOL_LOG: [],
        K.ACTIVE_PHASE: 0,
        K.LATEST_RESULT: None,
        K.LATEST_IMAGE: None,
        K.LAST_ERROR: "",
        K.MANUAL_IMAGE_REQUEST: None,
        K.QUICK_START_TRIGGER: False,
        K.DESIGN_REQUIREMENT: "",
        K.CONVERSATION_ID: "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # 自动生成对话 ID
    if not st.session_state[K.CONVERSATION_ID]:
        from .storage import new_conversation_id
        st.session_state[K.CONVERSATION_ID] = new_conversation_id()

    # 从 .env 同步 API key 到 session（如果 session 中还没有）
    if K.API_DASHSCOPE_KEY not in st.session_state:
        from .config import Config
        st.session_state[K.API_DASHSCOPE_KEY] = Config.DASHSCOPE_API_KEY
    if "api_llm_model" not in st.session_state:
        from .config import Config
        st.session_state["api_llm_model"] = Config.LLM_MODEL


def reset_session() -> None:
    """重置会话状态，开始新对话"""
    from .storage import new_conversation_id
    st.session_state[K.MESSAGES] = []
    st.session_state[K.TOOL_LOG] = []
    st.session_state[K.LATEST_RESULT] = None
    st.session_state[K.LATEST_IMAGE] = None
    st.session_state[K.ACTIVE_PHASE] = 0
    st.session_state[K.LAST_ERROR] = ""
    st.session_state[K.CONVERSATION_ID] = new_conversation_id()


# ═════════════════════════════════════════════════════════════
# 值读取工具
# ═════════════════════════════════════════════════════════════

def current_elements() -> list[str]:
    """返回当前选中的文化元素列表"""
    selected_labels: list[str] = st.session_state.get(K.SELECTED_ELEMENTS, [])
    elements = [name for label, name in ELEMENT_OPTIONS if label in selected_labels]
    custom: str = st.session_state.get(K.CUSTOM_ELEMENT, "").strip()
    if custom:
        elements.append(custom)
    return elements


def current_style() -> str:
    """返回当前设计风格"""
    choice: str = st.session_state.get(K.STYLE_CHOICE, "国潮")
    if choice == "🎨 自定义…":
        return st.session_state.get(K.CUSTOM_STYLE, "").strip() or "国潮"
    return choice


def current_product() -> str:
    """返回当前产品类型"""
    choice: str = st.session_state.get(K.PRODUCT_CHOICE, "T恤")
    if choice == "🛍️ 自定义…":
        return st.session_state.get(K.CUSTOM_PRODUCT, "").strip() or "T恤"
    return choice


# ═════════════════════════════════════════════════════════════
# 日志和结果管理
# ═════════════════════════════════════════════════════════════

def append_tool_log(title: str, detail: str) -> None:
    """追加工具调用日志（保留最近 6 条）"""
    log: list[dict] = st.session_state[K.TOOL_LOG]
    log.append({"title": title, "detail": detail})
    st.session_state[K.TOOL_LOG] = log[-6:]


def update_latest_result(content: str, image: str | None = None, caption: str = "") -> None:
    """更新当前方案结果"""
    st.session_state[K.LATEST_RESULT] = {
        "content": content,
        "style": current_style(),
        "product": current_product(),
    }
    if image:
        st.session_state[K.LATEST_IMAGE] = {"base64": image, "caption": caption}


# ═════════════════════════════════════════════════════════════
# 内容提取
# ═════════════════════════════════════════════════════════════

def extract_product_name(content: str) -> str | None:
    """从内容中提取产品名称"""
    match = re.search(r"#+\s*.*产品名称\s*\n+([^\n#]+)", content)
    return match.group(1).strip() if match else None


def extract_section(content: str, *headings: str) -> str:
    """按标题提取章节内容（多策略）"""
    for heading in headings:
        # 策略1: 严格 Markdown 标题匹配 (### 🎨 视觉描述)
        pattern = rf"^#{{1,4}}\s*[^#\n]*?{heading}\s*$"
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if re.search(pattern, line.strip()):
                # 收集后续行直到下一个 Markdown 标题
                parts = []
                for j in range(i + 1, len(lines)):
                    if re.match(r"^#{1,4}\s", lines[j]):
                        break
                    parts.append(lines[j])
                result = "\n".join(parts).strip()
                if result:
                    return result

        # 策略2: 宽松匹配 — 行中包含 ### 和关键词，不要求严格行首行尾
        pattern2 = rf"#+\s*.*{heading}"
        match = re.search(pattern2, content)
        if match:
            rest = content[match.end():]
            # 取到下一个 # 标题之前
            next_heading = re.search(r"\n#+\s", rest)
            if next_heading:
                result = rest[:next_heading.start()].strip()
            else:
                result = rest.strip()
            if result:
                return result

    return ""


def summary_markdown(content: str) -> str:
    """将方案内容压缩为摘要"""
    sections: list[str] = []
    name = extract_product_name(content)
    if name:
        sections.append(f"**产品名**  \n{name}")

    for heading, label in [
        ("设计理念", "设计理念"),
        ("视觉描述", "视觉描述"),
        ("产品文案", "产品文案"),
    ]:
        text = extract_section(content, heading)
        if not text:
            continue
        cleaned = re.sub(r"\n{2,}", "\n", text)
        if len(cleaned) > 180:
            cleaned = cleaned[:180].rstrip() + "…"
        sections.append(f"**{label}**  \n{cleaned}")

    if not sections:
        trimmed = content.strip()
        if len(trimmed) > 280:
            trimmed = trimmed[:280].rstrip() + "…"
        return trimmed
    return "\n\n".join(sections)


# ═════════════════════════════════════════════════════════════
# HTML 渲染
# ═════════════════════════════════════════════════════════════

def render_html(content: str) -> None:
    """渲染 HTML 内容（去缩进）"""
    st.markdown(dedent(content).strip(), unsafe_allow_html=True)
