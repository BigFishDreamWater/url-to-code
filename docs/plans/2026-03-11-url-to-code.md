# url-to-code Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fork screenshot-to-code, replace ScreenshotOne with Playwright for URL screenshots, add DOM extraction, redesign UI with URL-first input, and configure OpenRouter + Kimi 2.5 for testing.

**Architecture:** Backend adds Playwright screenshot service + DOM extractor. Frontend redesigns input area with URL as primary entry. Prompt pipeline enhanced with DOM context. All existing features preserved.

**Tech Stack:** Python/FastAPI, Playwright, React/Vite/Tailwind, OpenRouter API (Kimi 2.5)

---

## Phase 1: Project Setup

### Task 1: Fork and Initialize Project

**Files:**
- Copy: `/home/moxia/code/screenshot-to-code/` → `/home/moxia/code/url-to-code/`
- Modify: `backend/pyproject.toml`
- Create: `backend/.env`
- Create: `.gitignore`

**Step 1: Copy the project**

```bash
cp -r /home/moxia/code/screenshot-to-code/* /home/moxia/code/url-to-code/
cp /home/moxia/code/screenshot-to-code/.gitignore /home/moxia/code/url-to-code/ 2>/dev/null || true
```

**Step 2: Initialize git repo**

```bash
cd /home/moxia/code/url-to-code
git init
```

**Step 3: Add Playwright dependency to pyproject.toml**

In `backend/pyproject.toml`, add under `[tool.poetry.dependencies]`:
```toml
playwright = "^1.49.0"
```

**Step 4: Create backend/.env**

```env
OPENAI_API_KEY=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
OPENAI_BASE_URL=https://openrouter.ai/api/v1
IS_DEBUG_ENABLED=true
```

**Step 5: Install dependencies**

```bash
cd /home/moxia/code/url-to-code/backend
poetry install
poetry run playwright install chromium
```

**Step 6: Commit**

```bash
git add -A
git commit -m "chore: fork screenshot-to-code as url-to-code base"
```

---

## Phase 2: Backend — Playwright Screenshot + DOM Extraction

### Task 2: Create Playwright Screenshot Service

**Files:**
- Create: `backend/screenshot/playwright_service.py`
- Create: `backend/screenshot/__init__.py`

**Step 1: Create the screenshot module**

Create `backend/screenshot/__init__.py` (empty).

Create `backend/screenshot/playwright_service.py`:

```python
import base64
from playwright.async_api import async_playwright

# DOM extraction JS — injected into page to extract simplified DOM tree
EXTRACT_DOM_JS = """
() => {
    function extractDOM(el, depth = 0, maxDepth = 6) {
        if (depth > maxDepth) return null;
        const tag = el.tagName?.toLowerCase();
        if (!tag) return null;
        const skip = ['script','style','noscript','svg','path','link','meta'];
        if (skip.includes(tag)) return null;
        const rect = el.getBoundingClientRect();
        if (rect.width === 0 && rect.height === 0) return null;
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden') return null;

        const cls = el.className && typeof el.className === 'string'
            ? el.className.trim().substring(0, 100) : '';
        const text = el.childNodes.length === 1
            && el.childNodes[0].nodeType === 3
            ? el.childNodes[0].textContent?.trim().substring(0, 80) || '' : '';

        const children = [];
        for (const child of el.children) {
            const c = extractDOM(child, depth + 1, maxDepth);
            if (c) children.push(c);
        }
        const node = { tag };
        if (cls) node.class = cls;
        if (text) node.text = text;
        if (children.length) node.children = children;
        return node;
    }
    return JSON.stringify(extractDOM(document.body), null, 2);
}
"""


async def capture_screenshot_and_dom(
    url: str,
    viewport_width: int = 1280,
    viewport_height: int = 800,
) -> dict:
    """
    Use Playwright to capture a screenshot and extract simplified DOM.
    Returns { "screenshot": base64_data_url, "dom": simplified_dom_string }
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height},
            device_scale_factor=1,
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
        except Exception:
            # Fallback: if networkidle times out, try domcontentloaded
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # Wait a bit for any animations/lazy loading
        await page.wait_for_timeout(1000)

        # Take screenshot
        screenshot_bytes = await page.screenshot(full_page=False, type="png")
        base64_image = base64.b64encode(screenshot_bytes).decode("utf-8")
        data_url = f"data:image/png;base64,{base64_image}"

        # Extract DOM
        dom_json = await page.evaluate(EXTRACT_DOM_JS)

        await browser.close()

        return {
            "screenshot": data_url,
            "dom": dom_json or "",
        }
```

**Step 2: Commit**

```bash
git add backend/screenshot/
git commit -m "feat: add Playwright screenshot + DOM extraction service"
```

---

### Task 3: Replace Screenshot Route

**Files:**
- Modify: `backend/routes/screenshot.py`

**Step 1: Rewrite screenshot.py to use Playwright**

Replace the entire file `backend/routes/screenshot.py`:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from urllib.parse import urlparse
from screenshot.playwright_service import capture_screenshot_and_dom

router = APIRouter()


def normalize_url(url: str) -> str:
    url = url.strip()
    parsed = urlparse(url)
    if not parsed.scheme:
        url = f"https://{url}"
    elif parsed.scheme in ['http', 'https']:
        pass
    else:
        if ':' in url and not url.startswith(
            ('http://', 'https://', 'ftp://', 'file://')
        ):
            url = f"https://{url}"
        else:
            raise ValueError(f"Unsupported protocol: {parsed.scheme}")
    return url


class ScreenshotRequest(BaseModel):
    url: str


class ScreenshotResponse(BaseModel):
    url: str
    dom: str


@router.post("/api/screenshot")
async def app_screenshot(request: ScreenshotRequest):
    url = request.url
    try:
        normalized_url = normalize_url(url)
        result = await capture_screenshot_and_dom(normalized_url)
        return ScreenshotResponse(
            url=result["screenshot"],
            dom=result["dom"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error capturing screenshot: {str(e)}",
        )
```

Key changes:
- Removed `apiKey` from `ScreenshotRequest` (no longer needed)
- Added `dom` field to `ScreenshotResponse`
- Calls `capture_screenshot_and_dom()` instead of ScreenshotOne API
- Removed `bytes_to_data_url` and `capture_screenshot` functions

**Step 2: Commit**

```bash
git add backend/routes/screenshot.py
git commit -m "feat: replace ScreenshotOne with Playwright in screenshot route"
```

---

## Phase 3: Backend — Prompt Enhancement with DOM

### Task 4: Add DOM Context to Image Prompts

**Files:**
- Modify: `backend/prompts/prompt_types.py:4-9` — add `dom` field to `UserTurnInput`
- Modify: `backend/prompts/create/image.py` — append DOM context
- Modify: `backend/prompts/create/__init__.py` — pass DOM through
- Modify: `backend/prompts/pipeline.py` — pass DOM through

**Step 1: Add `dom` field to UserTurnInput**

In `backend/prompts/prompt_types.py`, change `UserTurnInput`:

```python
class UserTurnInput(TypedDict):
    """Normalized current user turn payload from the request."""
    text: str
    images: List[str]
    videos: List[str]
    dom: str  # Simplified DOM structure from URL screenshot
```

**Step 2: Update image prompt builder**

In `backend/prompts/create/image.py`, modify `build_image_prompt_messages` to accept and use DOM:

```python
def build_image_prompt_messages(
    image_data_urls: list[str],
    stack: Stack,
    text_prompt: str,
    image_generation_enabled: bool,
    dom_context: str = "",
) -> list[ChatCompletionMessageParam]:
```

After the existing `user_prompt` string, before `if text_prompt.strip():`, add:

```python
    if dom_context.strip():
        user_prompt += f"""

## Page DOM Structure (for reference)

The following is a simplified DOM structure of the original page. Use it to better understand
the layout, class names, and text content:

{dom_context}
"""
```

**Step 3: Update create/__init__.py to pass DOM**

In `backend/prompts/create/__init__.py`, modify `build_create_prompt_from_input`:

```python
def build_create_prompt_from_input(
    input_mode: InputMode,
    stack: Stack,
    prompt: UserTurnInput,
    image_generation_enabled: bool,
) -> Prompt:
    if input_mode == "image":
        image_urls = prompt.get("images", [])
        text_prompt = prompt.get("text", "")
        dom_context = prompt.get("dom", "")
        return build_image_prompt_messages(
            image_data_urls=image_urls,
            stack=stack,
            text_prompt=text_prompt,
            image_generation_enabled=image_generation_enabled,
            dom_context=dom_context,
        )
    # ... rest unchanged
```

**Step 4: Update request_parsing.py to parse DOM**

In `backend/prompts/request_parsing.py`, modify `parse_prompt_content`:

```python
def parse_prompt_content(raw_prompt: object) -> UserTurnInput:
    if not isinstance(raw_prompt, dict):
        return {"text": "", "images": [], "videos": [], "dom": ""}

    prompt_dict = cast(dict[str, object], raw_prompt)
    text = prompt_dict.get("text")
    dom = prompt_dict.get("dom")
    return {
        "text": text if isinstance(text, str) else "",
        "images": _to_string_list(prompt_dict.get("images")),
        "videos": _to_string_list(prompt_dict.get("videos")),
        "dom": dom if isinstance(dom, str) else "",
    }
```

**Step 5: Commit**

```bash
git add backend/prompts/
git commit -m "feat: add DOM context to image prompt for better code generation"
```

---

## Phase 4: Frontend — URL-First Input Redesign

### Task 5: Redesign UnifiedInputPane with URL-First Layout

**Files:**
- Modify: `frontend/src/components/unified-input/UnifiedInputPane.tsx`
- Modify: `frontend/src/components/unified-input/tabs/UrlTab.tsx`
- Modify: `frontend/src/components/start-pane/StartPane.tsx`

**Step 1: Rewrite UrlTab.tsx — remove ScreenshotOne dependency**

Replace `frontend/src/components/unified-input/tabs/UrlTab.tsx`. Key changes:
- Remove `screenshotOneApiKey` prop
- Add `dom` to the response handling — pass DOM data alongside screenshot
- Remove ScreenshotOne API key validation
- Update loading text to "正在访问页面..."
- Remove "Requires ScreenshotOne API key" footer text

```tsx
import { useState } from "react";
import { HTTP_BACKEND_URL } from "../../../config";
import { Button } from "../../ui/button";
import { Input } from "../../ui/input";
import { toast } from "react-hot-toast";
import OutputSettingsSection from "../../settings/OutputSettingsSection";
import { Stack } from "../../../lib/stacks";

interface Props {
  doCreate: (
    urls: string[],
    inputMode: "image" | "video",
    textPrompt?: string,
    dom?: string,
  ) => void;
  stack: Stack;
  setStack: (stack: Stack) => void;
}

function isFigmaUrl(url: string): boolean {
  return /^https?:\/\/([\w.-]*\.)?figma\.com\//i.test(url.trim());
}

function UrlTab({ doCreate, stack, setStack }: Props) {
  const [isLoading, setIsLoading] = useState(false);
  const [referenceUrl, setReferenceUrl] = useState("");

  async function takeScreenshot() {
    const trimmedUrl = referenceUrl.trim();

    if (!trimmedUrl) {
      toast.error("Please enter a URL");
      return;
    }

    if (trimmedUrl.toLowerCase().startsWith("file://")) {
      toast.error(
        "file:// URLs are not supported. Use the Upload tab for local files.",
      );
      return;
    }

    if (isFigmaUrl(trimmedUrl)) {
      toast.error(
        "Figma URLs are not supported. Export as images and use Upload tab.",
        { duration: 6000 },
      );
      return;
    }

    try {
      setIsLoading(true);
      const response = await fetch(`${HTTP_BACKEND_URL}/api/screenshot`, {
        method: "POST",
        body: JSON.stringify({ url: trimmedUrl }),
        headers: { "Content-Type": "application/json" },
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to capture screenshot");
      }

      const res = await response.json();
      doCreate([res.url], "image", "", res.dom || "");
    } catch (error) {
      console.error(error);
      toast.error(
        error instanceof Error ? error.message : "Failed to capture screenshot",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="w-full space-y-3">
      <div className="flex gap-2">
        <Input
          placeholder="输入网址，如 https://example.com"
          onChange={(e) => setReferenceUrl(e.target.value)}
          value={referenceUrl}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !isLoading) takeScreenshot();
          }}
          className="flex-1"
          data-testid="url-input"
        />
        <Button
          onClick={takeScreenshot}
          disabled={isLoading}
          size="lg"
          data-testid="url-capture"
        >
          {isLoading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"
                fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle className="opacity-25" cx="12" cy="12" r="10"
                  stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              访问中...
            </span>
          ) : "生成代码"}
        </Button>
      </div>
      {isFigmaUrl(referenceUrl) && (
        <p className="text-xs text-amber-600 dark:text-amber-400">
          Figma URLs are not supported. Export as images and use Upload tab.
        </p>
      )}
      <OutputSettingsSection stack={stack} setStack={setStack} />
    </div>
  );
}

export default UrlTab;
```

**Step 2: Rewrite UnifiedInputPane.tsx — URL input on top**

Replace `frontend/src/components/unified-input/UnifiedInputPane.tsx`.
Key changes:
- URL input is always visible at the top (not inside a tab)
- Tabs below for Upload, Text, Video (removed URL tab from tabs)
- Add Import tab
- Divider "── 或者 ──" between URL and tabs
- Remove `screenshotOneApiKey` prop passing

```tsx
import React, { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { Stack } from "../../lib/stacks";
import { Settings } from "../../types";
import UploadTab from "./tabs/UploadTab";
import UrlTab from "./tabs/UrlTab";
import TextTab from "./tabs/TextTab";
import ImportTab from "./tabs/ImportTab";

interface Props {
  doCreate: (
    images: string[],
    inputMode: "image" | "video",
    textPrompt?: string,
    dom?: string,
  ) => void;
  doCreateFromText: (text: string) => void;
  importFromCode: (code: string, stack: Stack) => void;
  settings: Settings;
  setSettings: React.Dispatch<React.SetStateAction<Settings>>;
}

type InputTab = "upload" | "text" | "import";

function UnifiedInputPane({
  doCreate,
  doCreateFromText,
  importFromCode,
  settings,
  setSettings,
}: Props) {
  const [activeTab, setActiveTab] = useState<InputTab>("upload");

  function setStack(stack: Stack) {
    setSettings((prev: Settings) => ({
      ...prev,
      generatedCodeConfig: stack,
    }));
  }

  return (
    <div className="w-full max-w-2xl mx-auto px-4">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          url-to-code
        </h1>
        <p className="text-gray-500 dark:text-zinc-400">
          输入网址或上传截图，生成前端代码
        </p>
      </div>

      {/* URL Input — always visible, primary entry */}
      <div className="mb-6">
        <UrlTab
          doCreate={doCreate}
          stack={settings.generatedCodeConfig}
          setStack={setStack}
        />
      </div>

      {/* Divider */}
      <div className="flex items-center gap-4 mb-6">
        <div className="flex-1 border-t border-gray-200 dark:border-zinc-700" />
        <span className="text-sm text-gray-400 dark:text-zinc-500">或者</span>
        <div className="flex-1 border-t border-gray-200 dark:border-zinc-700" />
      </div>

      {/* Secondary input tabs */}
      <Tabs
        value={activeTab}
        onValueChange={(v) => setActiveTab(v as InputTab)}
        className="w-full"
      >
        <TabsList className="grid w-full grid-cols-3 mb-6">
          <TabsTrigger value="upload" data-testid="tab-upload">
            Upload
          </TabsTrigger>
          <TabsTrigger value="text" data-testid="tab-text">
            Text
          </TabsTrigger>
          <TabsTrigger value="import" data-testid="tab-import">
            Import
          </TabsTrigger>
        </TabsList>

        <TabsContent value="upload" className="mt-0">
          <UploadTab
            doCreate={doCreate}
            stack={settings.generatedCodeConfig}
            setStack={setStack}
          />
        </TabsContent>

        <TabsContent value="text" className="mt-0">
          <TextTab
            doCreateFromText={doCreateFromText}
            stack={settings.generatedCodeConfig}
            setStack={setStack}
          />
        </TabsContent>

        <TabsContent value="import" className="mt-0">
          <ImportTab importFromCode={importFromCode} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default UnifiedInputPane;
```

**Step 3: Commit**

```bash
git add frontend/src/components/
git commit -m "feat: redesign input UI with URL-first layout"
```

---

### Task 6: Wire DOM Data Through Frontend → Backend

**Files:**
- Modify: `frontend/src/App.tsx:460-510` — update `doCreate` to accept and pass `dom`
- Modify: `frontend/src/components/start-pane/StartPane.tsx` — update `doCreate` prop type
- Modify: `frontend/src/types.ts` — remove `screenshotOneApiKey` from Settings

**Step 1: Update doCreate in App.tsx**

In `frontend/src/App.tsx`, modify the `doCreate` function signature (line ~460):

```typescript
function doCreate(
  referenceImages: string[],
  inputMode: "image" | "video",
  textPrompt: string = "",
  dom: string = "",
) {
```

In the `doGenerateCode` call inside `doCreate` (line ~499), add `dom` to the prompt:

```typescript
doGenerateCode({
  generationType: "create",
  inputMode,
  prompt: {
    text: textPrompt,
    images: inputMode === "image" ? media : [],
    videos: inputMode === "video" ? media : [],
    dom,
  },
  variantHistory,
});
```

**Step 2: Update StartPane.tsx prop type**

In `frontend/src/components/start-pane/StartPane.tsx`, update the `doCreate` type:

```typescript
doCreate: (
  images: string[],
  inputMode: "image" | "video",
  textPrompt?: string,
  dom?: string,
) => void;
```

**Step 3: Remove screenshotOneApiKey from Settings**

In `frontend/src/types.ts`, remove `screenshotOneApiKey` from the `Settings` interface.

In `frontend/src/App.tsx`, remove `screenshotOneApiKey: null` from the default settings (line ~88).

**Step 4: Commit**

```bash
git add frontend/src/
git commit -m "feat: wire DOM data from URL screenshot through to code generation"
```

---

## Phase 5: LLM Configuration

### Task 7: Add Kimi 2.5 Model via OpenRouter

**Files:**
- Modify: `backend/llm.py` — add Kimi model
- Modify: `frontend/src/lib/models.ts` — add Kimi to frontend model list

**Step 1: Add Kimi model to backend**

In `backend/llm.py`, add to the `Llm` enum:

```python
# Kimi (via OpenRouter)
KIMI_K2 = "moonshotai/kimi-k2"
```

Add to `MODEL_PROVIDER`:

```python
Llm.KIMI_K2: "openai",  # OpenRouter uses OpenAI-compatible API
```

Add to `OPENAI_MODEL_CONFIG`:

```python
Llm.KIMI_K2: {"api_name": "moonshotai/kimi-k2"},
```

**Step 2: Add Kimi to frontend model list**

Find the frontend models file and add Kimi 2.5 as an option.
The exact file path needs to be checked — likely `frontend/src/lib/models.ts`.

**Step 3: Commit**

```bash
git add backend/llm.py frontend/src/lib/
git commit -m "feat: add Kimi 2.5 model via OpenRouter"
```

---

## Phase 6: Branding & Cleanup

### Task 8: Update Branding

**Files:**
- Modify: `frontend/index.html` — update title
- Modify: `frontend/src/components/sidebar/IconStrip.tsx` — update logo/name if present
- Modify: `frontend/package.json` — update project name

**Step 1: Update page title**

In `frontend/index.html`, change `<title>` to `url-to-code`.

**Step 2: Update package.json name**

In `frontend/package.json`, change `"name"` to `"url-to-code"`.

**Step 3: Remove ScreenshotOne references from Settings UI**

Find and remove any ScreenshotOne API key input fields in the settings component.
Likely in `frontend/src/components/settings/SettingsTab.tsx`.

**Step 4: Commit**

```bash
git add frontend/
git commit -m "chore: update branding to url-to-code, remove ScreenshotOne references"
```

---

## Phase 7: Verification

### Task 9: End-to-End Verification

**Step 1: Start backend**

```bash
cd /home/moxia/code/url-to-code/backend
poetry run uvicorn main:app --port 7001 --reload
```

**Step 2: Start frontend**

```bash
cd /home/moxia/code/url-to-code/frontend
npm run dev
```

**Step 3: Test URL-to-code flow**

1. Open http://localhost:5173
2. Enter a URL (e.g., `https://example.com`) in the top input
3. Click "生成代码"
4. Verify: screenshot is captured, DOM is extracted, code is generated

**Step 4: Test image upload flow**

1. Switch to Upload tab
2. Upload a screenshot image
3. Verify code generation works as before

**Step 5: Final commit**

```bash
git add -A
git commit -m "chore: url-to-code v0.1 ready"
```

---

## Summary of All Files Changed

| File | Action | Description |
|------|--------|-------------|
| `backend/screenshot/__init__.py` | Create | Empty module init |
| `backend/screenshot/playwright_service.py` | Create | Playwright screenshot + DOM extraction |
| `backend/routes/screenshot.py` | Rewrite | Use Playwright, return DOM, remove API key |
| `backend/pyproject.toml` | Modify | Add playwright dependency |
| `backend/.env` | Create | OpenRouter API key + base URL |
| `backend/llm.py` | Modify | Add Kimi 2.5 model |
| `backend/prompts/prompt_types.py` | Modify | Add `dom` to UserTurnInput |
| `backend/prompts/create/image.py` | Modify | Append DOM context to prompt |
| `backend/prompts/create/__init__.py` | Modify | Pass DOM through |
| `backend/prompts/request_parsing.py` | Modify | Parse DOM from request |
| `frontend/src/components/unified-input/UnifiedInputPane.tsx` | Rewrite | URL-first layout |
| `frontend/src/components/unified-input/tabs/UrlTab.tsx` | Rewrite | Remove ScreenshotOne, use Playwright |
| `frontend/src/components/start-pane/StartPane.tsx` | Modify | Update doCreate prop type |
| `frontend/src/App.tsx` | Modify | Pass DOM through doCreate |
| `frontend/src/types.ts` | Modify | Remove screenshotOneApiKey |
| `frontend/index.html` | Modify | Update title |
| `frontend/package.json` | Modify | Update project name |
