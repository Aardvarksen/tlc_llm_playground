"""
Streaming Client Test - demonstrates end-to-end streaming flow
===============================================================

This script shows how a client (like Streamlit) would interact with the queue server
to get streaming LLM responses.

Flow:
1. Submit a request to /queue/add
2. Get request_id back
3. Open streaming connection to /stream/{request_id}
4. Read chunks as they arrive
5. Display them in real-time

Requirements:
- Queue server must be running (uvicorn queue_server:app --reload --host 0.0.0.0 --port 8000)
- LM Studio must be running with a model loaded
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"


def test_streaming():
    """
    Full end-to-end test of the streaming workflow.
    """
    print("="*70)
    print("Streaming LLM Request Test")
    print("="*70)

    # Step 1: Submit a request
    print("\n[1] Submitting request to queue...")

    request_data = {
        "client_id": "streaming_test_client",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Be concise."},
            {"role": "user", "content": "Write a haiku about programming."}
        ],
        "model": "mistralai/mistral-7b-instruct-v0.3",  # Use your loaded model
        "temperature": 0.8,
        "max_tokens": 100
    }

    response = requests.post(f"{BASE_URL}/queue/add", json=request_data)

    if response.status_code != 200:
        print(f"[ERROR] Failed to submit request: {response.status_code}")
        print(response.text)
        return

    data = response.json()
    request_id = data["request_id"]
    queue_position = data["queue_position"]

    print(f"[OK] Request submitted!")
    print(f"  Request ID: {request_id}")
    print(f"  Queue position: {queue_position}")

    # Step 2: Open streaming connection
    print(f"\n[2] Opening streaming connection...")
    print(f"  URL: {BASE_URL}/stream/{request_id}")
    print("\n" + "="*70)
    print("STREAMING RESPONSE:")
    print("="*70)

    import time
    start_time = time.time()
    chunk_count = 0

    try:
        # Open streaming connection
        stream_response = requests.get(
            f"{BASE_URL}/stream/{request_id}",
            stream=True,  # CRITICAL: enables streaming
            headers={"Accept": "text/event-stream"}
        )

        if stream_response.status_code != 200:
            print(f"[ERROR] Stream failed: {stream_response.status_code}")
            print(stream_response.text)
            return

        # Read chunks as they arrive
        full_text = ""
        first_chunk_time = None

        for line in stream_response.iter_lines():
            if not line:
                continue  # Skip empty lines

            # Decode the line
            line_text = line.decode('utf-8')

            # SSE format: "data: {json}"
            if line_text.startswith("data: "):
                json_str = line_text[6:]  # Remove "data: " prefix

                try:
                    chunk_data = json.loads(json_str)

                    if "position" in chunk_data:
                        # Queue position update
                        print(f"\r[Waiting in queue... position: {chunk_data['position']}]", end="", flush=True)

                    elif "chunk" in chunk_data:
                        # Actual content chunk!
                        if first_chunk_time is None:
                            first_chunk_time = time.time()
                            print(f"\n[First chunk received in {first_chunk_time - start_time:.2f}s]\n")

                        text = chunk_data["chunk"]
                        full_text += text
                        chunk_count += 1

                        # Show chunk with timing
                        elapsed = time.time() - start_time
                        print(f"[{elapsed:.2f}s] {text}", end="", flush=True)

                    elif "done" in chunk_data:
                        # Stream complete
                        print("\n")  # Final newline
                        break

                    elif "error" in chunk_data:
                        # Error occurred
                        print(f"\n[ERROR] {chunk_data['error']}")
                        return

                except json.JSONDecodeError as e:
                    print(f"\n[WARNING] Failed to parse JSON: {json_str}")

        end_time = time.time()
        total_time = end_time - start_time

        print("="*70)
        print(f"\n[3] Stream complete!")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Chunks received: {chunk_count}")
        print(f"  Total characters: {len(full_text)}")
        print(f"  Average chunk size: {len(full_text) / max(chunk_count, 1):.1f} chars")
        print(f"\n  Full text:\n  {full_text}")

    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Could not connect to queue server!")
        print("Make sure it's running: uvicorn queue_server:app --reload --host 0.0.0.0 --port 8000")

    except KeyboardInterrupt:
        print("\n\n[INFO] Interrupted by user")


def test_multiple_concurrent():
    """
    Test multiple concurrent streaming requests.
    Shows how the queue handles multiple clients.
    """
    import threading
    import time

    print("="*70)
    print("Multiple Concurrent Streaming Requests Test")
    print("="*70)

    def stream_request(client_num):
        """Submit and stream a request"""
        import time
        start = time.time()

        request_data = {
            "client_id": f"concurrent_client_{client_num}",
            "messages": [
                {"role": "user", "content": f"Write a {client_num}-sentence story about a robot."}
            ],
            "model": "mistralai/mistral-7b-instruct-v0.3",
            "temperature": 0.7,
            "max_tokens": 150
        }

        # Submit
        response = requests.post(f"{BASE_URL}/queue/add", json=request_data)
        if response.status_code != 200:
            print(f"[Client {client_num}] Failed to submit")
            return

        data = response.json()
        request_id = data["request_id"]
        queue_pos = data["queue_position"]
        submit_time = time.time() - start

        print(f"[Client {client_num}] Submitted (position {queue_pos}) - {submit_time:.2f}s")

        # Stream
        chunk_count = 0
        first_chunk = None
        stream_response = requests.get(f"{BASE_URL}/stream/{request_id}", stream=True)

        for line in stream_response.iter_lines():
            if not line:
                continue

            line_text = line.decode('utf-8')
            if line_text.startswith("data: "):
                chunk_data = json.loads(line_text[6:])

                if "position" in chunk_data:
                    elapsed = time.time() - start
                    print(f"[Client {client_num}] Waiting... position {chunk_data['position']} ({elapsed:.1f}s)")

                elif "chunk" in chunk_data:
                    chunk_count += 1
                    if first_chunk is None:
                        first_chunk = time.time() - start
                        print(f"[Client {client_num}] First chunk! ({first_chunk:.2f}s)")

                elif "done" in chunk_data:
                    total_time = time.time() - start
                    print(f"[Client {client_num}] Done! ({chunk_count} chunks, {total_time:.2f}s total)")
                    break

    # Launch 3 concurrent requests
    threads = []
    for i in range(1, 4):
        thread = threading.Thread(target=stream_request, args=(i,))
        threads.append(thread)
        thread.start()
        time.sleep(0.5)  # Stagger slightly

    # Wait for all to complete
    for thread in threads:
        thread.join()

    print("\n[OK] All concurrent requests completed!")


if __name__ == "__main__":
    print("\n")
    print("Streaming Client Test")
    print("Make sure:")
    print("1. Queue server is running (uvicorn queue_server:app --reload --host 0.0.0.0 --port 8000)")
    print("2. LM Studio is running with a model loaded")
    print("\n")

    choice = input("Choose test:\n  [1] Single streaming request\n  [2] Multiple concurrent requests\n  Choice: ")

    if choice == "1":
        test_streaming()
    elif choice == "2":
        test_multiple_concurrent()
    else:
        print("Invalid choice")
