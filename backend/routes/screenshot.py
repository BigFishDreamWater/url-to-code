from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from urllib.parse import urlparse
from screenshot.playwright_service import capture_screenshot_and_dom

router = APIRouter()


def normalize_url(url: str) -> str:
    """
    Normalize URL to ensure it has a proper protocol.
    If no protocol is specified, default to https://
    """
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
