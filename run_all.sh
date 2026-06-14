#!/bin/bash
# Script maestro de arranque - OmniCore-AI

echo "--- 1. Limpiando procesos antiguos ---"
fuser -k 8000/tcp
fuser -k 5173/tcp

echo "--- 2. Levantando Backend ---"
export PYTHONPATH=$PYTHONPATH:.
uvicorn src.api.main:app --port 8000 &
BACKEND_PID=$!

echo "--- 3. Levantando Frontend ---"
cd web && npm install && npm run dev &
FRONTEND_PID=$!

echo "--- ¡SISTEMA ONLINE! ---"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
