#!/bin/bash
# Start all three services for the demo.
cd "$(dirname "$0")/.."
PY=.venv/bin/python

# load local secrets (gitignored) if present
if [ -f .env ]; then
  set -a; . ./.env; set +a
  echo "loaded .env (GEMINI_API_KEY ${GEMINI_API_KEY:+set}${GEMINI_API_KEY:-not set})"
fi

echo "starting govt api replica on :9000"
(cd govt-api && ../$PY -m uvicorn main:app --port 9000 &)

echo "starting backend on :8000"
(cd backend && ../$PY -m uvicorn app.main:app --port 8000 &)

if [ -d frontend/node_modules ]; then
  echo "starting frontend on :3000"
  (cd frontend && npm run dev &)
fi

sleep 2
echo ""
echo "govt api : http://127.0.0.1:9000/docs"
echo "backend  : http://127.0.0.1:8000/docs"
echo "frontend : http://127.0.0.1:3000"
wait
