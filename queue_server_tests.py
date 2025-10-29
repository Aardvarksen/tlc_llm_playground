"""
Queue Server Tests - Manual Testing Script
===========================================

This script tests the queue server endpoints we've built so far.
Run this AFTER starting the queue server with:
    uvicorn queue_server:app --reload --host 0.0.0.0 --port 8000

This is a "manual test script" (not pytest/unittest) because:
- Easier to understand what's happening
- Good for learning HTTP request/response patterns
- Shows you exactly what clients will do
- Can run step-by-step

Later, we can convert this to proper unit tests with pytest.
"""

import requests
import json
import time
import sys

# Configuration
BASE_URL = "http://localhost:8000"

# ANSI color codes for pretty output
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# ASCII-safe symbols (work on all platforms)
CHECK = "[OK]"
CROSS = "[FAIL]"
INFO = "[INFO]"


def print_test(name):
    """Print a test section header"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}TEST: {name}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")


def print_success(message):
    """Print a success message"""
    print(f"{GREEN}{CHECK} {message}{RESET}")


def print_error(message):
    """Print an error message"""
    print(f"{RED}{CROSS} {message}{RESET}")


def print_info(message):
    """Print an info message"""
    print(f"{YELLOW}{INFO} {message}{RESET}")


def print_response(response):
    """Pretty print a response"""
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Body:")
    print(json.dumps(response.json(), indent=2))


# ============================================================================
# TEST 1: Health Check Endpoints
# ============================================================================

def test_health_endpoints():
    """
    Test the basic health check endpoints.
    These should work even if the queue is empty.
    """
    print_test("Health Check Endpoints")

    # Test root endpoint
    print_info("Testing GET /")
    response = requests.get(f"{BASE_URL}/")

    if response.status_code == 200:
        print_success("Root endpoint is responding")
        print_response(response)
    else:
        print_error(f"Root endpoint failed with status {response.status_code}")
        return False

    # Test health endpoint
    print_info("\nTesting GET /health")
    response = requests.get(f"{BASE_URL}/health")

    if response.status_code == 200:
        print_success("Health endpoint is responding")
        print_response(response)

        data = response.json()
        # Verify expected fields are present
        if "queue_size" in data and "stats" in data:
            print_success("Health endpoint has expected fields")
        else:
            print_error("Health endpoint missing expected fields")
            return False
    else:
        print_error(f"Health endpoint failed with status {response.status_code}")
        return False

    return True


# ============================================================================
# TEST 2: Add Request to Queue
# ============================================================================

def test_add_request():
    """
    Test adding a request to the queue.

    This is what Streamlit apps will do:
    1. Build a request with messages, model, parameters
    2. POST to /queue/add
    3. Get back a request_id and queue_position
    """
    print_test("Add Request to Queue")

    # Build a sample request (what a Streamlit app would send)
    request_data = {
        "client_id": "test_script",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Tell me a joke about programming."}
        ],
        "model": "mistral-7b",
        "temperature": 0.8,
        "max_tokens": 100
    }

    print_info("Sending request:")
    print(json.dumps(request_data, indent=2))

    # Send POST request
    response = requests.post(
        f"{BASE_URL}/queue/add",
        json=request_data  # requests library automatically sets Content-Type: application/json
    )

    if response.status_code == 200:
        print_success("Request successfully added to queue")
        print_response(response)

        data = response.json()

        # Verify response has expected fields
        if "request_id" in data and "queue_position" in data and "status" in data:
            print_success("Response has all expected fields")

            # Return the request_id so we can use it in other tests
            request_id = data["request_id"]
            print_info(f"Received request_id: {request_id}")
            return request_id
        else:
            print_error("Response missing expected fields")
            return None
    else:
        print_error(f"Add request failed with status {response.status_code}")
        print_response(response)
        return None


# ============================================================================
# TEST 3: Check Queue Status
# ============================================================================

def test_queue_status():
    """
    Test the queue status endpoint.
    This shows overall queue health and statistics.
    """
    print_test("Queue Status")

    print_info("Testing GET /queue/status")
    response = requests.get(f"{BASE_URL}/queue/status")

    if response.status_code == 200:
        print_success("Queue status endpoint responding")
        print_response(response)

        data = response.json()
        print_info(f"Current queue size: {data.get('queue_size', 'unknown')}")
        print_info(f"Total requests received: {data.get('stats', {}).get('total_received', 'unknown')}")
        return True
    else:
        print_error(f"Queue status failed with status {response.status_code}")
        return False


# ============================================================================
# TEST 4: Check Individual Request Status
# ============================================================================

def test_request_status(request_id):
    """
    Test checking the status of a specific request.

    Args:
        request_id: The UUID returned from adding a request
    """
    print_test("Individual Request Status")

    if not request_id:
        print_error("No request_id provided, skipping test")
        return False

    print_info(f"Checking status of request: {request_id}")
    response = requests.get(f"{BASE_URL}/request/{request_id}")

    if response.status_code == 200:
        print_success("Request status retrieved")
        print_response(response)

        data = response.json()
        print_info(f"Status: {data.get('status', 'unknown')}")
        print_info(f"Client ID: {data.get('client_id', 'unknown')}")
        print_info(f"Created at: {data.get('created_at', 'unknown')}")
        return True
    else:
        print_error(f"Request status failed with status {response.status_code}")
        return False


# ============================================================================
# TEST 5: Invalid Request (Error Handling)
# ============================================================================

def test_invalid_request():
    """
    Test that the server properly rejects invalid requests.
    This tests Pydantic validation.
    """
    print_test("Invalid Request Handling")

    # Missing required field (no client_id)
    invalid_request = {
        "messages": [{"role": "user", "content": "Hello"}],
        "model": "mistral-7b"
        # Missing client_id!
    }

    print_info("Sending invalid request (missing client_id):")
    print(json.dumps(invalid_request, indent=2))

    response = requests.post(f"{BASE_URL}/queue/add", json=invalid_request)

    # We EXPECT this to fail with 422 (Unprocessable Entity)
    if response.status_code == 422:
        print_success("Server correctly rejected invalid request with 422")
        print_info("Validation error details:")
        print(json.dumps(response.json(), indent=2))
        return True
    else:
        print_error(f"Expected 422, got {response.status_code}")
        return False


# ============================================================================
# TEST 6: Multiple Requests (Queue Behavior)
# ============================================================================

def test_multiple_requests():
    """
    Test adding multiple requests to see queue behavior.
    This simulates multiple clients submitting requests.
    """
    print_test("Multiple Requests (Queue Behavior)")

    request_ids = []

    # Add 3 requests
    for i in range(3):
        request_data = {
            "client_id": f"client_{i+1}",
            "messages": [{"role": "user", "content": f"Request number {i+1}"}],
            "model": "mistral-7b"
        }

        print_info(f"\nAdding request {i+1}/3")
        response = requests.post(f"{BASE_URL}/queue/add", json=request_data)

        if response.status_code == 200:
            data = response.json()
            request_ids.append(data["request_id"])
            print_success(f"Request {i+1} added - position: {data['queue_position']}")
        else:
            print_error(f"Request {i+1} failed")
            return False

    # Check queue status
    print_info("\nChecking queue after adding 3 requests")
    response = requests.get(f"{BASE_URL}/queue/status")
    if response.status_code == 200:
        data = response.json()
        queue_size = data.get('queue_size', 0)
        print_info(f"Queue size: {queue_size}")

        if queue_size >= 3:  # At least our 3 requests
            print_success("All requests are in the queue")
        else:
            print_error(f"Expected at least 3 items in queue, found {queue_size}")
            return False

    return True


# ============================================================================
# TEST 7: Non-existent Request (Error Handling)
# ============================================================================

def test_nonexistent_request():
    """
    Test checking status of a request that doesn't exist.
    """
    print_test("Non-existent Request Handling")

    fake_id = "00000000-0000-0000-0000-000000000000"
    print_info(f"Checking status of fake request: {fake_id}")

    response = requests.get(f"{BASE_URL}/request/{fake_id}")

    if response.status_code == 200:
        data = response.json()
        if "error" in data:
            print_success("Server correctly returned error for non-existent request")
            print_info(f"Error message: {data['error']}")
            return True
        else:
            print_error("Server returned 200 but no error message")
            return False
    else:
        print_error(f"Unexpected status code: {response.status_code}")
        return False


# ============================================================================
# RUN ALL TESTS
# ============================================================================

def run_all_tests():
    """
    Run all tests in sequence.
    """
    print(f"\n{BLUE}{'='*70}")
    print("Queue Server Test Suite")
    print(f"{'='*70}{RESET}\n")

    print_info(f"Testing server at: {BASE_URL}")
    print_info("Make sure the queue server is running!")
    print_info("Start it with: uvicorn queue_server:app --reload --host 0.0.0.0 --port 8000\n")

    input("Press Enter to start tests...")

    results = {}

    # Run each test
    results["Health Endpoints"] = test_health_endpoints()

    time.sleep(0.5)  # Brief pause between tests
    request_id = test_add_request()
    results["Add Request"] = (request_id is not None)

    time.sleep(0.5)
    results["Queue Status"] = test_queue_status()

    time.sleep(0.5)
    results["Request Status"] = test_request_status(request_id)

    time.sleep(0.5)
    results["Invalid Request"] = test_invalid_request()

    time.sleep(0.5)
    results["Multiple Requests"] = test_multiple_requests()

    time.sleep(0.5)
    results["Non-existent Request"] = test_nonexistent_request()

    # Print summary
    print(f"\n{BLUE}{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}{RESET}\n")

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")

    print(f"\n{BLUE}Passed: {passed}/{total}{RESET}")

    if passed == total:
        print(f"\n{GREEN}{CHECK} All tests passed!{RESET}")
    else:
        print(f"\n{YELLOW}WARNING: Some tests failed{RESET}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print_error("\nCouldn't connect to the queue server!")
        print_info("Make sure it's running: uvicorn queue_server:app --reload --host 0.0.0.0 --port 8000")
    except KeyboardInterrupt:
        print_info("\nTests interrupted by user")
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
