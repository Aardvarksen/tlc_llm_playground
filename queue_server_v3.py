"""
Queue Server v3 for TLC LLM Playground
======================================

Builds on v2 with full tool-calling support for agentic clients.

Key changes from v2:
- Worker forwards full stream deltas (not just content strings), preserving
  tool_calls, finish_reason, and any other fields the model returns.
- SSE streaming endpoint passes delta through as-is instead of reconstructing it.
- Non-streaming responses include tool_calls in the message when present.
- finish_reason reflects the actual model output ("stop" vs "tool_calls").

Queue position feedback via SSE comments is preserved from v2:
    : queue_entered=5
    : queue_position=3
    : queue_position=1
    data: {"id":"chatcmpl-...","choices":[{"delta":{"content":"Hello"}}]}

For tool call responses the deltas look like:
    data: {"id":"chatcmpl-...","choices":[{"delta":{"tool_calls":[...]},"finish_reason":null}]}

Run:
    uvicorn queue_server_v3:app --reload --host 0.0.0.0 --port 8001
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
    title="LLM Queue Server v3",
    description="Queue server with tool-calling support and SSE queue position feedback",
    version="0.3.0"
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
    tool_calls: Optional[list[dict]] = None
    error: Optional[str] = None
    queue_entered_position: Optional[int] = None


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

                # Accumulate content and tool_calls for non-streaming result
                full_response = ""
                accumulated_tool_calls = []

                async for chunk in stream:
                    if chunk.choices:
                        delta = chunk.choices[0].delta
                        finish_reason = chunk.choices[0].finish_reason

                        # Accumulate text content
                        if delta.content:
                            full_response += delta.content

                        # Accumulate tool calls by index
                        if delta.tool_calls:
                            for tc_delta in delta.tool_calls:
                                idx = tc_delta.index
                                # Extend list to fit this index
                                while len(accumulated_tool_calls) <= idx:
                                    accumulated_tool_calls.append({
                                        "id": "",
                                        "type": "function",
                                        "function": {"name": "", "arguments": ""}
                                    })
                                if tc_delta.id:
                                    accumulated_tool_calls[idx]["id"] = tc_delta.id
                                if tc_delta.type:
                                    accumulated_tool_calls[idx]["type"] = tc_delta.type
                                if tc_delta.function:
                                    if tc_delta.function.name:
                                        accumulated_tool_calls[idx]["function"]["name"] += tc_delta.function.name
                                    if tc_delta.function.arguments:
                                        accumulated_tool_calls[idx]["function"]["arguments"] += tc_delta.function.arguments

                        # Forward full delta dict to stream consumers
                        await stream_chunks[request_id].put({
                            "delta": delta.model_dump(exclude_none=True),
                            "finish_reason": finish_reason
                        })

                # Sentinel: signals end of stream
                await stream_chunks[request_id].put(None)

                status_tracker[request_id].status = "complete"
                status_tracker[request_id].completed_at = datetime.now().isoformat()
                status_tracker[request_id].result = full_response if full_response else None
                status_tracker[request_id].tool_calls = accumulated_tool_calls if accumulated_tool_calls else None

                queue_stats["total_processed"] += 1
                queue_stats["current_request_id"] = None

                tc_info = f", {len(accumulated_tool_calls)} tool call(s)" if accumulated_tool_calls else ""
                print(f"[OK] Request {request_id} completed ({len(full_response)} chars{tc_info})")

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
    print("[SERVER] Starting up v3...")
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
# Queue Management Endpoints
# ============================================================================

@app.post("/queue/add", response_model=QueueResponse)
async def add_to_queue(request: QueueRequest):
    """Add a new LLM request to the queue."""
    request_id = str(uuid.uuid4())
    queue_position = request_queue.qsize() + 1

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
# Streaming Endpoint
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
            elif isinstance(chunk, dict) and "delta" in chunk:
                # Extract text content as "chunk" for backward compat
                # with Streamlit pages (side_by_side, batch_runner)
                content = chunk["delta"].get("content")
                if content:
                    yield f"data: {json.dumps({'chunk': content})}\n\n"
                # Forward tool_calls as full delta for advanced consumers
                elif chunk["delta"].get("tool_calls"):
                    yield f"data: {json.dumps(chunk)}\n\n"
            else:
                # Fallback for unexpected formats
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

@app.post("/v1/chat/completions")
async def openai_chat_completions(request: OpenAIChatRequest):
    """
    OpenAI-compatible chat completions with queue position feedback.

    When streaming, sends SSE comments (: prefixed) with queue info:
        : queue_entered=5
        : queue_position=3
        data: {"id":"chatcmpl-...","choices":[{"delta":{"content":"Hi"}}]}

    Tool call deltas are forwarded as-is:
        data: {"id":"chatcmpl-...","choices":[{"delta":{"tool_calls":[...]},"finish_reason":null}]}

    Standard OpenAI clients ignore comments per SSE spec.
    Custom clients can parse them for queue feedback.
    """
    import json
    import time

    request_id = str(uuid.uuid4())
    queue_position = request_queue.qsize() + 1

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
            Forwards full deltas (content, tool_calls, etc.) as received from the model.
            """
            created_timestamp = int(time.time())

            # Send initial queue position as SSE comment
            entered_pos = status_tracker[request_id].queue_entered_position
            yield f": queue_entered={entered_pos}\n"

            # Wait for request to start processing, sending position updates
            last_position = None
            while status_tracker[request_id].status == "queued":
                current_position = request_queue.qsize()
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
                    # Sentinel — the real finish chunk (with finish_reason)
                    # already came through in the stream. Just close out.
                    yield "data: [DONE]\n\n"
                    break

                elif isinstance(chunk, dict) and "error" in chunk:
                    error_chunk = {
                        "error": {"message": chunk["error"], "type": "server_error"}
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"
                    break

                else:
                    # Forward the delta and finish_reason as-is
                    openai_chunk = {
                        "id": f"chatcmpl-{request_id}",
                        "object": "chat.completion.chunk",
                        "created": created_timestamp,
                        "model": request.model,
                        "choices": [{
                            "index": 0,
                            "delta": chunk["delta"],
                            "finish_reason": chunk["finish_reason"]
                        }]
                    }
                    yield f"data: {json.dumps(openai_chunk)}\n\n"

            if request_id in stream_chunks:
                del stream_chunks[request_id]

        return StreamingResponse(
            openai_stream_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )

    else:
        # Non-streaming — wait for completion then return full response
        timeout_seconds = 300
        start_time = asyncio.get_event_loop().time()

        while status_tracker[request_id].status in ("queued", "processing"):
            if asyncio.get_event_loop().time() - start_time > timeout_seconds:
                return {"error": {"message": "Request timed out", "type": "timeout"}}
            await asyncio.sleep(0.1)

        status = status_tracker[request_id]

        if status.status == "error":
            return {"error": {"message": status.error or "Unknown error", "type": "server_error"}}

        message = {"role": "assistant", "content": status.result}
        if status.tool_calls:
            message["tool_calls"] = status.tool_calls

        return {
            "id": f"chatcmpl-{request_id}",
            "object": "chat.completion",
            "created": int(datetime.fromisoformat(status.created_at).timestamp()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": message,
                "finish_reason": "tool_calls" if status.tool_calls else "stop"
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
        "message": "LLM Queue Server v3 (tool-calling support + queue position feedback)",
        "version": "0.3.0"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "lm_studio_url": config.LM_STUDIO_BASE_URL,
        "queue_size": request_queue.qsize(),
        "stats": queue_stats,
        "version": "0.3.0",
        "features": ["sse_queue_position_comments", "tool_calling"]
    }


# ============================================================================
# Run with:
#   uvicorn queue_server_v3:app --reload --host 0.0.0.0 --port 8001
# ============================================================================
