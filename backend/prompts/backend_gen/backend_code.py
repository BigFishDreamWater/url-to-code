from openai.types.chat import ChatCompletionMessageParam

from prompts.backend_gen.system_prompt import BACKEND_SYSTEM_PROMPT


BackendLanguage = str  # "python" | "php" | "java"

FRAMEWORK_MAP = {
    "python": "Flask",
    "php": "Laravel",
    "java": "Spring Boot",
}


def build_backend_code_prompt(
    api_doc_json: str,
    language: BackendLanguage,
) -> list[ChatCompletionMessageParam]:
    """Build prompt messages for Stage 3: generate backend code from API doc."""

    framework = FRAMEWORK_MAP.get(language, "Flask")

    user = f"""Generate a complete backend project using **{language}** with the **{framework}** framework.

## API Specification

The following JSON describes the endpoints and data models to implement:

<api_spec>
{api_doc_json}
</api_spec>

## Requirements

1. Implement ALL endpoints listed in the spec above.
2. Use SQLite as the database. Create a schema.sql with all CREATE TABLE statements.
3. Include realistic mock/seed data (at least 5 rows per table).
4. Every endpoint must return JSON responses.
5. Add CORS middleware so the frontend at http://localhost:5173 can access the API.
6. Include a README.md with:
   - Project description
   - How to install dependencies
   - How to initialize the database
   - How to run the server
   - API endpoint list with example requests
7. The server should run on port 8000.
8. Keep the code clean and simple. No unnecessary abstractions.

## File creation

Use the create_file tool to create each file. Create all files needed for a runnable project.
"""

    return [
        {"role": "system", "content": BACKEND_SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
