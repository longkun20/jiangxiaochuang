"""全局 CSS 样式 — 干净现代的对话式界面"""

STYLES = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Serif+SC:wght@400;600;700&display=swap');

    /* ── 基础 ── */
    html, body, [class*="css"] {
        font-family: "Inter", "Noto Serif SC", -apple-system, sans-serif;
    }
    .stApp {
        background: #faf8f3;
    }
    .main .block-container {
        max-width: 1200px;
        padding: 0;
    }

    /* ── 隐藏 Streamlit 默认元素 ── */
    #MainMenu, footer, .stDeployButton, [data-testid="stToolbar"] {
        display: none !important;
    }
    [data-testid="stHeader"] { background: transparent !important; }

    /* ── 隐藏原生 sidebar（用页面左栏替代） ── */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    [data-testid="stSidebarContent"] {
        display: none !important;
    }
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    button[kind="header"] {
        display: none !important;
    }

    /* ── 左栏按钮 ── */
    .stButton > button {
        border-radius: 10px !important;
    }

    /* ── 聊天消息 ── */
    [data-testid="stChatMessage"] {
        background: transparent !important;
        padding: 0.3rem 0 !important;
    }

    /* 用户消息 — 墨蓝色气泡靠右 */
    [data-testid="stChatMessage"][data-testid*="user"] [data-testid="stMarkdownContainer"] {
        background: #2c3e50 !important;
        color: #f5f0e8 !important;
        padding: 0.75rem 1rem !important;
        border-radius: 16px 16px 4px 16px !important;
        max-width: 75% !important;
        margin-left: auto !important;
        font-size: 0.95rem;
        line-height: 1.65;
    }

    /* 助手消息 — 暖米纸气泡靠左 */
    [data-testid="stChatMessage"][data-testid*="assistant"] [data-testid="stMarkdownContainer"] {
        background: #fdf6e3 !important;
        color: #2c2416 !important;
        padding: 0.9rem 1.1rem !important;
        border-radius: 4px 16px 16px 16px !important;
        max-width: 92% !important;
        border: 1px solid #ede4cd !important;
        font-size: 0.95rem;
        line-height: 1.75;
        box-shadow: 0 1px 4px rgba(60, 40, 20, 0.04);
    }

    /* ── 输入框 ── */
    [data-testid="stChatInput"] textarea {
        border-radius: 12px !important;
        border: 1px solid #e0d8c5 !important;
        background: #fffefb !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.95rem;
    }
    [data-testid="stChatInput"] textarea:focus {
        border-color: #c0392b !important;
        box-shadow: 0 0 0 3px rgba(192,57,43,0.1) !important;
    }

    /* ── 按钮 ── */
    .stButton > button {
        background: #2c3e50 !important;
        color: #f5f0e8 !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        padding: 0.55rem 1rem !important;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: #1a2d3d !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(44,62,80,0.3);
    }
    .stButton > button:disabled {
        background: #ddd8cd !important;
        color: #a09888 !important;
        transform: none;
        box-shadow: none;
    }

    /* ── 表单控件 ── */
    .stMultiSelect > div > div,
    .stSelectbox > div > div,
    .stTextInput > div > div > input,
    .stTextArea textarea {
        background: #fffefb !important;
        border: 1px solid #e0d8c5 !important;
        border-radius: 8px !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] { gap: 0; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 0 !important;
        background: transparent;
        color: #8a8070;
        padding: 0.5rem 1rem;
        font-weight: 500;
        border-bottom: 2px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        background: transparent !important;
        color: #2c3e50 !important;
        border-bottom-color: #2c3e50;
    }

    /* ── Expander (工具调用展示) ── */
    .streamlit-expanderHeader {
        font-size: 0.8rem !important;
        color: #8a8070 !important;
        background: transparent !important;
        border: none !important;
        padding: 0.2rem 0 !important;
    }

    /* ── 图片 ── */
    .stImage img {
        border-radius: 12px !important;
        box-shadow: 0 2px 16px rgba(60,40,20,0.08) !important;
    }

    /* ── Spinner ── */
    .stSpinner > div {
        border-top-color: #2c3e50 !important;
    }

    /* ═══════════════════════════════════════════
       自定义组件
       ═══════════════════════════════════════════ */

    /* 工具调用卡片 */
    .tool-call-card {
        background: #f5efe0;
        border: 1px solid #e8ddc5;
        border-radius: 10px;
        padding: 0.5rem 0.8rem;
        margin: 0.3rem 0;
        font-size: 0.82rem;
        color: #6b5e48;
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
    }
    .tool-call-card .icon { font-size: 1rem; }
    .tool-call-card .label { font-weight: 600; color: #4a3f2f; }

    /* 方案结果卡片 */
    .result-card {
        background: #fffefb;
        border: 1px solid #e8e0cc;
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        margin: 0.6rem 0;
        box-shadow: 0 2px 12px rgba(60,40,20,0.04);
    }
    .result-card h3 {
        margin: 0 0 0.5rem 0;
        font-size: 1.05rem;
        color: #2c2416;
    }
    .result-card .meta {
        font-size: 0.8rem;
        color: #8a8070;
        margin-bottom: 0.8rem;
    }

    /* 方案摘要 */
    .solution-summary-card {
        background: #fdf7ec;
        border: 1px solid #efe0c0;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
        line-height: 1.7;
    }

    /* 产品名字大标题 */
    .product-name-display {
        font-size: 1.6rem;
        font-weight: 700;
        color: #2c3e50;
        text-align: center;
        padding: 1rem;
    }

    /* 营销文案卡 */
    .marketing-card {
        background: #fdf6e3;
        border: 1px solid #efe0c0;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
        font-size: 0.95rem;
        line-height: 1.8;
    }

    /* 出图区 */
    .image-action-zone {
        background: #faf8f3;
        border: 1px dashed #d5cfbf;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        text-align: center;
    }

    /* 欢迎页/空状态 */
    .welcome {
        text-align: center;
        padding: 3rem 2rem;
        color: #8a8070;
    }
    .welcome .icon { font-size: 3rem; margin-bottom: 1rem; }
    .welcome h2 { font-size: 1.3rem; color: #4a3f2f; margin-bottom: 0.5rem; }
    .welcome p { font-size: 0.9rem; line-height: 1.7; max-width: 500px; margin: 0 auto; }
    .welcome .hints {
        display: flex; flex-wrap: wrap; gap: 0.5rem; justify-content: center; margin-top: 1.5rem;
    }
    .welcome .hint-chip {
        background: #fffefb;
        border: 1px solid #e8ddc5;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        font-size: 0.82rem;
        color: #6b5e48;
        cursor: default;
    }

    /* ── 分屏滚动容器（st.container(height=...)） ── */
    /* 固定高度容器自带滚动 + 边框，这里把边框/圆角调成暖色主题 */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #e8e0cc !important;
        border-radius: 14px !important;
        background: #fffefb;
        box-shadow: 0 1px 8px rgba(60,40,20,0.04);
    }
    /* 左栏（第一列）配置面板 — 稍深的背景制造左右色差 */
    [data-testid="stColumn"]:first-child [data-testid="stVerticalBlockBorderWrapper"] {
        background: #f7f2e7;
        padding: 0.4rem 0.8rem;
    }
    /* 右栏（对话流）— 内边距更宽松 */
    [data-testid="stColumn"]:last-child [data-testid="stVerticalBlockBorderWrapper"] {
        padding: 0.6rem 1.1rem;
    }

    @media (max-width: 768px) {
        .main .block-container { padding: 0.5rem 0.8rem !important; }
        [data-testid="stChatMessage"][data-testid*="user"] [data-testid="stMarkdownContainer"] {
            max-width: 90% !important;
        }
    }
</style>
"""
