"""
Test that demonstrates actual queue buildup
===========================================

This submits multiple requests INSTANTLY (no stagger) to show
the queue positions incrementing.
"""

import requests
import json
import time
import threading

BASE_URL = "http://localhost:8000"


def test_rapid_submission():
    """
    Submit 5 requests as fast as possible to see queue buildup.
    """
    print("="*70)
    print("Rapid Submission Test - Watch Queue Positions!")
    print("="*70)
    print("\nSubmitting 5 requests instantly...\n")

    # Submit all 5 requests as fast as possible (NO delays)
    request_ids = []
    for i in range(1, 6):
        request_data = {
            "client_id": f"rapid_client_{i}",
            "messages": [
                {"role": "user", "content": f"Write exactly {i * 20} words about space."}
            ],
            "model": "mistralai/mistral-7b-instruct-v0.3",
            "temperature": 0.7,
            "max_tokens": 200
        }

        start = time.time()
        response = requests.post(f"{BASE_URL}/queue/add", json=request_data)
        submit_time = time.time() - start

        if response.status_code == 200:
            data = response.json()
            request_ids.append(data["request_id"])

            print(f"[Client {i}] Submitted in {submit_time*1000:.0f}ms - POSITION: {data['queue_position']} ← ✓")
        else:
            print(f"[Client {i}] Failed!")

    print(f"\n✓ All 5 requests submitted!")
    print(f"  You should see positions 1, 2, 3, 4, 5")
    print(f"  This shows the queue building up before the worker can process them all\n")

    # Now check queue status
    print("Checking queue status right after submission...")
    response = requests.get(f"{BASE_URL}/queue/status")
    if response.status_code == 200:
        data = response.json()
        print(f"  Queue size: {data['queue_size']}")
        print(f"  Total received: {data['stats']['total_received']}")
        print(f"  Currently processing: {data['stats']['current_request_id']}\n")

    # Watch them process
    print("Watching them process (first chunk times)...\n")

    def watch_request(client_num, request_id):
        """Watch when a specific request gets its first chunk"""
        start = time.time()
        stream_response = requests.get(f"{BASE_URL}/stream/{request_id}", stream=True)

        for line in stream_response.iter_lines():
            if not line:
                continue

            line_text = line.decode('utf-8')
            if line_text.startswith("data: "):
                chunk_data = json.loads(line_text[6:])

                if "position" in chunk_data:
                    elapsed = time.time() - start
                    print(f"[Client {client_num}] Waiting in queue... position {chunk_data['position']} ({elapsed:.1f}s)")

                elif "chunk" in chunk_data:
                    elapsed = time.time() - start
                    print(f"[Client {client_num}] ✓ First chunk received! ({elapsed:.2f}s from submission)")
                    return  # Exit after first chunk

                elif "done" in chunk_data:
                    return

    # Launch watchers for all 5 in parallel
    threads = []
    for i, request_id in enumerate(request_ids, 1):
        thread = threading.Thread(target=watch_request, args=(i, request_id))
        threads.append(thread)
        thread.start()

    # Wait for all to finish
    for thread in threads:
        thread.join()

    print("\n" + "="*70)
    print("✓ All requests processed!")
    print("="*70)


if __name__ == "__main__":
    print("\nMake sure:")
    print("1. Queue server is running")
    print("2. LM Studio is running with a model loaded")
    print("\n")
    input("Press Enter to start rapid submission test...")

    test_rapid_submission()
