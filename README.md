# 江小创

一个基于 Streamlit 的对话式文创设计 Demo。项目围绕“武汉文化元素 + AI 设计助手”这个主题实现：用户可以通过自然语言描述想法，让 Agent 先检索文化资料、再参考产品设计规则，最后输出设计方案，并在确认后生成效果图。

这个仓库更适合作为一个 Agent 应用示例来看待，而不是完整的商业产品。它重点展示了几个具体能力：

- 用 Streamlit 搭建可直接运行的多页面交互界面
- 用自定义 ReAct 风格循环组织 LLM 推理与工具调用
- 用本地 JSON 知识库补充特定领域数据
- 在同一条对话链路里串联文本生成、规则检索和图片生成

## 功能概览

- 对话式设计：直接输入需求，Agent 会给出文创产品方案
- 文化检索：从本地武汉文化知识库中查找相关背景和视觉元素
- 规则辅助：根据产品类型读取预设设计规则
- 流式输出：LLM 回复按流式方式展示
- 图片生成：在用户明确要求出图后调用通义万相生成效果图
- 会话保存：对话内容会保存在本地，便于继续查看

## 技术栈

- Python 3.10+
- Streamlit
- OpenAI Python SDK
- 阿里云百炼兼容接口
- 通义千问 `qwen-plus`
- 通义万相 `wan2.7-image-pro`

## 项目结构

```text
.
├── app.py
├── 启动.bat
├── pages/
│   ├── 00_开始设计.py
│   └── 02_API配置.py
├── src/
│   ├── agent.py
│   ├── config.py
│   ├── prompts.py
│   ├── state.py
│   ├── storage.py
│   ├── tools.py
│   ├── data/
│   │   ├── design_rules.json
│   │   └── wuhan_culture.json
│   └── ui/
│       ├── conversation.py
│       ├── sidebar.py
│       ├── solution.py
│       └── styles.py
├── tests/
│   └── test_tools.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## 核心模块说明

- `src/agent.py`
  负责 Agent 主循环，处理流式输出、工具调用和多轮推理。

- `src/tools.py`
  定义文化检索、设计规则查询和图片生成相关工具。

- `src/data/wuhan_culture.json`
  本地文化知识库，存放武汉文化元素的结构化数据。

- `src/data/design_rules.json`
  不同产品类型的设计规则数据。

- `pages/00_开始设计.py`
  主交互页面，负责聊天区、快捷面板和结果展示。

- `pages/02_API配置.py`
  API Key 和模型配置页面。

## 运行方式

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制一份环境变量模板：

```bash
cp .env.example .env
```

然后在 `.env` 中填写你的百炼 API Key：

```env
DASHSCOPE_API_KEY=your-api-key
LLM_MODEL=qwen-plus
IMAGE_MODEL=wan2.7-image-pro
```

如果你在 Windows PowerShell 中操作，也可以直接手动新建 `.env` 文件。

### 3. 启动项目

```bash
streamlit run app.py
```

启动后默认访问：

```text
http://localhost:8501
```

Windows 用户也可以直接运行 [启动.bat](/d:/江小创/江小创/启动.bat)。

## 使用说明

1. 打开应用后，先在“API 配置”页填入百炼 API Key。
2. 回到“开始设计”页，选择文化元素、风格和产品类型，或直接输入需求。
3. Agent 会调用文化检索和设计规则工具，生成一版设计方案。
4. 你可以继续通过对话调整方案，例如修改配色、字体、构图或风格。
5. 当你明确要求“出图”时，Agent 会调用图片生成接口生成效果图。

## 当前实现特点

- 工具调用逻辑比较直观，适合学习和演示
- 数据来源以本地 JSON 为主，便于替换成其他城市或主题
- UI 偏 Demo 风格，适合课程作业、比赛展示或原型验证

## 已知限制

- 当前文化知识库范围有限，主要围绕武汉元素
- 图片生成依赖外部 API，速度和稳定性受网络与账户状态影响
- 会话持久化使用本地文件，不适合多人协作或生产环境
- README 中提到的模型和接口基于当前代码实现，后续如果更换服务商需要同步调整配置

## 测试

项目包含基础测试文件：

```bash
pytest
```

如果你的环境里还没有安装测试依赖，请先执行 `pip install -r requirements.txt`。

## 后续可扩展方向

- 增加更多城市或主题的文化知识库
- 将工具系统替换为真实搜索或检索服务
- 接入更稳定的会话存储方式
- 补充更多自动化测试
- 优化提示词、状态管理和前端交互细节

## 说明

仓库中的 `.env` 不应该提交到 GitHub。提交前建议确认 `.gitignore` 已正确排除敏感配置。
