# AI Chat
> [English](./README.md)

基于 Streamlit + DeepSeek API 的 AI 对话应用，支持多会话管理、流式输出、历史记录持久化。

## 功能特性

- 💬 **多会话管理** — 新建、加载、删除历史对话
- ⚡ **流式输出** — 打字机效果实时显示 AI 回复
- 📝 **自定义系统提示词**
- 💾 **本地 JSON 持久化** — 对话自动保存到 `sessions/` 目录
- 🧹 **路径安全** — 会话名经过 sanitize 处理，防御路径遍历
- 🛡️ **友好错误处理** — API 异常时 UI 显示提示而非直接崩溃

## 快速开始

### 前置条件

- Python >= 3.13
- DeepSeek API Key

### 安装

```bash
git clone <repo-url>
cd <repo-name>

# 推荐使用虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -e .
```

### 配置

```bash
cp .env.example .env
# 编辑 .env，填入你的 API Key:
# DEEPSEEK_API_KEY=sk-your-key-here
```

### 运行

```bash
streamlit run main.py
```

浏览器访问 `http://localhost:8501` 即可。

## 项目结构

```
.
├── main.py              # 主入口
├── pyproject.toml       # 项目配置与依赖
├── .env.example         # 环境变量模板
├── .gitignore
└── sessions/            # 对话数据（已 gitignore）
```

## 注意事项

- `sessions/` 目录已被 `.gitignore` 忽略，本地对话不会提交到仓库
- API Key 通过环境变量读取，切勿直接写入代码或提交 `.env`
