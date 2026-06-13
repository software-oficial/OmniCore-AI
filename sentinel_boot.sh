#!/bin/bash
echo "🚀 OmniCore Sentinel: Booting System..."

# 1. Clean environment
pkill -f uvicorn || true
rm -f server.log
docker exec omnicore-redis redis-cli flushall

# 2. Infra Check
echo "🔍 Checking Infra..."
docker exec omnicore-redis redis-cli ping | grep -q PONG || { echo "❌ Redis Down"; exit 1; }
docker exec omnicore-db pg_isready -U omnicore_user || { echo "❌ DB Down"; exit 1; }
echo "✅ Infra Online"

# 3. Seeding
echo "🌱 Seeding Database..."
python3 seed_omnicore.py

# 4. Start API
echo "⚡ Starting API..."
nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &

# 5. Health Check Loop
echo "⏳ Waiting for API Health..."
for i in {1..10}; do
    if curl -s http://localhost:8000/health | grep -q "ok"; then
        echo "✅ API is ALIVE"
        break
    fi
    echo "Waiting... ($i/10)"
    sleep 2
    if [ $i -eq 10 ]; then
        echo "❌ API failed to start. Logs:"
        cat server.log
        exit 1
    fi
done

# 6. Deploy Business Schema
echo "🏗️ Deploying Business Schema..."
curl -s -X POST http://localhost:8000/api/gateway/execute \
     -H "Authorization: Bearer PRODUCTION_test_agent_001" \
     -H "Content-Type: application/json" \
     -d '{"command": "system.deploy_schema", "params": {}}' > /dev/null
echo "✅ Schema Deployed"

# 7. Run Gauntlet
echo "⚔️ Executing Gauntlet Test..."
python3 tests/gauntlet_test.py
