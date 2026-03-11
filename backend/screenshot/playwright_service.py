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
