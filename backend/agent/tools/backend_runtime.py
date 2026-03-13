"""Tool runtime for backend code generation (multi-file mode)."""

from typing import Any, Dict

from agent.state import AgentFileState, ensure_str
from agent.tools.types import ToolCall, ToolExecutionResult
from agent.tools.summaries import summarize_text


class BackendToolRuntime:
    def __init__(self, file_state: AgentFileState):
        self.file_state = file_state

    async def execute(self, tool_call: ToolCall) -> ToolExecutionResult:
        if "INVALID_JSON" in tool_call.arguments:
            return ToolExecutionResult(
                ok=False,
                result={"error": "Tool arguments were invalid JSON."},
                summary={"error": "Invalid JSON tool arguments"},
            )

        if tool_call.name == "create_file":
            return self._create_file(tool_call.arguments)

        return ToolExecutionResult(
            ok=False,
            result={"error": f"Unknown tool: {tool_call.name}"},
            summary={"error": f"Unknown tool: {tool_call.name}"},
        )

    def _create_file(self, args: Dict[str, Any]) -> ToolExecutionResult:
        path = ensure_str(args.get("path"))
        content = ensure_str(args.get("content"))

        if not path:
            return ToolExecutionResult(
                ok=False,
                result={"error": "create_file requires a path"},
                summary={"error": "Missing path"},
            )
        if not content:
            return ToolExecutionResult(
                ok=False,
                result={"error": "create_file requires non-empty content"},
                summary={"error": "Missing content"},
            )

        self.file_state.set_file(path, content)

        summary = {
            "path": path,
            "contentLength": len(content),
            "preview": summarize_text(content, 320),
        }
        result = {
            "content": f"Successfully created file at {path}.",
            "details": {"path": path, "contentLength": len(content)},
        }
        return ToolExecutionResult(
            ok=True,
            result=result,
            summary=summary,
            updated_content=content,
        )
