"""Engine for backend code generation with multi-file support."""

import asyncio
import uuid
from typing import Any, Awaitable, Callable, Dict, List, Optional

from openai.types.chat import ChatCompletionMessageParam

from llm import Llm
from agent.providers.base import ExecutedToolCall, StreamEvent
from agent.providers.factory import create_provider_session
from agent.state import AgentFileState
from agent.tools import extract_content_from_args, extract_path_from_args, summarize_text
from agent.tools.backend_definitions import backend_tool_definitions
from agent.tools.backend_runtime import BackendToolRuntime
from agent.tools.types import ToolCall


class BackendEngine:
    """Agent engine for backend code generation. Supports multi-file output."""

    def __init__(
        self,
        send_message: Callable[
            [str, Optional[str], int, Optional[Dict[str, Any]], Optional[str]],
            Awaitable[None],
        ],
        variant_index: int,
        openai_api_key: Optional[str],
        openai_base_url: Optional[str],
        anthropic_api_key: Optional[str],
        gemini_api_key: Optional[str],
    ):
        self.send_message = send_message
        self.variant_index = variant_index
        self.openai_api_key = openai_api_key
        self.openai_base_url = openai_base_url
        self.anthropic_api_key = anthropic_api_key
        self.gemini_api_key = gemini_api_key

        self.file_state = AgentFileState()
        self.file_state.files = {}
        self.tool_runtime = BackendToolRuntime(file_state=self.file_state)

    def _next_event_id(self, prefix: str) -> str:
        return f"{prefix}-{self.variant_index}-{uuid.uuid4().hex[:8]}"

    async def _send(
        self,
        msg_type: str,
        value: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        event_id: Optional[str] = None,
    ) -> None:
        await self.send_message(msg_type, value, self.variant_index, data, event_id)

    async def _handle_streamed_tool_delta(
        self,
        event: StreamEvent,
        started_tool_ids: set[str],
        streamed_lengths: Dict[str, int],
    ) -> None:
        if event.type != "tool_call_delta":
            return
        if event.tool_name != "create_file":
            return
        if not event.tool_call_id:
            return

        content = extract_content_from_args(event.tool_arguments)
        path = extract_path_from_args(event.tool_arguments) or ""
        if content is None:
            return

        tool_event_id = event.tool_call_id
        if tool_event_id not in started_tool_ids:
            await self._send(
                "toolStart",
                data={
                    "name": "create_file",
                    "input": {
                        "path": path,
                        "contentLength": len(content),
                        "preview": summarize_text(content, 200),
                    },
                },
                event_id=tool_event_id,
            )
            started_tool_ids.add(tool_event_id)

        last_len = streamed_lengths.get(tool_event_id, 0)
        if len(content) - last_len >= 40:
            streamed_lengths[tool_event_id] = len(content)
            await self._send(
                "setFile",
                data={"path": path, "content": content},
            )

    async def _run_with_session(self, session) -> dict[str, str]:
        max_steps = 20

        for _ in range(max_steps):
            assistant_event_id = self._next_event_id("assistant")
            thinking_event_id = self._next_event_id("thinking")
            started_tool_ids: set[str] = set()
            streamed_lengths: Dict[str, int] = {}

            async def on_event(event: StreamEvent) -> None:
                if event.type == "assistant_delta" and event.text:
                    await self._send("assistant", event.text, event_id=assistant_event_id)
                    return
                if event.type == "thinking_delta" and event.text:
                    await self._send("thinking", event.text, event_id=thinking_event_id)
                    return
                if event.type == "tool_call_delta":
                    await self._handle_streamed_tool_delta(
                        event, started_tool_ids, streamed_lengths
                    )

            turn = await session.stream_turn(on_event)

            if not turn.tool_calls:
                return self.file_state.get_all_files()

            executed_tool_calls: List[ExecutedToolCall] = []
            for tool_call in turn.tool_calls:
                tool_event_id = tool_call.id or self._next_event_id("tool")
                if tool_event_id not in started_tool_ids:
                    await self._send(
                        "toolStart",
                        data={
                            "name": tool_call.name,
                            "input": {
                                "path": extract_path_from_args(tool_call.arguments) or "",
                                "contentLength": len(
                                    extract_content_from_args(tool_call.arguments) or ""
                                ),
                            },
                        },
                        event_id=tool_event_id,
                    )

                tool_result = await self.tool_runtime.execute(tool_call)

                if tool_result.ok and tool_call.name == "create_file":
                    path = tool_call.arguments.get("path", "")
                    await self._send(
                        "setFile",
                        data={
                            "path": path,
                            "content": tool_result.updated_content or "",
                        },
                    )

                await self._send(
                    "toolResult",
                    data={
                        "name": tool_call.name,
                        "output": tool_result.summary,
                        "ok": tool_result.ok,
                    },
                    event_id=tool_event_id,
                )
                executed_tool_calls.append(
                    ExecutedToolCall(tool_call=tool_call, result=tool_result)
                )

            session.append_tool_results(turn, executed_tool_calls)

        raise Exception("Backend agent exceeded max tool turns")

    async def run(
        self, model: Llm, prompt_messages: List[ChatCompletionMessageParam]
    ) -> dict[str, str]:
        session = create_provider_session(
            model=model,
            prompt_messages=prompt_messages,
            should_generate_images=False,
            openai_api_key=self.openai_api_key,
            openai_base_url=self.openai_base_url,
            anthropic_api_key=self.anthropic_api_key,
            gemini_api_key=self.gemini_api_key,
            custom_tools=backend_tool_definitions(),
        )
        try:
            return await self._run_with_session(session)
        finally:
            await session.close()
