import multiprocessing
import time

import pytest
import requests
import schemathesis
import uvicorn

from src.api.main import app

# Configuration for the real server
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"


def run_server():
    """Function to run the FastAPI app using uvicorn."""
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT, log_level="error")


@pytest.fixture(scope="session", autouse=True)
def api_server():
    """
    Fixture to start the API server in a separate process for high-fidelity fuzzing.
    Ensures the server is online before tests start and terminates it afterwards.
    """
    # Start the server in a separate process
    process = multiprocessing.Process(target=run_server, daemon=True)
    process.start()

    # Polling: Wait for the server to be ready
    timeout = 5
    start_time = time.time()
    while True:
        try:
            # Use a simple request to the health endpoint to verify the server is up
            response = requests.get(f"{BASE_URL}/health", timeout=1)
            if response.status_code == 200:
                break
        except requests.RequestException:
            pass

        if time.time() - start_time > timeout:
            process.terminate()
            pytest.fail(f"API Server failed to start at {BASE_URL} within {timeout}s")

        time.sleep(0.2)

    yield

    # Teardown: Stop the server process
    process.terminate()
    process.join()


# Load schema from the running server's OpenAPI endpoint
# This ensures Schemathesis uses its native transport against a real HTTP interface.
schema = schemathesis.openapi.from_url(f"{BASE_URL}/openapi.json")

# Valid token for the Fuzzing tests
TEST_TOKEN = "test_agent_001"


@schemathesis.pytest.parametrize(schema=schema)
def test_api_fuzzing(case):
    """
    Fuzzing test that executes a generated case against the REAL API.
    Any 500 Internal Server Error is considered a failure.
    """
    # Inject the Authorization header into every request
    case.headers = {"Authorization": f"Bearer {TEST_TOKEN}"}

    # Execute the request using Schemathesis's native requests-based transport.
    # We no longer pass a 'session' object to avoid TestClient incompatibilities.
    response = case.call()

    # The goal of the Guardian is to ensure NO 500 errors occur.
    # 4xx errors are acceptable (they mean validation is working).
    assert response.status_code < 500, (
        f"🚨 CRITICAL FAILURE: Command {case.operation.operation_id} "
        f"caused a 500 Internal Server Error!\n"
        f"Payload: {case.body}\n"
        f"Response: {response.text}"
    )
