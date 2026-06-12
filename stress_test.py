import asyncio
import httpx
import time
from typing import List

URL = "http://localhost:8000/api/command"
TOKEN = "LEARNING_9cdb5d9d-278f-4c12-83f3-c6d9d7fc594d"
CONCURRENT_REQUESTS = 50
TOTAL_REQUESTS = 500

async def send_request(client: httpx.AsyncClient, request_id: int):
    payload = {"command": "stock.get_all", "params": {}}
    headers = {"Authorization": TOKEN}
    try:
        start = time.time()
        response = await client.post(URL, json=payload, headers=headers)
        return response.status_code, time.time() - start
    except Exception as e:
        return str(type(e)), 0

async def main():
    print(f"🚀 Starting Stress Test: {CONCURRENT_REQUESTS} conc, {TOTAL_REQUESTS} total.")
    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = [send_request(client, i) for i in range(TOTAL_REQUESTS)]
        results = []
        for i in range(0, TOTAL_REQUESTS, CONCURRENT_REQUESTS):
            chunk = tasks[i:i+CONCURRENT_REQUESTS]
            results.extend(await asyncio.gather(*chunk))
            print(f"Processed {len(results)} requests...")

    successes = [r for r in results if r[0] == 200]
    failures = [r for r in results if r[0] != 200]
    durations = [r[1] for r in results if r[1] > 0]
    print(f"Results -> Success: {len(successes)}, Failures: {len(failures)}")
    if durations:
        print(f"Avg Time: {sum(durations)/len(durations):.4f}s")

if __name__ == "__main__":
    asyncio.run(main())
