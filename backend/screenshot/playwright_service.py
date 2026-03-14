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


# Image extraction JS — collect all visible image URLs from the page
EXTRACT_IMAGES_JS = """
() => {
    const images = [];
    const seen = new Set();

    // Collect <img> elements
    document.querySelectorAll('img').forEach(img => {
        const src = img.src || img.getAttribute('data-src') || '';
        if (!src || src.startsWith('data:') || seen.has(src)) return;
        const rect = img.getBoundingClientRect();
        if (rect.width < 10 || rect.height < 10) return;
        seen.add(src);
        images.push({
            src: src,
            alt: (img.alt || '').substring(0, 100),
            width: Math.round(rect.width),
            height: Math.round(rect.height),
        });
    });

    // Collect CSS background images
    document.querySelectorAll('*').forEach(el => {
        const bg = window.getComputedStyle(el).backgroundImage;
        if (!bg || bg === 'none') return;
        const match = bg.match(/url\\(["']?(https?:\\/\\/[^"')]+)["']?\\)/);
        if (!match) return;
        const src = match[1];
        if (seen.has(src)) return;
        const rect = el.getBoundingClientRect();
        if (rect.width < 10 || rect.height < 10) return;
        seen.add(src);
        images.push({
            src: src,
            alt: '',
            width: Math.round(rect.width),
            height: Math.round(rect.height),
        });
    });

    return JSON.stringify(images);
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
            await page.goto(url, wait_until="networkidle", timeout=60000)
        except Exception:
            try:
                # Fallback: if networkidle times out, try domcontentloaded
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            except Exception:
                # Last resort: just load whatever we can
                await page.goto(url, wait_until="commit", timeout=60000)
                await page.wait_for_timeout(3000)

        # Wait a bit for any animations/lazy loading
        await page.wait_for_timeout(1000)

        # Scroll to bottom to trigger lazy-loaded images, then back to top
        await page.evaluate("""
            async () => {
                const delay = ms => new Promise(r => setTimeout(r, ms));
                const height = () => document.body.scrollHeight;
                let prev = 0;
                while (prev !== height()) {
                    prev = height();
                    window.scrollTo(0, prev);
                    await delay(300);
                }
                window.scrollTo(0, 0);
            }
        """)
        await page.wait_for_timeout(500)

        # Take screenshot
        screenshot_bytes = await page.screenshot(full_page=True, type="png")
        base64_image = base64.b64encode(screenshot_bytes).decode("utf-8")
        data_url = f"data:image/png;base64,{base64_image}"

        # Extract DOM
        dom_json = await page.evaluate(EXTRACT_DOM_JS)

        # Extract images
        images_json = await page.evaluate(EXTRACT_IMAGES_JS)

        await browser.close()

        return {
            "screenshot": data_url,
            "dom": dom_json or "",
            "images": images_json or "[]",
        }
