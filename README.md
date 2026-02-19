# local-agentic-rag

Phase 1 is implemented and testable.

## Phase 1 scope

- FastAPI service with [`/healthz`](services/api/app/main.py:10)
- OpenAI-compatible model list endpoint at [`/v1/models`](services/api/app/openai_compat/chat.py:25)
- OpenAI-compatible non-streaming chat endpoint at [`/v1/chat/completions`](services/api/app/openai_compat/chat.py:40)
- Provider switch support in [`Settings`](services/api/app/settings.py:9) with OpenAI default

## Prerequisites

- Python 3.11 installed
- uv installed
- OpenAI API key (if using OpenAI provider)

## Setup and run with uv

From repository root:

1. Go to API service folder:

   cd services/api

2. Create local env file:

   copy .env.example .env

3. Edit `.env` and set provider values:

   - `CHAT_PROVIDER=openai`
   - `EMBEDDING_PROVIDER=openai`
   - `OPENAI_API_KEY=...`

4. Sync dependencies with uv:

   uv sync

5. Run API with uv:

   uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

## Phase 1 test steps

Open a second terminal in `services/api`.

### 1) Health check

curl http://localhost:8000/healthz

Expected: JSON containing `status: ok` and provider fields.

### 2) Models list

curl http://localhost:8000/v1/models

Expected: OpenAI-style list response with model ids.

### 3) Non-streaming chat completion

curl -X POST http://localhost:8000/v1/chat/completions -H "Content-Type: application/json" -d "{\"model\":\"gpt-4o-mini\",\"messages\":[{\"role\":\"user\",\"content\":\"Say hello from phase 1\"}],\"stream\":false}"

Expected: OpenAI-style `chat.completion` JSON with `choices[0].message.content`.

## Optional: switch to Ollama provider (still Phase 1-compatible)

In `.env`:

- `CHAT_PROVIDER=ollama`
- `OLLAMA_BASE_URL=http://localhost:11434`
- `OLLAMA_CHAT_MODEL=qwen2.5:7b-instruct`

Then restart the API and run the same tests.

## Implemented files

- [`services/api/pyproject.toml`](services/api/pyproject.toml)
- [`services/api/.env.example`](services/api/.env.example)
- [`services/api/app/main.py`](services/api/app/main.py)
- [`services/api/app/settings.py`](services/api/app/settings.py)
- [`services/api/app/openai_compat/models.py`](services/api/app/openai_compat/models.py)
- [`services/api/app/openai_compat/chat.py`](services/api/app/openai_compat/chat.py)
- [`.gitignore`](.gitignore)
