import requests
import time
import statistics

URL = "https://omnicore-ai-production.up.railway.app/api/gateway/execute"
TOKEN = "PRODUCTION_test_agent_001" # Token de prueba seedead
COMMAND = "stock.list"

def test_latency():
    latencies = []
    print(f"🚀 Starting Latency Test on {URL}...")
    print(f"Command: {COMMAND} | Token: {TOKEN}\n")
    
    for i in range(1, 11):
        start = time.perf_counter()
        try:
            res = requests.post(
                URL, 
                json={"command": COMMAND, "params": {}}, 
                headers={"Authorization": f"Bearer {TOKEN}"},
                timeout=10
            )
            end = time.perf_counter()
            
            if res.status_code == 200:
                data = res.json()
                # Usamos el latency_ms reportado por la API (tiempo interno)
                internal_ms = data.get('latency_ms', 0)
                # Calculamos el tiempo total (incluyendo red)
                total_ms = (end - start) * 1000
                latencies.append(total_ms)
                print(f"Req {i}: Total={total_ms:.2f}ms | Internal={internal_ms:.2f}ms | Status={data.get('success')}")
            else:
                print(f"Req {i}: ❌ HTTP {res.status_code}")
        except Exception as e:
            print(f"Req {i}: ❌ Error: {e}")

    if latencies:
        print(f"\n📊 RESULTS:")
        print(f"Average Latency: {statistics.mean(latencies):.2f}ms")
        print(f"Min Latency: {min(latencies):.2f}ms")
        print(f"Max Latency: {max(latencies):.2f}ms")
        print(f"P95 Latency: {statistics.quantiles(latencies, n=20)[18]:.2f}ms")
    else:
        print("\n❌ No successful requests.")

if __name__ == "__main__":
    test_latency()
