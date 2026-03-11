# url-to-code 设计文档

## 项目概述

基于 screenshot-to-code（Fork 后改造），开发 url-to-code 开源项目。用户输入网址即可生成对应前端代码，同时保留图片上传等原有功能。

## 核心决策

| 决策项 | 选择 |
|--------|------|
| 项目关系 | Fork screenshot-to-code 后改造 |
| 截图方案 | 后端 Playwright（替代 ScreenshotOne） |
| UI 改造 | 中等改造，URL 优先入口 |
| 截图增强 | 截图 + DOM 提取 |
| 功能裁剪 | 全部保留，只做加法 |
| 测试 LLM | OpenRouter + Kimi 2.5 |

## 架构改动

### 1. 后端：Playwright 截图服务

新增 `backend/screenshot/playwright_service.py`，替代 ScreenshotOne API。

**流程：**
```
POST /api/screenshot { url }
  → Playwright 启动无头 Chromium
  → 导航到目标 URL，等待 networkidle
  → 截取可见区域截图 → base64 data URL
  → 注入 JS 提取简化 DOM
  → 返回 { url: dataUrl, dom: simplifiedDom }
```

**DOM 提取策略：**
- 提取每个可见元素的：标签名、class 列表、文本内容（截断）、位置/尺寸
- 过滤不可见元素、script、style 标签
- 输出简洁树形结构，控制在 2000-4000 tokens

### 2. 前端：URL 优先入口

```
┌─────────────────────────────────────────────┐
│  url-to-code                    [设置按钮]    │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────────────────────┐ ┌────────┐ │
│  │ 输入网址，如 https://...     │ │ 生成   │ │
│  └─────────────────────────────┘ └────────┘ │
│                                             │
│  ── 或者 ──                                  │
│                                             │
│  [图片上传] [文本描述] [视频] [导入代码]       │
│  ┌─────────────────────────────────────────┐ │
│  │  拖拽上传图片 / 对应 Tab 内容             │ │
│  └─────────────────────────────────────────┘ │
│                                             │
│  输出格式: [HTML+Tailwind ▾]  模型: [Kimi ▾] │
└─────────────────────────────────────────────┘
```

**关键交互：**
- URL 输入框始终可见，是页面最突出的元素
- 输入 URL 后点击"生成"，后端截图 + DOM 提取，自动进入代码生成
- 截图过程中显示 loading 状态
- 下方 Tab 保留原有图片上传、文本、视频、导入功能
- 移除所有 ScreenshotOne API key 相关 UI

**品牌改动：**
- 项目名：url-to-code
- 页面标题和 Logo 更新
- 描述文案："输入网址或上传截图，生成前端代码"

### 3. Prompt 增强

代码生成时的 Prompt 结构：
```
System Prompt（现有的，按 stack 选择）
  ↓
User Message:
  ├─ 截图图片（base64）
  ├─ [新增] DOM 结构信息
  └─ 用户额外指令（如果有）
```

### 4. 数据流变化

```
现有：URL → ScreenshotOne API → 截图 → WebSocket → LLM → 代码
新增：URL → Playwright → { 截图 + DOM } → WebSocket → LLM（截图+DOM） → 代码
```

**具体改动文件：**
- `routes/screenshot.py` — 返回值增加 dom 字段
- 新增 `screenshot/playwright_service.py` — Playwright 截图 + DOM 提取
- 前端 `UrlTab.tsx` — 移除 API key，接收 DOM 数据
- `prompts/create/` — image prompt 后追加 DOM context
- `routes/generate_code.py` 的 `PromptCreationMiddleware` — 处理 DOM 参数

### 5. LLM 配置（测试用）

通过 OpenRouter 使用 Kimi 2.5：
- `OPENAI_BASE_URL=https://openrouter.ai/api/v1`
- `OPENAI_API_KEY` 存在 `.env` 中
- 模型名：`moonshotai/kimi-k2`

## 不变的部分

- Agent 系统、LLM Provider 架构
- WebSocket 通信协议
- 代码生成/编辑/历史管理
- 状态管理（Zustand stores）
- 所有现有功能（Video、图片生成、Evals 等）
- 所有其他输入方式（图片、文本、视频、导入）
