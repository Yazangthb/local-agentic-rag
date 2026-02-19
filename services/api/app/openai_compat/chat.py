from __future__ import annotations

import time
import uuid
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from openai import OpenAI

from app.openai_compat.models import (
    ChatCompletionChoice,
    ChatCompletionChoiceMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ModelCard,
    ModelsResponse,
    Usage,
)
from app.settings import get_settings

router = APIRouter()


@router.get("/models", response_model=ModelsResponse)
def list_models() -> ModelsResponse:
    settings = get_settings()
    created_at = int(time.time())

    model_ids = [settings.openai_chat_model, settings.ollama_chat_model]
    unique_models = list(dict.fromkeys([m for m in model_ids if m]))

    return ModelsResponse(
        data=[ModelCard(id=model_id, created=created_at) for model_id in unique_models]
    )


@router.post("/chat/completions", response_model=ChatCompletionResponse)
def chat_completions(request: ChatCompletionRequest) -> ChatCompletionResponse:
    if request.stream:
        raise HTTPException(status_code=400, detail="Streaming not enabled in phase 1")

    settings = get_settings()
    model = request.model or (
        settings.openai_chat_model
        if settings.chat_provider == "openai"
        else settings.ollama_chat_model
    )

    if settings.chat_provider == "openai":
        content, usage = _chat_with_openai(model=model, request=request)
    else:
        content, usage = _chat_with_ollama(model=model, request=request)

    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex}",
        created=int(time.time()),
        model=model,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatCompletionChoiceMessage(content=content),
                finish_reason="stop",
            )
        ],
        usage=usage,
    )


def _chat_with_openai(model: str, request: ChatCompletionRequest) -> tuple[str, Usage]:
    settings = get_settings()
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is required when chat_provider=openai",
        )

    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    response = client.chat.completions.create(
        model=model,
        messages=[m.model_dump() for m in request.messages],
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        stream=False,
    )

    if not response.choices:
        raise HTTPException(status_code=502, detail="No choices returned from OpenAI")

    message = response.choices[0].message
    content = message.content or ""
    usage_obj = response.usage

    usage = Usage(
        prompt_tokens=(usage_obj.prompt_tokens if usage_obj else 0),
        completion_tokens=(usage_obj.completion_tokens if usage_obj else 0),
        total_tokens=(usage_obj.total_tokens if usage_obj else 0),
    )
    return content, usage


def _chat_with_ollama(model: str, request: ChatCompletionRequest) -> tuple[str, Usage]:
    settings = get_settings()
    endpoint = f"{settings.ollama_base_url.rstrip('/')}/api/chat"

    payload: dict[str, Any] = {
        "model": model,
        "messages": [m.model_dump() for m in request.messages],
        "stream": False,
        "options": {},
    }
    if request.temperature is not None:
        payload["options"]["temperature"] = request.temperature
    if request.max_tokens is not None:
        payload["options"]["num_predict"] = request.max_tokens

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(endpoint, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Ollama request failed: {exc}") from exc

    content = data.get("message", {}).get("content", "")

    prompt_eval_count = int(data.get("prompt_eval_count") or 0)
    eval_count = int(data.get("eval_count") or 0)
    usage = Usage(
        prompt_tokens=prompt_eval_count,
        completion_tokens=eval_count,
        total_tokens=prompt_eval_count + eval_count,
    )
    return content, usage

