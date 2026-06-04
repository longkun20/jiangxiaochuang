"""对话持久化存储 — 本地 JSON 文件"""

from __future__ import annotations

import json
import uuid
import time
from pathlib import Path

# 存储目录
_STORAGE_DIR = Path(__file__).resolve().parent.parent / ".streamlit" / "conversations"


def _ensure_dir() -> None:
    _STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def list_conversations() -> list[dict]:
    """列出所有历史对话，按更新时间倒序"""
    _ensure_dir()
    results = []
    for f in _STORAGE_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            results.append({
                "id": data.get("id", f.stem),
                "title": data.get("title", "未命名对话"),
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
                "message_count": len(data.get("messages", [])),
            })
        except (json.JSONDecodeError, OSError):
            continue
    results.sort(key=lambda x: x["updated_at"], reverse=True)
    return results


def save_conversation(conv_id: str, messages: list[dict], title: str = "") -> None:
    """保存或更新一个对话"""
    _ensure_dir()
    existing = load_conversation(conv_id)
    now = time.strftime("%Y-%m-%d %H:%M:%S")

    data = {
        "id": conv_id,
        "title": title or existing.get("title", "未命名对话"),
        "created_at": existing.get("created_at", now),
        "updated_at": now,
        "messages": messages,
    }

    # 如果没有标题，从第一条用户消息自动生成
    if not data["title"] or data["title"] == "未命名对话":
        for m in messages:
            if m.get("role") == "user":
                content = m.get("content", "")
                # 取第一行或前30个字符
                first_line = content.split("\n")[0].strip()
                data["title"] = first_line[:30] + ("…" if len(first_line) > 30 else "")
                break

    filepath = _STORAGE_DIR / f"{conv_id}.json"
    filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_conversation(conv_id: str) -> dict:
    """加载一个对话，不存在则返回空 dict"""
    _ensure_dir()
    filepath = _STORAGE_DIR / f"{conv_id}.json"
    if not filepath.exists():
        return {}
    try:
        return json.loads(filepath.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def delete_conversation(conv_id: str) -> None:
    """删除一个对话"""
    _ensure_dir()
    filepath = _STORAGE_DIR / f"{conv_id}.json"
    if filepath.exists():
        filepath.unlink()


def new_conversation_id() -> str:
    """生成新的对话 ID"""
    return uuid.uuid4().hex[:12]
