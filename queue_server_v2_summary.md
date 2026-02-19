# Queue Server v2 Summary

> **Purpose**: Reference document for understanding and testing `queue_server_v2.py`
> **Audience**: Claude instances building tests, Darrin learning the system

## What Is This?

A FastAPI server that sits between your apps and LM Studio, providing:
1. **Request queuing** - Multiple apps can submit requests; they're processed one at a time
2. **OpenAI API compatibility** - Apps can use the standard OpenAI client library
3. **Queue position feedback** - (v2 feature) Tells clients where they are in the queue via SSE comments

```
┌─────────────┐     ┌──────────────────┐     ┌────────────┐
│ Your App    │────▶│ Queue Server v2  │────▶│ LM Studio  │
│ (Streamlit, │     │ (port 8001)      │     │ (port 1234)│
│  scripts)   │◀────│                  │◀────│            │
└─────────────┘     └──────────────────┘     └────────────┘
```

## Why Queue?

LM Studio can only process one request at a time. If you send a second request while one is running, it either fails or gets weird. The queue server serializes requests so they're processed one-by-one.

## Endpoints

### Health & Discovery

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Basic health check, returns version |
| `/health` | GET | Detailed health with queue stats |
| `/v1/models` | GET | Lists available models from LM Studio |

### Queue Management (Custom Protocol)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/queue/add` | POST | Add request to queue, get request_id back |
| `/queue/status` | GET | Overall queue size and stats |
| `/request/{id}` | GET | Status of specific request |
| `/stream/{id}` | GET | SSE stream of response chunks |

### OpenAI-Compatible (Drop-in Replacement)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/chat/completions` | POST | Standard OpenAI chat API |

## The v2 Feature: SSE Queue Position Comments

### The Problem
When using `/v1/chat/completions`, the client has no idea where they are in the queue. They just wait... and wait... with no feedback.

### The Solution
SSE (Server-Sent Events) spec says lines starting with `:` are comments that clients should ignore. We use these to send queue position updates:

```
: queue_entered=5       <- "You entered at position 5"
: queue_position=3      <- "Now at position 3" (updates as queue moves)
: queue_position=1
: queue_position=0      <- "Now processing your request"
data: {"id":"chatcmpl-abc","choices":[{"delta":{"content":"Hello"}}]}
data: {"id":"chatcmpl-abc","choices":[{"delta":{"content":" there"}}]}
data: {"id":"chatcmpl-abc","choices":[{"delta":{}}],"finish_reason":"stop"}
data: [DONE]
```

### Compatibility
- **Standard OpenAI clients**: Ignore comments, work normally
- **Custom clients**: Can parse comments for queue feedback

## Data Flow for `/v1/chat/completions` (Streaming)

```
1. Client POSTs to /v1/chat/completions with stream=true

2. Server:
   - Generates request_id (UUID)
   - Records queue_entered_position = current_queue_size + 1
   - Creates status_tracker entry (status="queued")
   - Adds to request_queue
   - Returns StreamingResponse immediately

3. StreamingResponse generator:
   - Yields `: queue_entered={position}\n`
   - While status == "queued":
       - Yields `: queue_position={current_size}\n` (when changed)
       - Sleeps 0.3s
   - Yields `: queue_position=0\n` (processing indicator)
   - Waits for stream_chunks[request_id] to exist
   - While chunks available:
       - Yields `data: {openai_format_chunk}\n\n`
   - Yields `data: [DONE]\n\n`

4. Background worker (separate async task):
   - Pulls request from queue
   - Updates status to "processing"
   - Creates stream_chunks[request_id] queue
   - Calls LM Studio with streaming
   - For each chunk from LM Studio:
       - Puts chunk into stream_chunks[request_id]
   - Puts None (signals done)
   - Updates status to "complete"
```

## Key Data Structures

### request_queue (asyncio.Queue)
Items are dicts:
```python
{
    "request_id": "uuid-string",
    "client_id": "openai_compat",  # or custom client name
    "request_data": { ... }        # The full request payload
}
```

### status_tracker (dict)
Maps request_id to RequestStatus:
```python
{
    "status": "queued" | "processing" | "complete" | "error",
    "client_id": "openai_compat",
    "created_at": "2025-01-20T10:30:00",
    "started_at": "2025-01-20T10:30:05" | None,
    "completed_at": "2025-01-20T10:30:10" | None,
    "result": "The full response text" | None,
    "error": "Error message" | None,
    "queue_entered_position": 5  # v2: where we entered the queue
}
```

### stream_chunks (dict)
Maps request_id to asyncio.Queue containing:
- String chunks (actual content)
- `None` (signals stream complete)
- `{"error": "message"}` (signals error)

## Testing Checklist

### Basic Functionality
- [ ] `/` returns status and version "0.2.0"
- [ ] `/health` returns queue stats
- [ ] `/v1/models` returns model list (or helpful error if LM Studio down)

### Queue Position Feedback (The v2 Feature)
- [ ] Streaming response starts with `: queue_entered=N` comment
- [ ] While queued, sends `: queue_position=N` comments
- [ ] Position updates only sent when value changes (not every 0.3s spam)
- [ ] `: queue_position=0` sent when processing starts
- [ ] After comments, normal OpenAI-format chunks flow

### OpenAI Compatibility
- [ ] Standard `openai` Python client works without modification
- [ ] Streaming responses match OpenAI format exactly
- [ ] Non-streaming responses match OpenAI format exactly
- [ ] `data: [DONE]` sent at end of stream

### Queue Behavior
- [ ] Multiple simultaneous requests queue properly
- [ ] Requests processed in FIFO order
- [ ] Queue position decrements as earlier requests complete
- [ ] `/queue/status` accurately reflects queue state

### Error Handling
- [ ] LM Studio connection errors return helpful message
- [ ] Errors during processing sent via stream
- [ ] Status tracker updated to "error" state

## Running the Server

```bash
# From project directory with venv activated
uvicorn queue_server_v2:app --reload --host 0.0.0.0 --port 8001
```

## Example: Parsing Queue Comments in Python

```python
import httpx

def stream_with_queue_feedback(messages, model):
    """Example client that parses queue position comments."""

    queue_entered = None
    queue_position = None

    with httpx.stream(
        "POST",
        "http://localhost:8001/v1/chat/completions",
        json={"model": model, "messages": messages, "stream": True},
        timeout=300
    ) as response:
        for line in response.iter_lines():
            if line.startswith(': queue_entered='):
                queue_entered = int(line.split('=')[1])
                print(f"Entered queue at position {queue_entered}")

            elif line.startswith(': queue_position='):
                queue_position = int(line.split('=')[1])
                if queue_position == 0:
                    print("Now processing...")
                else:
                    print(f"Queue position: {queue_position}")

            elif line.startswith('data: ') and line != 'data: [DONE]':
                import json
                chunk = json.loads(line[6:])
                if 'choices' in chunk:
                    delta = chunk['choices'][0].get('delta', {})
                    if 'content' in delta:
                        print(delta['content'], end='', flush=True)

            elif line == 'data: [DONE]':
                print("\n[Complete]")
```

## Differences from queue_server.py (v1)

| Aspect | v1 | v2 |
|--------|----|----|
| Version | 0.1.0 | 0.2.0 |
| Default port | 8000 | 8001 |
| Queue position in OpenAI endpoint | None | SSE comments |
| `queue_entered_position` in status | No | Yes |
| `/health` features field | No | Yes |

## Configuration

Uses `config.py` for:
- `LM_STUDIO_BASE_URL` - Where LM Studio is running (default: `http://localhost:1234/v1`)
- `LM_STUDIO_API_KEY` - Placeholder (LM Studio doesn't check)
