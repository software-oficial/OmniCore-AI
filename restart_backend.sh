#!/bin/bash
echo "♻️ Sentinel is restarting the OmniCore-AI Backend..."
pkill -f "python3 api/main.py" || true
sleep 2
cd "/home/adrian/Escritorio/railway/OmniCore-AI"
export OMNICORE_INTERNAL_DB_URL=postgresql://omnicore_user:omnicore_password@localhost:5435/omnicore_registry
export REDIS_HOST=localhost
export REDIS_PORT=6380
# CORRECCIÓN: La variable de entorno debe ir ANTES del comando python3
nohup env PYTHONPATH=. python3 api/main.py > backend_sentinel.log 2>&1 &
echo "✅ Backend process triggered. Waiting for boot..."
sleep 5
curl -s http://localhost:8000/health | grep "ok" && echo "🚀 Backend is back online!" || echo "❌ Backend failed to boot."
