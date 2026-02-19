"""
Queue Server v2 for TLC LLM Playground
======================================

Same as queue_server.py but with SSE comment-based queue position feedback
for the OpenAI-compatible endpoint.

Key difference: When streaming from /v1/chat/completions, this version sends
SSE comments (: prefixed lines) with queue position updates:
    : queue_entered=5
    : queue_position=3
    : queue_position=2
    : queue_position=1
    data: {"id":"chatcmpl-...","choices":[{"delta":{"content":"Hello"}}]}

Standard OpenAI clients ignore these comments (per SSE spec).
Custom clients can parse them for queue feedback.

Run on port 8001 for side-by-side comparison:
    uvicorn queue_server_v2:app --reload --host 0.0.0.0 --port 8001
"""

import asyncio
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import AsyncOpenAI

import config

app = FastAPI(
    title="LLM Queue Server v2",
    description="Queue server with SSE queue position feedback",
    version="0.2.0"
)


# ============================================================================
# Data Models
# ============================================================================

class QueueRequest(BaseModel):
    """Request to add an LLM completion to the queue."""
    client_id: str
    messages: list[dict]
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    top_k: Optional[int] = None
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    repeat_penalty: Optional[float] = None
    stop: Optional[list[str]] = None
    logit_bias: Optional[dict[str, float]] = None
    seed: Optional[int] = None
    stream: bool = True
    tools: Optional[list[dict]] = None
    tool_choice: Optional[str] = None
    user: Optional[str] = None


class QueueResponse(BaseModel):
    """Response when a request is queued."""
    status: str
    request_id: str
    queue_position: int


class RequestStatus(BaseModel):
    """Tracks the current status of a request."""
    status: str  # "queued" | "processing" | "complete" | "error"
    client_id: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    queue_entered_position: Optional[int] = None  # NEW: track where we entered the queue


class OpenAIChatRequest(BaseModel):
    """Standard OpenAI chat completion request format."""
    model: str
    messages: list[dict]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    top_p: Optional[float] = 1.0
    top_k: Optional[int] = None
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    repeat_penalty: Optional[float] = None
    stop: Optional[list[str]] = None
    logit_bias: Optional[dict[str, float]] = None
    seed: Optional[int] = None
    stream: Optional[bool] = False
    tools: Optional[list[dict]] = None
    tool_choice: Optional[str] = None
    user: Optional[str] = None


# ============================================================================
# Queue Data Structures
# ============================================================================

request_queue: asyncio.Queue = asyncio.Queue()
status_tracker: dict[str, RequestStatus] = {}
stream_chunks: dict[str, asyncio.Queue] = {}

queue_stats = {
    "total_received": 0,
    "total_processed": 0,
    "total_errors": 0,
    "current_request_id": None,
}

worker_running = True

llm_client = AsyncOpenAI(
    base_url=config.LM_STUDIO_BASE_URL,
    api_key=config.LM_STUDIO_API_KEY
)


# ============================================================================
# Background Worker
# ============================================================================

async def queue_worker():
    """Background worker that processes requests from the queue."""
    print("[WORKER] Queue worker started - waiting for requests...")

    while worker_running:
        try:
            try:
                queue_item = await asyncio.wait_for(request_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            request_id = queue_item["request_id"]
            client_id = queue_item["client_id"]
            request_data = queue_item["request_data"]

            print(f"[WORKER] Processing request {request_id} from {client_id}")

            status_tracker[request_id].status = "processing"
            status_tracker[request_id].started_at = datetime.now().isoformat()
            queue_stats["current_request_id"] = request_id

            try:
                stream_chunks[request_id] = asyncio.Queue()

                messages = request_data.get("messages", [])
                model = request_data.get("model")

                print(f"[LLM] Calling LM Studio with model: {model}")

                llm_kwargs = {
                    "model": model,
                    "messages": messages,
                    "stream": True,
                    "temperature": request_data.get("temperature", 0.7),
                    "top_p": request_data.get("top_p", 1.0),
                    "frequency_penalty": request_data.get("frequency_penalty", 0.0),
                    "presence_penalty": request_data.get("presence_penalty", 0.0),
                }

                optional_params = [
                    "max_tokens", "top_k", "repeat_penalty", "stop",
                    "logit_bias", "seed", "tools", "tool_choice"
                ]
                for param in optional_params:
                    value = request_data.get(param)
                    if value is not None:
                        llm_kwargs[param] = value

                stream = await llm_client.chat.completions.create(**llm_kwargs)

                full_response = ""

                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        await stream_chunks[request_id].put(content)

                await stream_chunks[request_id].put(None)

                status_tracker[request_id].status = "complete"
                status_tracker[request_id].completed_at = datetime.now().isoformat()
                status_tracker[request_id].result = full_response

                queue_stats["total_processed"] += 1
                queue_stats["current_request_id"] = None

                print(f"[OK] Request {request_id} completed ({len(full_response)} chars)")

            except Exception as processing_error:
                print(f"[ERROR] Error processing request {request_id}: {processing_error}")

                if request_id in stream_chunks:
                    try:
                        await stream_chunks[request_id].put({"error": str(processing_error)})
                    except:
                        pass

                status_tracker[request_id].status = "error"
                status_tracker[request_id].completed_at = datetime.now().isoformat()
                status_tracker[request_id].error = str(processing_error)

                queue_stats["total_errors"] += 1
                queue_stats["current_request_id"] = None

        except Exception as e:
            print(f"[ERROR] Worker error: {e}")
            await asyncio.sleep(1)

    print("[WORKER] Queue worker stopped")


# ============================================================================
# Lifecycle Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    print("[SERVER] Starting up v2...")
    asyncio.create_task(queue_worker())
    print("[SERVER] Background worker launched")


@app.on_event("shutdown")
async def shutdown_event():
    global worker_running
    print("[SERVER] Shutting down...")
    worker_running = False
    await asyncio.sleep(2)
    print("[SERVER] Shutdown complete")


# ============================================================================
# Queue Management Endpoints (same as v1)
# ============================================================================

@app.post("/queue/add", response_model=QueueResponse)
async def add_to_queue(request: QueueRequest):
    """Add a new LLM request to the queue."""
    request_id = str(uuid.uuid4())
    queue_position = request_queue.qsize() + 1  # +1 because we're about to add

    status_tracker[request_id] = RequestStatus(
        status="queued",
        client_id=request.client_id,
        created_at=datetime.now().isoformat(),
        queue_entered_position=queue_position,
    )

    queue_item = {
        "request_id": request_id,
        "client_id": request.client_id,
        "request_data": request.dict(),
    }

    await request_queue.put(queue_item)
    queue_stats["total_received"] += 1

    return QueueResponse(
        status="queued",
        request_id=request_id,
        queue_position=queue_position
    )


@app.get("/queue/status")
async def get_queue_status():
    """Get overall queue status and statistics."""
    return {
        "queue_size": request_queue.qsize(),
        "stats": queue_stats,
        "tracked_requests": len(status_tracker)
    }


@app.get("/request/{request_id}")
async def get_request_status(request_id: str):
    """Get the status of a specific request."""
    if request_id not in status_tracker:
        return {"error": "Request ID not found"}
    return status_tracker[request_id]


# ============================================================================
# Streaming Endpoint (same as v1)
# ============================================================================

@app.get("/stream/{request_id}")
async def stream_response(request_id: str):
    """Stream the LLM response using Server-Sent Events."""
    if request_id not in status_tracker:
        return {"error": "Request ID not found"}

    async def event_generator():
        import json

        while status_tracker[request_id].status == "queued":
            queue_pos = request_queue.qsize()
            yield f"data: {json.dumps({'position': queue_pos})}\n\n"
            await asyncio.sleep(0.5)

        if status_tracker[request_id].status == "error":
            yield f"data: {json.dumps({'error': status_tracker[request_id].error})}\n\n"
            return

        while request_id not in stream_chunks:
            await asyncio.sleep(0.1)

        chunk_queue = stream_chunks[request_id]

        while True:
            chunk = await chunk_queue.get()

            if chunk is None:
                yield f"data: {json.dumps({'done': True})}\n\n"
                break
            elif isinstance(chunk, dict) and "error" in chunk:
                yield f"data: {json.dumps({'error': chunk['error']})}\n\n"
                break
            else:
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"

        if request_id in stream_chunks:
            del stream_chunks[request_id]

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


# ============================================================================
# OpenAI-Compatible Endpoint WITH Queue Position Feedback
# ============================================================================
# This is the key difference from v1 - SSE comments provide queue info

@app.post("/v1/chat/completions")
async def openai_chat_completions(request: OpenAIChatRequest):
    """
    OpenAI-compatible chat completions with queue position feedback.

    When streaming, sends SSE comments (: prefixed) with queue info:
        : queue_entered=5
        : queue_position=3
        data: {"id":"chatcmpl-...","choices":[{"delta":{"content":"Hi"}}]}

    Standard OpenAI clients ignore comments per SSE spec.
    Custom clients can parse them for queue feedback.
    """
    import json
    import time

    request_id = str(uuid.uuid4())
    queue_position = request_queue.qsize() + 1  # Position we'll be at after adding

    status_tracker[request_id] = RequestStatus(
        status="queued",
        client_id="openai_compat",
        created_at=datetime.now().isoformat(),
        queue_entered_position=queue_position,
    )

    queue_item = {
        "request_id": request_id,
        "client_id": "openai_compat",
        "request_data": request.dict(),
    }

    await request_queue.put(queue_item)
    queue_stats["total_received"] += 1

    print(f"[QUEUE] OpenAI-compat request {request_id} queued at position {queue_position} (stream={request.stream})")

    if request.stream:
        async def openai_stream_generator():
            """
            Generates SSE events in OpenAI format with queue position comments.
            """
            created_timestamp = int(time.time())

            # Send initial queue position as SSE comment
            entered_pos = status_tracker[request_id].queue_entered_position
            yield f": queue_entered={entered_pos}\n"

            # Wait for request to start processing, sending position updates
            last_position = None
            while status_tracker[request_id].status == "queued":
                current_position = request_queue.qsize()
                # Only send if position changed (avoid spam)
                if current_position != last_position:
                    yield f": queue_position={current_position}\n"
                    last_position = current_position
                await asyncio.sleep(0.3)

            # Send "processing" indicator
            yield ": queue_position=0\n"

            # Check for errors
            if status_tracker[request_id].status == "error":
                error_msg = status_tracker[request_id].error or "Unknown error"
                error_chunk = {
                    "error": {"message": error_msg, "type": "server_error"}
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
                return

            # Wait for stream queue
            while request_id not in stream_chunks:
                await asyncio.sleep(0.05)

            chunk_queue = stream_chunks[request_id]

            while True:
                chunk = await chunk_queue.get()

                if chunk is None:
                    finish_chunk = {
                        "id": f"chatcmpl-{request_id}",
                        "object": "chat.completion.chunk",
                        "created": created_timestamp,
                        "model": request.model,
                        "choices": [{
                            "index": 0,
                            "delta": {},
                            "finish_reason": "stop"
                        }]
                    }
                    yield f"data: {json.dumps(finish_chunk)}\n\n"
                    yield "data: [DONE]\n\n"
                    break

                elif isinstance(chunk, dict) and "error" in chunk:
                    error_chunk = {
                        "error": {"message": chunk["error"], "type": "server_error"}
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"
                    break

                else:
                    content_chunk = {
                        "id": f"chatcmpl-{request_id}",
                        "object": "chat.completion.chunk",
                        "created": created_timestamp,
                        "model": request.model,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": chunk},
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(content_chunk)}\n\n"

            if request_id in stream_chunks:
                del stream_chunks[request_id]

        return StreamingResponse(
            openai_stream_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )

    else:
        # Non-streaming - same as v1 (no way to send queue updates)
        timeout_seconds = 300
        start_time = asyncio.get_event_loop().time()

        while status_tracker[request_id].status in ("queued", "processing"):
            if asyncio.get_event_loop().time() - start_time > timeout_seconds:
                return {"error": {"message": "Request timed out", "type": "timeout"}}
            await asyncio.sleep(0.1)

        status = status_tracker[request_id]

        if status.status == "error":
            return {"error": {"message": status.error or "Unknown error", "type": "server_error"}}

        return {
            "id": f"chatcmpl-{request_id}",
            "object": "chat.completion",
            "created": int(datetime.fromisoformat(status.created_at).timestamp()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": status.result},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": -1, "completion_tokens": -1, "total_tokens": -1}
        }


# ============================================================================
# Model Discovery Endpoint
# ============================================================================

@app.get("/v1/models")
async def list_models():
    """List available models from LM Studio."""
    try:
        models = await llm_client.models.list()
        return {
            "object": "list",
            "data": [model.model_dump() for model in models.data]
        }
    except Exception as e:
        error_msg = str(e)
        if "Connection refused" in error_msg or "Cannot connect" in error_msg:
            return {
                "error": {
                    "message": f"Cannot reach LM Studio at {config.LM_STUDIO_BASE_URL}. Is it running?",
                    "type": "connection_error",
                    "details": error_msg
                }
            }
        return {
            "error": {
                "message": "Failed to fetch models from LM Studio",
                "type": "server_error",
                "details": error_msg
            }
        }


# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/")
def root():
    return {
        "status": "running",
        "message": "LLM Queue Server v2 (with queue position feedback)",
        "version": "0.2.0"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "lm_studio_url": config.LM_STUDIO_BASE_URL,
        "queue_size": request_queue.qsize(),
        "stats": queue_stats,
        "version": "0.2.0",
        "features": ["sse_queue_position_comments"]
    }


# ============================================================================
# Run with:
#   uvicorn queue_server_v2:app --reload --host 0.0.0.0 --port 8001
# ============================================================================
