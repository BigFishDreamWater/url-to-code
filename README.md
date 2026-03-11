# url-to-code

[English](#english) | [中文](#中文)

---

<a name="english"></a>

## English

A tool that converts any live website URL into clean, functional frontend code using AI. Enter a URL, and the tool automatically captures a screenshot and extracts the DOM structure via Playwright, then uses LLMs to generate pixel-accurate, interactive code.

Forked from [screenshot-to-code](https://github.com/abi/screenshot-to-code) with significant enhancements.

### Key Features

- **URL-first workflow** — Enter a URL, get code. No need to manually capture screenshots.
- **Playwright-powered** — Local screenshot capture + DOM extraction, no external API dependencies.
- **DOM-aware generation** — Extracted DOM structure is passed to the LLM as additional context, improving semantic accuracy.
- **Multiple input modes** — URL input (primary), image upload, text description, code import.
- **Interactive output** — Generated buttons, links, and controls are real clickable HTML elements with hover/focus states.
- **Multi-stack support** — HTML + Tailwind, HTML + CSS, React + Tailwind, Vue + Tailwind, Bootstrap, Ionic + Tailwind, SVG.
- **Multi-model support** — OpenAI (GPT-4.1/5.x), Anthropic (Claude Sonnet/Opus), Google (Gemini 3), OpenRouter (Kimi K2).
- **Code variants** — Generates multiple options per request for comparison.
- **Live preview** — Real-time preview of generated code in the browser.
- **One-click download** — Download generated code as an HTML file.

### How It Works

```
URL → Playwright (screenshot + DOM extraction) → LLM (image + DOM + prompt) → Generated Code → Live Preview
```

1. User enters a website URL
2. Playwright navigates to the URL, captures a screenshot (1280×800), and extracts a simplified DOM tree
3. Both the screenshot and DOM structure are sent to the LLM along with the selected code stack
4. The LLM generates pixel-accurate, interactive frontend code
5. The code is displayed with a live preview and code editor

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, FastAPI, Playwright, Uvicorn |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Radix UI, Zustand |
| LLM | OpenAI SDK, Anthropic SDK, Google GenAI SDK |
| Package Management | Poetry (backend), npm (frontend) |

### Getting Started

#### Prerequisites

- Python 3.10+
- Node.js 14.18+
- [Poetry](https://python-poetry.org/) (`pip install --upgrade poetry`)
- At least one LLM API key (OpenAI, Anthropic, or Google Gemini)

#### Backend

```bash
cd backend

# Configure API keys
echo "OPENAI_API_KEY=sk-your-key" > .env
echo "ANTHROPIC_API_KEY=your-key" >> .env
echo "GEMINI_API_KEY=your-key" >> .env

# Install dependencies
poetry install
poetry run playwright install chromium

# Start the server
poetry run uvicorn main:app --reload --port 7001
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

#### Docker

```bash
echo "OPENAI_API_KEY=sk-your-key" > .env
docker-compose up -d --build
```

Access at http://localhost:5173.

### Environment Variables

#### Backend (`backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | At least one key | OpenAI or OpenRouter API key |
| `ANTHROPIC_API_KEY` | At least one key | Anthropic API key |
| `GEMINI_API_KEY` | At least one key | Google Gemini API key |
| `OPENAI_BASE_URL` | No | Override base URL (e.g. for OpenRouter: `https://openrouter.ai/api/v1`) |
| `REPLICATE_API_KEY` | No | For Flux Schnell image generation |

#### Frontend (`frontend/.env.local`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_WS_BACKEND_URL` | No | `ws://127.0.0.1:7001` | WebSocket backend URL |
| `VITE_HTTP_BACKEND_URL` | No | `http://127.0.0.1:7001` | HTTP backend URL |

### Differences from screenshot-to-code

| | screenshot-to-code | url-to-code |
|---|---|---|
| Primary input | Upload screenshots | Enter URLs |
| Screenshot engine | ScreenshotOne (external API) | Playwright (local) |
| External API key | ScreenshotOne key required | Not needed |
| DOM context | Not available | Extracted and passed to LLM |
| UI design | Tab-based | URL-first |
| Cost | LLM + ScreenshotOne API | LLM API only |

### License

MIT License — see [LICENSE](LICENSE) for details.

Based on [screenshot-to-code](https://github.com/abi/screenshot-to-code) by [Abi Raja](https://github.com/abi).

---

<a name="中文"></a>

## 中文

一个使用 AI 将任意网站 URL 转换为干净、可用的前端代码的工具。输入一个网址，工具会自动通过 Playwright 截图并提取 DOM 结构，然后利用大语言模型生成像素级精确、可交互的代码。

基于 [screenshot-to-code](https://github.com/abi/screenshot-to-code) 进行了大量增强改造。

### 核心特性

- **URL 优先** — 输入网址，直接生成代码，无需手动截图。
- **Playwright 驱动** — 本地截图 + DOM 提取，不依赖外部 API。
- **DOM 感知生成** — 提取的 DOM 结构作为额外上下文传递给 LLM，提升语义准确性。
- **多种输入方式** — URL 输入（主要）、图片上传、文字描述、代码导入。
- **可交互输出** — 生成的按钮、链接等控件是真实的可点击 HTML 元素，带有 hover/focus 状态。
- **多技术栈** — HTML + Tailwind、HTML + CSS、React + Tailwind、Vue + Tailwind、Bootstrap、Ionic + Tailwind、SVG。
- **多模型支持** — OpenAI (GPT-4.1/5.x)、Anthropic (Claude Sonnet/Opus)、Google (Gemini 3)、OpenRouter (Kimi K2)。
- **多方案对比** — 每次请求生成多个代码方案供选择。
- **实时预览** — 在浏览器中实时预览生成的代码。
- **一键下载** — 将生成的代码下载为 HTML 文件。

### 工作原理

```
URL → Playwright（截图 + DOM 提取）→ LLM（图片 + DOM + 提示词）→ 生成代码 → 实时预览
```

1. 用户输入网站 URL
2. Playwright 访问该 URL，截取页面截图（1280×800），并提取简化的 DOM 树
3. 截图和 DOM 结构连同选定的技术栈一起发送给 LLM
4. LLM 生成像素级精确、可交互的前端代码
5. 代码通过实时预览和代码编辑器展示

### 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.10+、FastAPI、Playwright、Uvicorn |
| 前端 | React 18、TypeScript、Vite、Tailwind CSS、Radix UI、Zustand |
| 大模型 | OpenAI SDK、Anthropic SDK、Google GenAI SDK |
| 包管理 | Poetry（后端）、npm（前端） |

### 快速开始

#### 前置要求

- Python 3.10+
- Node.js 14.18+
- [Poetry](https://python-poetry.org/)（`pip install --upgrade poetry`）
- 至少一个 LLM API 密钥（OpenAI、Anthropic 或 Google Gemini）

#### 后端

```bash
cd backend

# 配置 API 密钥
echo "OPENAI_API_KEY=sk-your-key" > .env
echo "ANTHROPIC_API_KEY=your-key" >> .env
echo "GEMINI_API_KEY=your-key" >> .env

# 安装依赖
poetry install
poetry run playwright install chromium

# 启动服务
poetry run uvicorn main:app --reload --port 7001
```

#### 前端

```bash
cd frontend
npm install
npm run dev
```

在浏览器中打开 http://localhost:5173。

#### Docker

```bash
echo "OPENAI_API_KEY=sk-your-key" > .env
docker-compose up -d --build
```

访问 http://localhost:5173。

### 环境变量

#### 后端（`backend/.env`）

| 变量 | 是否必需 | 说明 |
|------|---------|------|
| `OPENAI_API_KEY` | 至少配置一个密钥 | OpenAI 或 OpenRouter API 密钥 |
| `ANTHROPIC_API_KEY` | 至少配置一个密钥 | Anthropic API 密钥 |
| `GEMINI_API_KEY` | 至少配置一个密钥 | Google Gemini API 密钥 |
| `OPENAI_BASE_URL` | 否 | 自定义 API 地址（如 OpenRouter：`https://openrouter.ai/api/v1`） |
| `REPLICATE_API_KEY` | 否 | 用于 Flux Schnell 图片生成 |

#### 前端（`frontend/.env.local`）

| 变量 | 是否必需 | 默认值 | 说明 |
|------|---------|--------|------|
| `VITE_WS_BACKEND_URL` | 否 | `ws://127.0.0.1:7001` | WebSocket 后端地址 |
| `VITE_HTTP_BACKEND_URL` | 否 | `http://127.0.0.1:7001` | HTTP 后端地址 |

### 与 screenshot-to-code 的区别

| | screenshot-to-code | url-to-code |
|---|---|---|
| 主要输入方式 | 上传截图 | 输入 URL |
| 截图引擎 | ScreenshotOne（外部 API） | Playwright（本地） |
| 外部 API 密钥 | 需要 ScreenshotOne 密钥 | 不需要 |
| DOM 上下文 | 无 | 提取并传递给 LLM |
| UI 设计 | 标签页式 | URL 优先 |
| 费用 | LLM + ScreenshotOne API | 仅 LLM API |

### 许可证

MIT 许可证 — 详见 [LICENSE](LICENSE)。

基于 [Abi Raja](https://github.com/abi) 的 [screenshot-to-code](https://github.com/abi/screenshot-to-code)。
