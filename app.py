"""江小创 · 武汉文创 AI 设计助手 — 入口路由"""

import streamlit as st

st.set_page_config(
    page_title="江小创 · 武汉文创 AI 设计师",
    page_icon="🏯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

pages = [
    st.Page("pages/00_开始设计.py", title="🏯 开始设计", default=True),
    st.Page("pages/02_API配置.py", title="🔐 API 配置"),
]

pg = st.navigation(pages)
pg.run()
