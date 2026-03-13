"""WebSocket routes for backend code generation (Stage 2 & Stage 3)."""

import json
import traceback
from typing import Any, Dict, Optional, cast

from fastapi import APIRouter, WebSocket
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

from config import (
    ANTHROPIC_API_KEY,
    GEMINI_API_KEY,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
)
from llm import Llm, OPENAI_MODELS, ANTHROPIC_MODELS, GEMINI_MODELS
from prompts.backend_gen.api_doc import build_api_doc_prompt
from prompts.backend_gen.backend_code import build_backend_code_prompt
from agent.backend_engine import BackendEngine
from ws.constants import APP_ERROR_WEB_SOCKET_CODE

router = APIRouter()


def _pick_model() -> Llm:
    """Pick the best available model for backend generation."""
    if ANTHROPIC_API_KEY:
        return Llm.CLAUDE_SONNET_4_6
    if OPENAI_API_KEY:
        return Llm.GPT_4_1_2025_04_14
    if GEMINI_API_KEY:
        return Llm.GEMINI_3_FLASH_PREVIEW_HIGH
    raise Exception("No API key available")


async def _send_json(ws: WebSocket, data: Dict[str, Any]) -> None:
    try:
        await ws.send_json(data)
    except (ConnectionClosedOK, ConnectionClosedError):
        pass


@router.websocket("/generate-api-doc")
async def generate_api_doc(websocket: WebSocket) -> None:
    """Stage 2: Analyze frontend code and generate API documentation."""
    await websocket.accept()
    try:
        params = await websocket.receive_json()
        frontend_code: str = params.get("frontendCode", "")

        if not frontend_code.strip():
            await _send_json(websocket, {"type": "error", "value": "No frontend code provided"})
            await websocket.close(APP_ERROR_WEB_SOCKET_CODE)
            return

        await _send_json(websocket, {"type": "status", "value": "Analyzing frontend code..."})

        model = _pick_model()
        prompt_messages = build_api_doc_prompt(frontend_code)

        # Use a simple streaming call (no tool-calling needed for JSON output)
        from agent.providers.factory import create_provider_session

        session = create_provider_session(
            model=model,
            prompt_messages=prompt_messages,
            should_generate_images=False,
            openai_api_key=OPENAI_API_KEY,
            openai_base_url=OPENAI_BASE_URL,
            anthropic_api_key=ANTHROPIC_API_KEY,
            gemini_api_key=GEMINI_API_KEY,
            custom_tools=[],  # No tools needed
        )

        full_text = ""
        try:
            from agent.providers.base import StreamEvent

            async def on_event(event: StreamEvent) -> None:
                nonlocal full_text
                if event.type == "assistant_delta" and event.text:
                    full_text += event.text
                    await _send_json(websocket, {
                        "type": "chunk",
                        "value": event.text,
                    })

            turn = await session.stream_turn(on_event)
            if turn.assistant_text:
                full_text = turn.assistant_text
        finally:
            await session.close()

        # Parse the JSON response
        # Strip markdown fences if present
        cleaned = full_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first and last lines (``` markers)
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines)

        try:
            api_doc = json.loads(cleaned)
        except json.JSONDecodeError:
            await _send_json(websocket, {
                "type": "error",
                "value": "Failed to parse API documentation. Please retry.",
            })
            await websocket.close(APP_ERROR_WEB_SOCKET_CODE)
            return

        await _send_json(websocket, {
            "type": "apiDoc",
            "value": json.dumps(api_doc, ensure_ascii=False),
        })
        await _send_json(websocket, {"type": "complete"})

    except Exception as e:
        print(f"[GENERATE_API_DOC] Error: {e}")
        traceback.print_exc()
        await _send_json(websocket, {"type": "error", "value": str(e)})
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


@router.websocket("/generate-backend")
async def generate_backend(websocket: WebSocket) -> None:
    """Stage 3: Generate backend code from API documentation."""
    await websocket.accept()
    try:
        params = await websocket.receive_json()
        api_doc_json: str = params.get("apiDoc", "")
        language: str = params.get("language", "python")

        if not api_doc_json.strip():
            await _send_json(websocket, {"type": "error", "value": "No API doc provided"})
            await websocket.close(APP_ERROR_WEB_SOCKET_CODE)
            return

        if language not in ("python", "php", "java"):
            language = "python"

        await _send_json(websocket, {
            "type": "status",
            "value": f"Generating {language} backend code...",
            "variantIndex": 0,
        })

        model = _pick_model()
        prompt_messages = build_backend_code_prompt(api_doc_json, language)

        async def send_message(
            msg_type: str,
            value: Optional[str],
            variant_index: int,
            data: Optional[Dict[str, Any]] = None,
            event_id: Optional[str] = None,
        ) -> None:
            payload: Dict[str, Any] = {"type": msg_type, "variantIndex": variant_index}
            if value is not None:
                payload["value"] = value
            if data is not None:
                payload["data"] = data
            if event_id is not None:
                payload["eventId"] = event_id
            await _send_json(websocket, payload)

        engine = BackendEngine(
            send_message=send_message,
            variant_index=0,
            openai_api_key=OPENAI_API_KEY,
            openai_base_url=OPENAI_BASE_URL,
            anthropic_api_key=ANTHROPIC_API_KEY,
            gemini_api_key=GEMINI_API_KEY,
        )

        files = await engine.run(model, prompt_messages)

        # Send all files as final result
        await _send_json(websocket, {
            "type": "backendFiles",
            "value": json.dumps(files, ensure_ascii=False),
        })
        await _send_json(websocket, {"type": "complete"})

    except Exception as e:
        print(f"[GENERATE_BACKEND] Error: {e}")
        traceback.print_exc()
        await _send_json(websocket, {"type": "error", "value": str(e)})
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
