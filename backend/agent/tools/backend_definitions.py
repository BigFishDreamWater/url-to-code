"""Tool definitions for backend code generation (multi-file mode)."""

from typing import Any, Dict, List

from agent.tools.types import CanonicalToolDefinition


def _backend_create_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "File path relative to project root, e.g. app.py, routes/users.py, schema.sql",
            },
            "content": {
                "type": "string",
                "description": "Full content of the file.",
            },
        },
        "required": ["path", "content"],
    }


def backend_tool_definitions() -> List[CanonicalToolDefinition]:
    return [
        CanonicalToolDefinition(
            name="create_file",
            description=(
                "Create a project file. Call once per file with the full content. "
                "You may create multiple files by calling this tool multiple times."
            ),
            parameters=_backend_create_schema(),
        ),
    ]
