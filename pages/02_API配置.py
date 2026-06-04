"""API 配置页面 — 百炼 API Key"""

from __future__ import annotations

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import Config
from src.state import K

st.set_page_config(page_title="API 配置", page_icon="🔐", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #fdf6e3 0%, #fceabb 100%); }
    .config-card {
        background: white; border-radius: 12px; padding: 1.5rem;
        margin: 1rem 0; box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }
    .warning-box {
        background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px;
        padding: 1rem; margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔐 API 配置")

st.markdown("""
<div class="warning-box">
⚠️ <b>安全提醒</b>：API Key 仅保存在当前浏览器会话中，关闭后自动清除。<br/>
<b>请勿</b>将包含真实 Key 的 .env 文件提交到代码仓库。
</div>
""", unsafe_allow_html=True)

# ── 初始化 ──
if K.API_DASHSCOPE_KEY not in st.session_state:
    st.session_state[K.API_DASHSCOPE_KEY] = Config.DASHSCOPE_API_KEY
if "api_llm_model" not in st.session_state:
    st.session_state["api_llm_model"] = Config.LLM_MODEL

# ── 百炼 API Key（文本 + 图片共用） ──
st.markdown('<div class="config-card">', unsafe_allow_html=True)
st.markdown("### 🔑 百炼 API Key（必填）")
st.caption(
    "通义千问（文本）和通义万相（图片）共用同一个百炼 API Key。"
    "获取地址：https://bailian.console.aliyun.com"
)

dashscope_key = st.text_input(
    "百炼 API Key",
    value=st.session_state[K.API_DASHSCOPE_KEY],
    type="password",
    placeholder="sk-...",
    help="阿里云百炼平台 API Key，文本生成和图片生成共用。",
)

st.markdown("</div>", unsafe_allow_html=True)

# ── 模型选择 ──
st.markdown('<div class="config-card">', unsafe_allow_html=True)
st.markdown("### 🤖 模型配置")

llm_model = st.selectbox(
    "文本模型（通义千问）",
    ["qwen-plus", "qwen-max", "qwen-turbo", "qwen-plus-latest", "qwen-max-latest"],
    index=0 if st.session_state["api_llm_model"] == "qwen-plus" else 0,
    help="qwen-plus：性价比推荐 | qwen-max：最强能力 | qwen-turbo：最快速度",
)

st.caption("图片模型固定使用通义万相 wan2.7-image-pro，无需额外配置。")
st.markdown("</div>", unsafe_allow_html=True)

# ── 操作 ──
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 4])

with col1:
    if st.button("💾 保存配置", use_container_width=True):
        st.session_state[K.API_DASHSCOPE_KEY] = dashscope_key
        st.session_state["api_llm_model"] = llm_model
        st.success("✅ 配置已保存！切换到「开始设计」页面即可使用。")

with col2:
    if st.button("🔄 恢复默认", use_container_width=True):
        st.session_state[K.API_DASHSCOPE_KEY] = Config.DASHSCOPE_API_KEY
        st.session_state["api_llm_model"] = Config.LLM_MODEL
        st.rerun()

# ── 状态 ──
st.markdown("---")
st.markdown("### 📊 当前配置状态")

has_key = (
    bool(st.session_state[K.API_DASHSCOPE_KEY])
    and st.session_state[K.API_DASHSCOPE_KEY] != "sk-your-dashscope-key"
)
if has_key:
    st.success(f"✅ 百炼 API：已配置")
    st.caption(f"文本模型：{st.session_state['api_llm_model']}")
    st.caption(f"图片模型：{Config.IMAGE_MODEL}")
else:
    st.error("❌ 百炼 API：未配置")

st.divider()
st.caption("配置保存在浏览器会话中，关闭后需重新输入。可在 .env 文件中持久化配置。")
