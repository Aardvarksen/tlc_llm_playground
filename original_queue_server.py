from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import queue
import time
from datetime import datetime
import asyncio
import httpx


app = FastAPI()

request_queue = queue.Queue()
queue_stats = {
    "total_processed": 0,
    "current_request": None
}

results = {}
LM_STUDIO_URL = "http://10.0.118.25:1234/v1/chat/completions"

@app.get("/")
def read_root():
    return {"message": "Queue server is running!"}

@app.get("/queue/status")
def get_queue_status():
    """Check how many items are in the queue"""
    return {
        "queue_size": request_queue.qsize(),
        "total_processed": queue_stats["total_processed"],
        "current_request": queue_stats["current_request"]
    }

@app.post("/queue/add")

def add_to_queue(prompt: str, model: str, user: str):
    """Add a request to the queue"""
    request_id = f"{user}_{datetime.now().timestamp()}"

    request_data = {
        "id": request_id,
        "prompt": prompt,
        "model": model,
        "user": user,
        "timestamp": datetime.now().isoformat()
    }

    request_queue.put(request_data)

    results[request_id] = {
        "status": "queued",
        "response": None
    }

    return {
        "status": "queued",
        "request_id": request_id,
        "queue_position": request_queue.qsize()
    }

@app.get("/result/{request_id}")
def get_result(request_id: str):
    """Check if a request has been processed"""
    if request_id not in results:
        return {"error": "Request ID not found"}
    
    return results[request_id]

@app.get("/stream/{request_id}")
async def stream_result(request_id: str):
    async def event_stream():
        while queue_stats["current_request"] != request_id:
            await asyncio.sleep(0.5)

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                LM_STUDIO_URL,
                json={...},
                timeout=None
            ) as response:
                async for chunk in response.aiter_lines():
                    yield f"data: {chunk}\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.get("/hello/{name}")
def say_hello(name: str):
    return {"message": f"Hello, {name}!"}