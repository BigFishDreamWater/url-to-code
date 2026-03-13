from openai.types.chat import ChatCompletionMessageParam


def build_api_doc_prompt(frontend_code: str) -> list[ChatCompletionMessageParam]:
    """Build prompt messages for Stage 2: analyze frontend code and generate API doc."""

    system = """You are an API architect. Analyze the provided frontend HTML code and design a simple, clean REST API that would serve the data this frontend needs.

Your output MUST be a single JSON object with this exact structure (no markdown, no explanation, just raw JSON):

{
  "recommended_language": "python" | "php" | "java",
  "recommend_reason": "Brief reason for the recommendation in the user's language",
  "endpoints": [
    {
      "method": "GET" | "POST" | "PUT" | "DELETE",
      "path": "/api/xxx",
      "description": "What this endpoint does",
      "request_body": { ... } | null,
      "response_body": { ... }
    }
  ],
  "data_models": [
    {
      "name": "ModelName",
      "fields": [
        { "name": "id", "type": "INTEGER", "primary_key": true },
        { "name": "field_name", "type": "TEXT|INTEGER|REAL|BOOLEAN", "nullable": false }
      ]
    }
  ]
}

## Rules

- Keep it simple. Only design endpoints the frontend actually needs.
- Identify data displayed on the page: lists, cards, user info, stats, forms, etc.
- For each data source, create a GET endpoint. For forms, create POST endpoints.
- Design flat, obvious REST paths like /api/users, /api/products.
- Do NOT create authentication/login endpoints unless the frontend clearly has a login form.
- Do NOT over-engineer. No pagination, no filtering, no sorting unless the UI clearly needs it.
- Data models should map directly to SQLite tables.
- Use simple field types: INTEGER, TEXT, REAL, BOOLEAN.
- Every model must have an integer primary key named "id".
- Recommend a language based on the project complexity:
  - Simple pages with few endpoints → Python (Flask)
  - Content-heavy sites with many routes → PHP (Laravel)
  - Complex business logic or many data models → Java (Spring Boot)
- Output ONLY the JSON object. No markdown fences, no explanation text.
"""

    user = f"""Analyze this frontend code and design the REST API it needs:

<frontend_code>
{frontend_code}
</frontend_code>"""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
