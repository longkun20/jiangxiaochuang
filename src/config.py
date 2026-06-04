"""配置管理 — 加载环境变量，统一管理 API Key 和模型配置"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """全局配置"""

    # LLM — 通义千问（百炼平台，OpenAI 兼容接口）
    LLM_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    LLM_BASE_URL: str = os.getenv(
        "LLM_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen-plus")

    # 图片生成 — 通义万相（百炼平台）
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    IMAGE_MODEL: str = os.getenv("IMAGE_MODEL", "wan2.7-image-pro")

    # 应用配置
    TEMPERATURE: float = 0.9
    MAX_TOKENS: int = 2048

    @classmethod
    def validate(cls) -> list[str]:
        """验证必要配置，返回缺失项列表"""
        missing: list[str] = []
        if not cls.DASHSCOPE_API_KEY or cls.DASHSCOPE_API_KEY == "sk-your-dashscope-key":
            missing.append("DASHSCOPE_API_KEY（百炼 API Key，文本+图片都需要）")
        return missing
