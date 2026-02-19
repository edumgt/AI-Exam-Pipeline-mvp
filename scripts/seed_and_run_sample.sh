#!/usr/bin/env bash
set -euo pipefail

API_BASE="http://localhost:8080/api"
DATA_PATH="/data/inbound/sample_timeseries.csv"

echo "[1] Create dataset..."
DATASET_ID=$(curl -s -X POST "${API_BASE}/datasets" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"sample\", \"source_path\":\"${DATA_PATH}\", \"meta\":{\"note\":\"generated\", \"type\":\"timeseries\"}}" \
  | python -c "import sys, json; print(json.load(sys.stdin)['id'])")

echo "  dataset_id=${DATASET_ID}"

echo "[2] Create run (enqueue pipeline)..."
RUN_ID=$(curl -s -X POST "${API_BASE}/runs" \
  -H "Content-Type: application/json" \
  -d "{\"dataset_id\":${DATASET_ID}, \"model_type\":\"baseline_sklearn\"}" \
  | python -c "import sys, json; print(json.load(sys.stdin)['id'])")

echo "  run_id=${RUN_ID}"
echo "[3] Tail logs:"
curl -s "${API_BASE}/runs/${RUN_ID}/logs?lines=200" | python -c "import sys, json; print(json.load(sys.stdin)['tail'])"
echo ""
echo "[OK] Open UI: http://localhost:8080"
