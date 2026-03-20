Queue Server v2 — Tool Calling Support                                                                                                             
                                                                                                                                                       Context                                                                                                                                            

  The queue server (queue_server_v2_reference.py) currently handles text chat completions correctly but silently drops tool calls. This is blocking  
  agentic clients (specifically Qwen Code CLI using Qwen3-Coder-Next) from functioning.

  The Three Bugs

  Bug 1 — Worker ignores tool_calls in stream chunks (line 186)

  # CURRENT — only captures .content, tool_calls are silently dropped
  async for chunk in stream:
      if chunk.choices and chunk.choices[0].delta.content:
          content = chunk.choices[0].delta.content
          full_response += content
          await stream_chunks[request_id].put(content)
  Tool call data arrives in chunk.choices[0].delta.tool_calls, not .content. The condition if ... .content is False for tool call chunks, so they    
  never enter the queue.

  Bug 2 — Streaming response hardcodes delta: {content: chunk} (line 460)

  # CURRENT — always reconstructs delta as a plain content string
  "delta": {"content": chunk},
  The worker puts raw strings into stream_chunks. The SSE formatter then wraps them back as {"content": chunk}. Tool call deltas have a completely   
  different shape — they need to be forwarded as-is, not reconstructed.

  Bug 3 — Non-streaming response wraps result as plain string (line 491)

  # CURRENT — result is a plain string, tool_calls never present
  "message": {"role": "assistant", "content": status.result},
  Tool call responses need message.tool_calls populated, not just message.content.

  ---
  What Needs to Change

  1. Worker: forward raw chunks instead of extracted strings

  Instead of putting content strings into stream_chunks, put the serialized chunk delta so the full structure (content OR tool_calls) is preserved:  

  async for chunk in stream:
      if chunk.choices:
          delta = chunk.choices[0].delta
          finish_reason = chunk.choices[0].finish_reason
          # Put the whole delta as a dict, not just .content
          await stream_chunks[request_id].put({
              "delta": delta.model_dump(exclude_none=True),
              "finish_reason": finish_reason
          })

  await stream_chunks[request_id].put(None)  # sentinel

  Also accumulate tool_calls alongside full_response for the non-streaming result.

  2. SSE formatter: forward delta as-is

  # Replace the hardcoded {"content": chunk} with the forwarded delta
  content_chunk = {
      "id": f"chatcmpl-{request_id}",
      "object": "chat.completion.chunk",
      "created": created_timestamp,
      "model": request.model,
      "choices": [{
          "index": 0,
          "delta": chunk["delta"],        # ← forward whatever came back
          "finish_reason": chunk["finish_reason"]
      }]
  }

  3. Non-streaming response: include tool_calls if present

  The worker needs to accumulate tool call data during streaming and store it on RequestStatus. The non-streaming response then returns:
  "message": {
      "role": "assistant",
      "content": status.result or None,
      "tool_calls": status.tool_calls or None  # new field on RequestStatus
  }

  4. RequestStatus model: add tool_calls field

  class RequestStatus(BaseModel):
      ...
      tool_calls: Optional[list[dict]] = None  # new

  ---
  Definition of Done

  - Streaming responses forward tool_calls deltas correctly in SSE chunks
  - Non-streaming responses include message.tool_calls when tool calls are present
  - Plain text chat still works (no regression)
  - Qwen Code CLI can complete a tool-calling round trip through the queue server

  Notes

  - The tools and tool_choice fields are already accepted by OpenAIChatRequest and QueueRequest and already forwarded to LM Studio in llm_kwargs — so
   the upstream leg is fine. Only the response path is broken.
  - Keep the SSE comment-based queue position feedback intact — that's a feature, not noise.
  - This is a reference file (queue_server_v2_reference.py) — confirm the actual running filename on the RTXBox before editing.