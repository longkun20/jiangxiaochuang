"""工具系统单元测试"""

import json
import sys
import os
from pathlib import Path

# 项目根目录加入路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.tools import (
    search_culture,
    check_design_rules,
    execute_tool,
    ToolResult,
    TOOL_DEFINITIONS,
    WUHAN_CULTURE_DB,
    DESIGN_RULES,
)


class TestToolDefinitions:
    """工具注册表测试"""

    def test_tools_registered(self):
        """确认 3 个工具都已注册"""
        tool_names = {t["function"]["name"] for t in TOOL_DEFINITIONS}
        assert "search_culture" in tool_names
        assert "check_design_rules" in tool_names

    def test_search_culture_params(self):
        """search_culture 需要 element_name 参数"""
        tool = next(t for t in TOOL_DEFINITIONS if t["function"]["name"] == "search_culture")
        required = tool["function"]["parameters"].get("required", [])
        assert "element_name" in required

    def test_check_design_rules_params(self):
        """check_design_rules 需要 product 参数"""
        tool = next(t for t in TOOL_DEFINITIONS if t["function"]["name"] == "check_design_rules")
        required = tool["function"]["parameters"].get("required", [])
        assert "product" in required


class TestCultureKnowledgeBase:
    """文化知识库测试"""

    def test_data_loaded(self):
        """数据文件已正确加载"""
        assert len(WUHAN_CULTURE_DB) >= 15
        assert "黄鹤楼" in WUHAN_CULTURE_DB

    def test_culture_field_structure(self):
        """每个元素包含必要字段"""
        for name, info in WUHAN_CULTURE_DB.items():
            assert "历史" in info, f"{name} 缺少 '历史' 字段"
            assert "符号" in info, f"{name} 缺少 '符号' 字段"
            assert "配色" in info, f"{name} 缺少 '配色' 字段"
            assert "关键词" in info, f"{name} 缺少 '关键词' 字段"

    def test_search_exact_match(self):
        """精确匹配测试"""
        result = search_culture("黄鹤楼")
        assert result.success
        assert result.metadata["match_type"] == "exact"
        assert "天下江山第一楼" in result.content

    def test_search_fuzzy_match(self):
        """模糊匹配测试"""
        result = search_culture("热干")
        assert result.success
        assert result.metadata["match_type"] == "fuzzy"

    def test_search_not_found(self):
        """未找到元素"""
        result = search_culture("不存在的元素XYZ")
        assert not result.success

    def test_search_empty(self):
        """空输入"""
        result = search_culture("")
        assert not result.success


class TestDesignRules:
    """设计规范测试"""

    def test_data_loaded(self):
        """设计规范已加载"""
        assert len(DESIGN_RULES) >= 6
        assert "T恤" in DESIGN_RULES
        assert "冰箱贴" in DESIGN_RULES
        assert "帆布包" in DESIGN_RULES

    def test_known_product(self):
        """已知产品类型"""
        result = check_design_rules("T恤")
        assert result.success
        assert "A4" in result.content or "21" in result.content

    def test_unknown_product_graceful(self):
        """未知产品类型 — 不应崩溃，给出通用建议"""
        result = check_design_rules("滑板")
        assert result.success  # 不报错
        assert "灵活设计" in result.content


class TestExecuteTool:
    """工具调度器测试"""

    def test_execute_search_culture(self):
        import json as _json
        result = execute_tool("search_culture", {"element_name": "黄鹤楼"})
        assert result.success
        parsed = _json.loads(result.content)
        # 验证搜索返回了有效数据（至少包含历史字段）
        assert "历史" in parsed

    def test_execute_check_design_rules(self):
        result = execute_tool("check_design_rules", {"product": "帆布包"})
        assert result.success

    def test_execute_unknown_tool(self):
        result = execute_tool("nonexistent_tool", {})
        assert not result.success


class TestToolResult:
    """ToolResult 数据类测试"""

    def test_basic_result(self):
        r = ToolResult(success=True, content="测试成功")
        assert r.success
        assert r.content == "测试成功"
        assert r.metadata == {}

    def test_result_with_metadata(self):
        r = ToolResult(success=True, content="ok", metadata={"source": "test"})
        assert r.metadata["source"] == "test"
