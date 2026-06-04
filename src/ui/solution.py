"""方案面板 — 完整方案的结构化展示（卡片式，嵌入聊天或独立展示）"""

from __future__ import annotations

from html import escape

import streamlit as st

from ..state import (
    K,
    extract_section,
    summary_markdown,
    render_html,
)


def render_solution_card(result: dict | None = None) -> None:
    """在对话下方渲染方案摘要卡片"""
    if result is None:
        result = st.session_state.get(K.LATEST_RESULT)
    if not result:
        return

    content: str = result["content"]
    name = _extract_product_name(content)
    summary = summary_markdown(content)

    with st.container():
        st.markdown("---")
        if name:
            st.markdown(
                f"<div class='product-name-display'>{escape(name)}</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            f"<div class='solution-summary-card'>{summary}</div>",
            unsafe_allow_html=True,
        )

        # 三个标签：完整方案 / 文案速取 / 出图
        tabs = st.tabs(["📋 完整方案", "📝 文案速取", "🖼️ 出图"])
        with tabs[0]:
            _render_full_solution(content)
        with tabs[1]:
            _render_copy_actions(result)
        with tabs[2]:
            _render_image_zone(result)


def _extract_product_name(content: str) -> str | None:
    import re
    match = re.search(r"#+\s*.*产品名称\s*\n+([^\n#]+)", content)
    return match.group(1).strip() if match else None


# ── 内部渲染 ──

def _render_full_solution(content: str) -> None:
    """完整方案渲染"""
    sections = _parse_sections(content)

    # 产品名称
    if sections.get("产品名称"):
        st.markdown(
            f"<div class='product-name-display'>{escape(sections['产品名称'].strip())}</div>",
            unsafe_allow_html=True,
        )

    # 设计理念
    if sections.get("设计理念"):
        st.markdown("**💡 设计理念**")
        st.markdown(sections["设计理念"].strip())

    # 视觉描述
    if sections.get("视觉描述"):
        st.markdown("**🎨 视觉描述**")
        st.markdown(sections["视觉描述"].strip())

    # 细节巧思
    if sections.get("设计细节"):
        st.markdown("**✨ 设计细节**")
        st.markdown(sections["设计细节"].strip())

    # 完整原文折叠
    with st.expander("查看完整输出"):
        st.markdown(content)


def _render_copy_actions(result: dict) -> None:
    """文案速取"""
    content = result["content"]
    marketing_copy = extract_section(content, "营销文案", "营销方案", "小红书文案")
    product_copy = extract_section(content, "产品文案")
    visual_desc = extract_section(content, "视觉描述")

    if product_copy:
        st.markdown("**📝 产品文案**")
        st.markdown(
            f"<div class='marketing-card'>{escape(product_copy)}</div>",
            unsafe_allow_html=True,
        )
        st.text_area("产品文案文本", product_copy, height=80, key="copy_product")

    if marketing_copy:
        st.markdown("**📱 营销文案**")
        st.markdown(
            f"<div class='marketing-card'>{escape(marketing_copy)}</div>",
            unsafe_allow_html=True,
        )
        st.text_area("营销文案文本", marketing_copy, height=120, key="copy_marketing")

    if visual_desc:
        st.markdown("**🎨 视觉描述 Prompt**")
        st.text_area("图片生成 Prompt", visual_desc, height=120, key="copy_visual")

    if not product_copy and not marketing_copy and not visual_desc:
        st.info("暂未识别到结构化文案，请查看完整方案标签。")


def _render_image_zone(result: dict) -> None:
    """出图操作区"""
    image: dict | None = st.session_state.get(K.LATEST_IMAGE)
    visual_desc = extract_section(result["content"], "视觉描述")

    if image:
        import base64
        st.image(
            base64.b64decode(image["base64"]),
            caption=image.get("caption", "AI 生成"),
            use_container_width=True,
        )
        st.caption("👆 这是当前方案的生成效果图")

    if visual_desc:
        with st.container():
            st.markdown("<div class='image-action-zone'>", unsafe_allow_html=True)
            prompt_value = st.text_area(
                "出图 Prompt（可修改后重新生成）",
                value=visual_desc,
                height=120,
                key="manual_image_prompt_v2",
            )
            btn_label = "🔄 重新生成" if image else "🖼️ 生成效果图"
            if st.button(btn_label, key="gen_image_v2", use_container_width=True):
                st.session_state[K.MANUAL_IMAGE_REQUEST] = {
                    "prompt": prompt_value.strip(),
                    "style": result.get("style", ""),
                    "product": result.get("product", ""),
                }
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        # 提取失败 — 显示诊断信息
        _show_extraction_help(result["content"])


# ── 章节解析 ──

def _parse_sections(content: str) -> dict[str, str]:
    """按 Markdown 标题拆分章节"""
    sections: dict[str, str] = {}
    current_key: str | None = None

    key_mapping = {
        "产品名称": "产品名称",
        "设计理念": "设计理念",
        "视觉描述": "视觉描述",
        "设计细节": "设计细节",
        "细节巧思": "设计细节",
        "营销文案": "营销",
        "营销方案": "营销",
        "小红书文案": "营销",
        "产品文案": "产品文案",
    }

    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            for pattern, key in key_mapping.items():
                if pattern in heading:
                    current_key = key
                    break
            else:
                current_key = heading
            continue

        if current_key and stripped:
            sections.setdefault(current_key, "")
            sections[current_key] += stripped + "\n"

    return sections


def _show_extraction_help(content: str) -> None:
    """视觉描述提取失败时，显示诊断帮助"""
    import re as _re

    # 检测所有 Markdown 标题
    headings = _re.findall(r"^#{1,4}\s*(.+)$", content, _re.MULTILINE)

    st.warning("未提取到「视觉描述」章节，无法自动出图。")

    if headings:
        st.caption(f"检测到以下标题：{'、'.join(headings)}")
        st.caption("请确认方案中包含「🎨 视觉描述」标题。如果没有，在聊天中说「补充视觉描述」让 AI 重新生成。")
    else:
        st.caption("未检测到任何 Markdown 标题。AI 可能未按标准格式输出方案。")
        st.caption("请在聊天中说「请按标准格式重新输出方案，包含视觉描述章节」。")

    # 手动输入备选
    with st.expander("🔧 手动输入视觉描述"):
        manual_prompt = st.text_area(
            "请输入视觉描述",
            height=120,
            key="manual_fallback_prompt",
            placeholder="描述画面构图、配色、元素排列、风格…",
        )
        if st.button("🖼️ 用此描述生成图片", key="manual_fallback_gen"):
            result_key = K.LATEST_RESULT
            result = st.session_state.get(result_key, {})
            if manual_prompt.strip() and result:
                st.session_state[K.MANUAL_IMAGE_REQUEST] = {
                    "prompt": manual_prompt.strip(),
                    "style": result.get("style", ""),
                    "product": result.get("product", ""),
                }
                st.rerun()


# 保留兼容导出
result_tabs = _render_full_solution
